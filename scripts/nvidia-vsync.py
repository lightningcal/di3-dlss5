"""Read/apply per-app VSync-off with NVIDIA NVAPI. Global profile is never changed."""
import ctypes as c,struct,json,pathlib,datetime,argparse
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--uncap',action='store_true');args=p.parse_args()
P=c.c_void_p;U=c.c_uint32;dll=c.CDLL('nvapi64.dll');q=dll.nvapi_QueryInterface;q.argtypes=[U];q.restype=P
def fn(i,*a):return c.CFUNCTYPE(c.c_int,*a)(q(i))
def ok(rc):
 if rc:raise RuntimeError('NVAPI status '+str(rc))
def buf(size):
 b=c.create_string_buffer(size);struct.pack_into('<I',b,0,size|0x10000);return b
def string(b,off,s):
 raw=s.encode('utf-16-le')+b'\0\0';c.memmove(c.addressof(b)+off,raw,len(raw))
def get(profile,id):
 b=buf(12320);rc=fn(0x73bf8338,P,P,U,P)(session,profile,id,b)
 return {'status':rc,'value':struct.unpack_from('<I',b,8220)[0],'location':struct.unpack_from('<I',b,4108)[0]},b
ok(fn(0x0150e828)());session=P();ok(fn(0x0694d52e,c.POINTER(P))(c.byref(session)));ok(fn(0x375dbd6b,P)(session))
root=pathlib.Path(__file__).resolve().parents[1];backup=root/'local/driver-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S');backup.mkdir(parents=True)
try:
 base=P();ok(fn(0xda8466a0,P,c.POINTER(P))(session,c.byref(base)))
 print('Global VSync:',get(base,0xa879cf)[0]);records=[]
 if args.apply:ok(fn(0x2be25df8,P,c.c_wchar_p)(session,str(backup/'all-profiles-before.txt')))
 for app in ['DisneyInfinity3.exe','dlss5-feed-host64.exe']:
  h=P();a=buf(12296);rc=fn(0xeee566b2,P,c.c_wchar_p,c.POINTER(P),P)(session,app,c.byref(h),a)
  created=False
  if rc!=0:
   if rc!=-166:raise RuntimeError('Find application '+app+': '+str(rc))
   if not args.apply:print(app,'no application profile');continue
   profile=buf(4116);string(profile,4,'DI3 DLSS5 - '+app);ok(fn(0xcc176068,P,P,c.POINTER(P))(session,profile,c.byref(h)))
   a=buf(12296);string(a,8,app);ok(fn(0x4347a9de,P,P,P)(session,h,a));created=True
  info=buf(4116);ok(fn(0x61cd6fd6,P,P,P)(session,h,info));apps=struct.unpack_from('<I',info,4108)[0]
  profile_name=bytes(info)[4:4100].decode('utf-16-le').split('\0')[0]
  fps_before,_=get(h,0x10835002);print('Application FPS limiter:',fps_before);before,_=get(h,0xa879cf);rec={'app':app,'profile':profile_name,'profile_apps':apps,'created':created,'before':before,'fps_before':fps_before};records.append(rec);print(rec)
  if apps>1:raise RuntimeError('Shared profile; refusing to change multiple applications')
  if args.apply:
   setting=buf(12320);struct.pack_into('<II',setting,4100,0xa879cf,0);struct.pack_into('<I',setting,8220,0x08416747)
   ok(fn(0x577dd202,P,P,P)(session,h,setting));print('VSync override set off',get(h,0xa879cf)[0])
   if args.uncap:
    fps=buf(12320);struct.pack_into('<II',fps,4100,0x10835002,0);struct.pack_into('<I',fps,8220,0)
    ok(fn(0x577dd202,P,P,P)(session,h,fps));print('Application FPS limiter off:',get(h,0x10835002)[0])
 if args.apply:ok(fn(0xfcbc7e14,P)(session));print('Saved application overrides. Backup:',backup)
 (backup/'changes.json').write_text(json.dumps(records,indent=2)+'\n')
finally:fn(0xdad9cff8,P)(session)
