"""Create the immutable versioned update contract for a GitHub release.
Does not upload or publish anything. The output URL is an intended deployment URL.
"""
import argparse,json,pathlib,re
p=argparse.ArgumentParser();p.add_argument('--owner',required=True);p.add_argument('--repo',default='car-launcher-data');p.add_argument('--tag',default='db-20261104');p.add_argument('--version',type=int,default=2026110401);p.add_argument('--out',default='server/manifest.json');a=p.parse_args()
for name in (a.owner,a.repo,a.tag):
 if not re.fullmatch(r'[A-Za-z0-9_.-]+',name):raise SystemExit('Invalid GitHub owner/repository/tag')
root=pathlib.Path(__file__).resolve().parents[1];d=json.loads((root/'data/bac-bo.json').read_text(encoding='utf-8'))
manifest={'format':1,'database_schema':2,'region':'bac-bo','version':a.version,'source_date':d['source_date'],'min_app_version':3,'database_url':f'https://github.com/{a.owner}/{a.repo}/releases/download/{a.tag}/{d["package_file"]}','package_size':d['package_bytes'],'package_sha256':d['package_sha256'],'database_size':d['bytes'],'database_sha256':d['sha256'],'attribution':'© OpenStreetMap contributors','license':'ODbL-1.0'}
out=pathlib.Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('Manifest created locally; deployment has not been performed: '+str(out))
