"""Pinned local assembly and reversible installation. Python 3.11+, standard library only."""
import argparse, hashlib, io, json, pathlib, shutil, subprocess, urllib.request, zipfile, re, datetime
ROOT = pathlib.Path(__file__).resolve().parents[1]
STAGE = ROOT / 'local/stage'
MODREL = pathlib.Path('mods/di3-dlss5')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ini_get(text, section, key, default=''):
    active = False
    for line in text.splitlines():
        if line.startswith('['): active = line.strip() == '['+section+']'
        elif active and line.partition('=')[0].strip() == key: return line.partition('=')[2].strip()
    return default
def ini_set(text, section, key, value):
    lines=text.splitlines(); start=next((i for i,x in enumerate(lines) if x.strip()=='['+section+']'),None)
    if start is None: return text.rstrip()+'\n\n['+section+']\n'+key+'='+value+'\n'
    end=next((i for i in range(start+1,len(lines)) if lines[i].startswith('[')),len(lines))
    found=next((i for i in range(start+1,end) if lines[i].partition('=')[0].strip()==key),None)
    if found is None: lines.insert(end,key+'='+value)
    else: lines[found]=key+'='+value
    return '\n'.join(lines)+'\n'
def put(source, dest):
    dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,dest)
def prepare(nr=None):
    archives={}
    for item in json.loads((ROOT/'sources.lock.json').read_text(encoding='utf-8-sig')):
        cache=ROOT/'.cache'/ (item['name']+('.exe' if item['name']=='reshade' else '.zip'))
        cache.parent.mkdir(exist_ok=True)
        if not cache.exists():
            with urllib.request.urlopen(urllib.request.Request(item['url'],headers={"User-Agent":"di3-dlss5/0.1"})) as r, cache.open('wb') as f: shutil.copyfileobj(r,f)
        if sha(cache)!=item['sha']: raise RuntimeError('Hash mismatch: '+str(cache))
        data=cache.read_bytes()
        if item['name']=='reshade':
            offset=next((i for i in range(0,len(data)-30,512) if data[i:i+4]==b'PK\x03\x04'),None)
            if offset is None: raise RuntimeError('No embedded ReShade ZIP')
            data=data[offset:]
        archives[item['name']]=zipfile.ZipFile(io.BytesIO(data))
    mod=STAGE/MODREL
    if mod.exists():
        if mod.resolve() != (ROOT/'local/stage/mods/di3-dlss5').resolve(): raise RuntimeError('Unexpected staging path')
        shutil.rmtree(mod)
    native=mod/'native'; host=native/'host64'; shader=mod/'shaders/Shaders'; texture=mod/'shaders/Textures'
    for d in [native,host,shader,texture,mod/'licenses']: d.mkdir(parents=True,exist_ok=True)
    def extract(archive, suffix, dest):
        z=archives[archive]; entries=[n for n in z.namelist() if n.replace('\\','/').endswith(suffix)]
        if len(entries)!=1: raise RuntimeError('Ambiguous/missing archive entry: '+suffix)
        dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(entries[0]))
    extract('feeder','dlss5-feed.addon32',native/'dlss5-feed.addon32')
    extract('feeder','host64/dlss5-feed-host64.exe',host/'dlss5-feed-host64.exe')
    extract('feeder','DLSS5_Feed.fx',shader/'DLSS5_Feed.fx')
    extract('nr','nvngx_dlssnr.dll',host/'nvngx_dlssnr.dll')
    if nr:
        put(nr,host/'nvngx_dlssnr.dll')
        (mod/'runtime-provenance.json').write_text(json.dumps({'source':'user supplied','filename':nr.name,'sha256':sha(nr)},indent=2)+'\n')
    extract('dlss-310.9.16','nvngx_dlss.dll',host/'nvngx_dlss.dll')
    extract('renodx-dlss5-8.5.0-rc10','renodx-dlss5.addon64',host/'renodx-dlss5.addon64')
    extract('reshade','ReShade64.dll',host/'dxgi.dll')
    for name in ['lumenite','framework']:
        z=archives[name]
        for entry in z.namelist():
            p=pathlib.PurePosixPath(entry)
            if entry.endswith('/'): continue
            if '..' in p.parts: raise RuntimeError('Unsafe ZIP path')
            if 'Shaders' in p.parts:
                parts=p.parts[p.parts.index('Shaders')+1:]
                if parts and ((name=='framework' and p.suffix=='.fxh') or (name=='lumenite' and parts[0]=='include') or parts[0]=='lumenite_Kernel.fx'):
                    dest=shader.joinpath(*parts); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(entry))
            elif 'Textures' in p.parts:
                dest=texture.joinpath(*p.parts[p.parts.index('Textures')+1:]); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(entry))
            elif p.name.lower().startswith(('license','notice')):
                (mod/'licenses'/(name+'-'+p.name)).write_bytes(z.read(entry))
    for n in ['main.lua','mod.json','DI3-DLSS5.ini']: put(ROOT/'mod'/n,mod/n)
    put(ROOT/'mod/host-ReShade.ini',host/'ReShade.ini'); put(ROOT/'mod/dlss5-feed.cfg',native/'dlss5-feed.cfg')
    put(ROOT/'sources.lock.json',mod/'sources.lock.json'); put(ROOT/'docs/THIRD-PARTY.md',mod/'licenses/THIRD-PARTY.md')
    put(ROOT/'docs/SETUP.md',mod/'SETUP.md')
    for image in (ROOT/'docs/images').rglob('*'):
        if image.is_file(): put(image,mod/'images'/image.relative_to(ROOT/'docs/images'))
    for f in (ROOT/'docs/licenses').iterdir(): put(f,mod/'licenses'/f.name)
    manifest={str(f.relative_to(STAGE)).replace('\\','/'):sha(f) for f in mod.rglob('*') if f.is_file() and f.suffix.lower() not in ['.log'] and f.name!='package-hashes.json'}
    (STAGE/'package-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Prepared',STAGE)
def ensure_stopped(game):
    # Do not modify files while DI or its 64-bit companion owns them.
    out=subprocess.run(['powershell','-NoProfile','-Command',"Get-Process | Where-Object { $_.ProcessName -like '*DisneyInfinity*' -or $_.ProcessName -eq 'dlss5-feed-host64' } | Select-Object -ExpandProperty Id"],capture_output=True,text=True,check=True).stdout.strip()
    if out: raise RuntimeError('Close DI and the Feeder host first. PIDs: '+out)
def verify_tree(base):
    manifest=json.loads((STAGE/'package-hashes.json').read_text())
    for rel,digest in manifest.items():
        p=base/rel
        if not p.is_file(): raise RuntimeError('Missing package file: '+str(p))
        mutable=p.suffix.lower() in ['.ini','.cfg']
        if sha(p)!=digest and not mutable: raise RuntimeError('Changed package file: '+str(p))
    print('Package hashes verified:',len(manifest))
def install(game):
    ensure_stopped(game); verify_tree(STAGE)
    if not (game/'DisneyInfinity3.exe').exists(): raise RuntimeError('Expected DisneyInfinity3.exe in game folder')
    if not (game/'plugins/CrabeReShade.asi').is_file(): raise RuntimeError('CrabeReShade plugin prerequisite missing: plugins/CrabeReShade.asi')
    dll=game/'plugins/ReShade32.dll'
    if not dll.is_file(): raise RuntimeError('Companion ReShade prerequisite missing: plugins/ReShade32.dll')
    # PE export name is present in the patched manual-depth build; version is checked in loader logs.
    if b'CrabeReShadeManualAddonSupport' not in dll.read_bytes(): raise RuntimeError('Custom manual addon bridge missing')
    target=game/MODREL
    if target.exists(): raise RuntimeError('Package already installed; uninstall first')
    config=game/'ReShade.ini'; original=config.read_text(encoding='utf-8-sig'); updated=original
    oldpath=ini_get(original,'ADDON','AddonPath','.')
    existing=game/oldpath
    if any(existing.glob('*.addon*')): raise RuntimeError('Existing external addons in search path; consolidate them manually before installing')
    updated=ini_set(updated,'ADDON','AddonPath',r'.\mods\di3-dlss5\native')
    for key,path in [('EffectSearchPaths',r'.\mods\di3-dlss5\shaders\Shaders\**'),('TextureSearchPaths',r'.\mods\di3-dlss5\shaders\Textures\**')]:
        old=ini_get(original,'GENERAL',key); updated=ini_set(updated,'GENERAL',key,old+(',' if old else '')+path)
    updated=ini_set(updated,'GENERAL','PresetPath',r'.\mods\di3-dlss5\DI3-DLSS5.ini')
    # Prevent startup-preset override from selecting the old diagnostic preset.
    updated=ini_set(updated,'GENERAL','StartupPresetPath','')
    backup=ROOT/'local/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'); backup.mkdir(parents=True)
    put(config,backup/'ReShade.ini'); baseline={str(p.relative_to(game)):sha(p) for p in [dll,game/'CrabeLoader.asi',game/'dinput8.dll']}
    state={'game':str(game),'backup':str(backup),'baseline':baseline,'previous_keys':{s:{k:ini_get(original,s,k,None) for k in keys} for s,keys in {'ADDON':['AddonPath'],'GENERAL':['EffectSearchPaths','TextureSearchPaths','PresetPath','StartupPresetPath']}.items()}}
    (backup/'state.json').write_text(json.dumps(state,indent=2)+'\n')
    try:
        shutil.copytree(STAGE/MODREL,target)
        config.write_text(updated,encoding='utf-8')
        state['installed_config_sha']=sha(config)
        (target/'install-state.json').write_text(json.dumps(state,indent=2)+'\n')
        verify_tree(game)
        for rel,h in baseline.items():
            if sha(game/rel)!=h: raise RuntimeError('Prerequisite changed: '+rel)
    except Exception:
        put(backup/'ReShade.ini',config)
        if target.exists(): shutil.move(str(target),str(backup/'failed-mod'))
        raise
    print('Installed; backup:',backup)
def uninstall(game):
    ensure_stopped(game); target=game/MODREL
    state=json.loads((target/'install-state.json').read_text())
    if pathlib.Path(state['game']).resolve()!=game: raise RuntimeError('Install path differs from recorded path')
    config=game/'ReShade.ini'
    # Restore only keys changed by this installer; preserve unrelated overlay changes.
    text=config.read_text(encoding='utf-8-sig')
    for section, keys in state['previous_keys'].items():
        for key,value in keys.items():
            if value is None:
                # Empty AddonPath returns discovery to the base directory, equivalent to absent.
                value=''
            text=ini_set(text,section,key,value)
    config.write_text(text,encoding='utf-8')
    # Move instead of deleting: retain logs and user tuning for diagnosis.
    saved=pathlib.Path(state['backup'])/'removed-mod'
    if saved.exists(): raise RuntimeError('Backup target already exists')
    shutil.move(str(target),str(saved)); print('Removed package; retained files at',saved)
def test():
    logs=ROOT/'local/evidence'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S'); logs.mkdir(parents=True)
    host=logs/'host64'; shutil.copytree(STAGE/MODREL/'native/host64',host)
    with (logs/'console.txt').open('w') as f: r=subprocess.run([str(host/'dlss5-feed-host64.exe'),'--test'],cwd=host,stdout=f,stderr=subprocess.STDOUT)
    for name in ['ReShade.log','dlss5-feed-host.log']:
        if (host/name).exists(): put(host/name,logs/name)
    hl=(logs/'dlss5-feed-host.log').read_text(errors='replace'); rl=(logs/'ReShade.log').read_text(errors='replace')
    ok=r.returncode==0 and '300/300 evaluates succeeded' in hl and 'feature 18 created' in rl and 'feature 18 evaluation succeeded' in rl
    summary={'passed':ok,'exit_code':r.returncode,'checks':['300/300 evaluates','feature 18 created','feature 18 evaluation succeeded'],'runtime_sha256':sha(host/'nvngx_dlssnr.dll')}
    (logs/'result.json').write_text(json.dumps(summary,indent=2)+'\n'); print(summary,'Evidence:',logs)
    if not ok: raise RuntimeError('Neural test failed; inspect evidence')
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','install','uninstall','verify','test']); parser.add_argument('--game',type=pathlib.Path)
    parser.add_argument('--nr',type=pathlib.Path)
    args=parser.parse_args()
    if args.action in ['install','uninstall','verify']:
        if not args.game: parser.error('--game required')
        game=args.game.resolve()
        {'install':install,'uninstall':uninstall,'verify':verify_tree}[args.action](game)
    elif args.action=='prepare': prepare(args.nr)
    else: test()
