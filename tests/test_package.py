import importlib.util, pathlib, tempfile, unittest, json
spec=importlib.util.spec_from_file_location('package',pathlib.Path(__file__).resolve().parents[1]/'scripts/package.py')
pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
class DeploymentTests(unittest.TestCase):
 def test_roundtrip_preserves_loader_and_unrelated_settings(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);pkg.ROOT=root;pkg.STAGE=root/'stage';game=root/'game';game.mkdir()
   pkg.ensure_stopped=lambda _:None
   for name,data in {'DisneyInfinity3.exe':b'fixture','Crabe/ReShade32.dll':b'CrabeReShadeManualAddonSupport','CrabeLoader.asi':b'loader','dinput8.dll':b'bootstrap'}.items():
    p=game/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data)
   config=game/'ReShade.ini';config.write_text('[GENERAL]\nEffectSearchPaths=old\nTextureSearchPaths=textures\nPresetPath=original.ini\n[OVERLAY]\nShowClock=0\n')
   mod=pkg.STAGE/pkg.MODREL;mod.mkdir(parents=True);(mod/'mod.json').write_text('{}')
   (pkg.STAGE/'package-hashes.json').write_text(json.dumps({'mods/di3-dlss5/mod.json':pkg.sha(mod/'mod.json')}))
   baseline=pkg.sha(game/'Crabe/ReShade32.dll');pkg.install(game)
   config.write_text(pkg.ini_set(config.read_text(),'OVERLAY','ShowClock','1'))
   pkg.uninstall(game)
   self.assertEqual(pkg.ini_get(config.read_text(),'GENERAL','PresetPath'),'original.ini')
   self.assertEqual(pkg.ini_get(config.read_text(),'GENERAL','EffectSearchPaths'),'old')
   self.assertEqual(pkg.ini_get(config.read_text(),'OVERLAY','ShowClock'),'1')
   self.assertEqual(pkg.sha(game/'Crabe/ReShade32.dll'),baseline)
   self.assertFalse((game/pkg.MODREL).exists())
if __name__=='__main__':unittest.main()
