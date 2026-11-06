"""Stream Geofabrik Vietnam PBF into the app's indexed offline road database.
Requires: python -m pip install osmium==4.3.2
The bounding box intentionally includes a southern buffer around Bac Bo.
"""
import argparse, collections, datetime, hashlib, json, math, pathlib, re, sqlite3
import osmium
HIGHWAYS=set('motorway trunk primary secondary tertiary unclassified residential living_street service motorway_link trunk_link primary_link secondary_link tertiary_link'.split())
BOX=(19.7,102.0,24.0,109.0)
def numeric(value):
    if not value:return 0
    m=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*(km/h|kph|mph)?\s*',value)
    if not m:return 0
    n=float(m[1])*(1.609344 if m[2]=='mph' else 1)
    return round(n) if 0<n<=200 else 0
def speeds(t):
    # Unknown conditions, lane-specific or vehicle-specific exceptions must never
    # be silently converted into a permanent all-car limit.
    uncertain=any(k.startswith('maxspeed') and (':conditional' in k or ':lanes' in k or ':motorcar' in k or ':motor_vehicle' in k) for k in t) or t.get('maxspeed:variable','no') not in ('no','')
    return (0,0) if uncertain else (numeric(t.get('maxspeed:forward',t.get('maxspeed',''))),numeric(t.get('maxspeed:backward',t.get('maxspeed',''))))
def geo(a,b):
    x=math.radians(b[1]-a[1])*math.cos(math.radians((a[0]+b[0])/2));y=math.radians(b[0]-a[0]);return math.hypot(x,y)*6371000,(math.degrees(math.atan2(x,y))+360)%360
def create(db):
    db.executescript('''PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF; PRAGMA user_version=2;
    CREATE TABLE meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
    CREATE TABLE ways(id INTEGER PRIMARY KEY,name TEXT,ref TEXT,highway TEXT,layer TEXT,bridge TEXT,tunnel TEXT,tags TEXT);
    CREATE TABLE segments(id INTEGER PRIMARY KEY,wayid INTEGER,n1 INTEGER,n2 INTEGER,lat1 REAL,lon1 REAL,lat2 REAL,lon2 REAL,length REAL,bearing REAL,speedf INTEGER,speedb INTEGER,dir INTEGER);
    CREATE TABLE cells(cell INTEGER,sid INTEGER,PRIMARY KEY(cell,sid)) WITHOUT ROWID;
    CREATE TABLE restrictions(id INTEGER PRIMARY KEY,fromway INTEGER,toway INTEGER,via INTEGER,kind TEXT,supported INTEGER,tags TEXT);
    CREATE INDEX segment_way ON segments(wayid); CREATE INDEX rule_from ON restrictions(fromway);
    ''')
class Builder(osmium.SimpleHandler):
    def __init__(self,db):
        super().__init__();self.db=db;self.sid=0;self.kept=set();self.stats=collections.Counter();self.batch=[];self.tiles=[]
    def flush(self):
        self.db.executemany('INSERT INTO segments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',self.batch);self.db.executemany('INSERT OR IGNORE INTO cells VALUES(?,?)',self.tiles);self.batch=[];self.tiles=[]
    def way(self,w):
        t=dict(w.tags)
        if t.get('highway') not in HIGHWAYS:return
        if t.get('area')=='yes' or t.get('motorcar',t.get('motor_vehicle',t.get('vehicle',t.get('access','yes')))) in ('no','private'):return
        try: pts=[(n.ref,n.lat,n.lon) for n in w.nodes]
        except osmium.InvalidLocationError:self.stats['invalid_geometry']+=1;return
        if len(pts)<2 or not any(BOX[0]<=p[1]<=BOX[2] and BOX[1]<=p[2]<=BOX[3] for p in pts):return
        sf,sb=speeds(t);one=t.get('oneway:motorcar',t.get('oneway:motor_vehicle',t.get('oneway:vehicle',t.get('oneway','yes' if t.get('junction')=='roundabout' or t.get('highway')=='motorway' else 'no'))));direction=-1 if one=='-1' else 1 if one in ('yes','1','true') else 0
        if any(k.startswith('oneway') and 'conditional' in k for k in t): self.stats['conditional_oneway_excluded']+=1;return
        self.kept.add(w.id);self.stats['ways']+=1;self.stats['ways_with_numeric_speed']+=bool(sf or sb)
        self.stats['conditional_speed_unknown']+=any('conditional' in k and k.startswith('maxspeed') for k in t)
        self.db.execute('INSERT INTO ways VALUES(?,?,?,?,?,?,?,?)',(w.id,t.get('name',''),t.get('ref',''),t.get('highway',''),t.get('layer','0'),t.get('bridge','no'),t.get('tunnel','no'),json.dumps(t,ensure_ascii=False,separators=(',',':'))))
        for a,b in zip(pts,pts[1:]):
            length,bearing=geo(a[1:],b[1:])
            if length<.1:continue
            self.sid+=1;self.batch.append((self.sid,w.id,a[0],b[0],a[1],a[2],b[1],b[2],length,bearing,sf,sb,direction))
            for y in range(math.floor(min(a[1],b[1])*200),math.floor(max(a[1],b[1])*200)+1):
                for x in range(math.floor(min(a[2],b[2])*200),math.floor(max(a[2],b[2])*200)+1):self.tiles.append((y*1000000+x,self.sid))
            if len(self.batch)>=10000:self.flush()
    def relation(self,r):
        t=dict(r.tags)
        if t.get('type')!='restriction':return
        fr=[m.ref for m in r.members if m.role=='from' and m.type=='w'];to=[m.ref for m in r.members if m.role=='to' and m.type=='w'];via=[m.ref for m in r.members if m.role=='via' and m.type=='n']
        if not fr or fr[0] not in self.kept:return
        kind=t.get('restriction:motorcar',t.get('restriction:motor_vehicle',t.get('restriction','')))
        supported=len(fr)==len(to)==len(via)==1 and to[0] in self.kept and not any('conditional' in k for k in t) and not any(v.strip() in ('motorcar','motor_vehicle','vehicle') for v in t.get('except','').split(';')) and kind in ('no_left_turn','no_right_turn','no_straight_on','no_u_turn','only_straight_on','only_left_turn','only_right_turn')
        if supported:
            self.flush()
            supported=all(self.db.execute('SELECT COUNT(*) FROM segments WHERE wayid=? AND (n1=? OR n2=?)',(w,via[0],via[0])).fetchone()[0]==1 for w in (fr[0],to[0]))
        self.db.execute('INSERT INTO restrictions VALUES(?,?,?,?,?,?,?)',(r.id,fr[0],to[0] if to else 0,via[0] if via else 0,kind,int(supported),json.dumps(t,ensure_ascii=False,separators=(',',':'))));self.stats['restrictions']+=1;self.stats['supported_restrictions']+=supported
def build(src,out):
    out=pathlib.Path(out);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.with_suffix('.building.sqlite')
    if tmp.exists():tmp.unlink()
    db=sqlite3.connect(tmp);create(db);builder=Builder(db);builder.apply_file(str(src),locations=True,idx='flex_mem');builder.flush()
    stamp=re.search(r'vietnam-(\d{6})\.osm\.pbf$',str(src));source_date=datetime.datetime.strptime(stamp[1],'%y%m%d').date().isoformat() if stamp else 'test-extract'
    source='https://download.geofabrik.de/asia/'+pathlib.Path(src).name if stamp else 'local test extract'
    meta={'schema':'2','region':'Bắc Bộ + vùng đệm phía Nam','bbox':json.dumps(BOX),'source':source,'source_date':source_date,'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors','built_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'segments':str(builder.sid),'stats':json.dumps(dict(builder.stats),ensure_ascii=False)}
    db.executemany('INSERT INTO meta VALUES(?,?)',meta.items());db.commit();db.execute('PRAGMA journal_mode=DELETE');assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close();tmp.replace(out)
    with out.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    manifest={**meta,'bytes':out.stat().st_size,'sha256':digest};out.with_suffix('.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(manifest,ensure_ascii=True))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('pbf');a.add_argument('out');p=a.parse_args();build(p.pbf,p.out)
