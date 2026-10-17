import argparse,pathlib,zipfile
r=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--local-binaries',action='store_true');args=p.parse_args()
out=r/'dist'/('di3-dlss5-0.1.0-'+('local' if args.local_binaries else 'source')+'.zip');out.parent.mkdir(exist_ok=True)
files=[r/'README.md',r/'sources.lock.json',r/'.gitignore']
for d in ['docs','scripts','mod','tests','patches']:
 files += [f for f in (r/d).rglob('*') if f.is_file() and '__pycache__' not in f.parts]
if args.local_binaries:
 files += [f for f in (r/'local/stage').rglob('*') if f.is_file()]
 if not (r/'local/stage/package-hashes.json').exists():raise RuntimeError('Run prepare first')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(f,f.relative_to(r).as_posix())
print(out)
