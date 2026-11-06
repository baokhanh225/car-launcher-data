"""Compress a validated SQLite package for Android's streaming importer."""
import pathlib,gzip,shutil,hashlib,json,sys
source=pathlib.Path(sys.argv[1]);dest=source.with_suffix(source.suffix+'.gz')
with source.open('rb') as a,gzip.open(dest,'wb',compresslevel=6) as b:shutil.copyfileobj(a,b,1024*1024)
metadata=source.with_suffix('.json');data=json.loads(metadata.read_text(encoding='utf-8'))
with dest.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
data.update(package_bytes=dest.stat().st_size,package_sha256=digest,package_file=dest.name);metadata.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'package_bytes':dest.stat().st_size,'sha256':digest}))
