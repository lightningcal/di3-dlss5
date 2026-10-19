# DLSS 5 for Disney Infinity 3.0: Gold Edition

Experimental CrabeLoader package for Disney Infinity 3.0 Gold Edition (32-bit, D3D11).

**Status:** the fixed30FPS plateau was removed by setting NVIDIA Global Background Application Max Frame RateOff: user screenshot69FPS, live client~75-78FPS. Neural rendering was verified earlier, but the current faster helper session still needs fresh feature18/ENGAGED evidence before the full60FPS-with-neural target is confirmed. Helper-only backgroundOff and VSyncOff did not remove the plateau. See the [running troubleshooting log](docs/TROUBLESHOOTING.md) for every experiment, results, current settings, evidence and rollback details. Keep that log updated as testing continues.

## Required dependency: CrabeReShade plugin and companion ReShade DLL

**This mod runs ReShade through the CrabeReShade `.asi` plugin for CrabeLoader.** The plugin hosts ReShade on Disney Infinity 3.0's own D3D11 swap chain. Its companion ReShade build captures the game's **Direct3D 11 depth data** and starts add-ons such as this mod's Feed.

Before installing this mod, you need:
- CrabeLoader with plugin API v2 (`onPresent` / `onBeforeResize`). The reference is the CrabeLoader fork's `fix/reshade-hosting` branch, commit `a201cdb`.
- `plugins/CrabeReShade.asi`.
- The companion **32-bit `plugins/ReShade32.dll`**. The ordinary ReShade installer's DLL runs effects through the plugin but does not start add-ons, so it is not enough for this mod.

Still run the official ReShade installer for `ReShade.ini` and the shaders, then delete the `dxgi.dll` it leaves in the game folder. The DLSS mod installer **does not install the plugin or the companion DLL**. See [build and deployment instructions below](#prerequisite-crabereshade-plugin-and-companion-reshade) and the [machine setup guide](docs/SETUP.md).

## Start here

Read the [machine setup and configuration guide](docs/SETUP.md) for prerequisites, the global background-cap fix, installation, current-session neural verification, optional visual effects and complete preset backups.

## Before and after

The **after** image shows the combined look of **DLSS 5 plus Tonemap, CAS sharpening, FakeHDR and Vibrance**. The comparison includes those additional ReShade effects; it does not isolate the changes made by DLSS 5 alone. These are separate gameplay captures with small pose/HUD differences.

**Before**

![Before the combined DLSS 5 and ReShade look](docs/images/di3-before.png)

**After - DLSS 5 plus additional ReShade effects**

![After: DLSS 5 with Tonemap, CAS sharpening, FakeHDR and Vibrance](docs/images/di3-after-reshade.png)

See the [visual preset section of the setup guide](docs/SETUP.md#5-optional-reproduce-the-brighter-visual-look) for the effect order and brightness settings.

## Layout and responsibilities

```text
DI3 + CrabeLoader
  plugins/CrabeReShade.asi            ReShade host plugin; installer preserves it
  plugins/ReShade32.dll               companion ReShade DLL; installer preserves it
  ReShade.ini                         backed up, selected keys merged
  mods/di3-dlss5/
    mod.json + main.lua               CrabeLoader discovery/status entry
    DI3-DLSS5.ini                     separate preset; old preset preserved
    shaders/                         Lumenite Kernel + Feed + framework headers
    native/dlss5-feed.addon32          consumes the 32-bit scene
    native/host64/                    matching helper, ReShade x64, RenoDX, NGX
```

The Lua entry announces the package. ReShade performs rendering; Home > Add-ons > DLSS 5 Feed controls it. Disabling the Lua entry in CrabeMenu does not unload the native addon. Use the Feeder Enabled checkbox for on/off comparison, or uninstall and restart to remove the native integration. No extra game-root graphics proxy is installed.

## Prerequisite: CrabeReShade plugin and companion ReShade

The CrabeReShade plugin and its companion ReShade build provide three parts of the integration: hosting the ReShade runtime on the game's existing D3D11 swap chain, initializing ReShade add-ons, and forwarding native D3D11 draws, binds and depth clears so scene depth is available. They preserve the game's original D3D11 COM objects to retain the crash workaround. Stock ReShade's manual runtime does not start add-ons or see the game's draws by itself.

From a CrabeReShade checkout, with Git and VS2022 C++ Build Tools/Windows SDK installed:

```powershell
cmake -S . -B build -A Win32
cmake --build build --config Release
& .\companion\build.ps1
```

This builds `build\Release\CrabeReShade.asi`. It also pins official ReShade 6.8.0 commit `18deaa52de0c425a78b329e9cb3c497281cd00ec`, applies `companion\manual-addons.patch`, copies `companion\crabe_manual_depth.hpp`, and builds `build\companion\ReShade32.dll` (Release/Win32). Close DI and copy both into the game's `plugins\` folder. CrabeReShade's `README.md` covers the plugin and its `loader.log` messages.

The package installer checks that `plugins\CrabeReShade.asi` exists and that `plugins\ReShade32.dll` has the companion's capability export. It does not build or replace either. Keep any ReShade `dxgi.dll` or `d3d11.dll` out of the game folder.

## Assemble and install

Python 3.11+; no third-party Python modules. Run from this repository:

```powershell
python .\scripts\package.py prepare --nr .\nvngx_dlssnr_compat-fp16-310.9.16-cuda13.4.3\nvngx_dlssnr.dll
python .\scripts\package.py test
python .\scripts\package.py install --game 'PATH_TO_YOUR_GAME_FOLDER'
```

`prepare` downloads exact locked archives, checks SHA256, and assembles `local/stage`. With no `--nr`, it uses the separately tested public RTX40 310.8 runtime from the lock file. With `--nr`, it uses that local file and records its hash in the package. The currently deployed file is the user-supplied FP16 310.9.16 / CUDA13.4.3 build. Its origin beyond the supplied local folder has not been established; see `docs/user-runtime.json`.

Close the game and helper before install/uninstall. The installer refuses an existing package or external addons in the currently configured addon directory, rather than silently hiding them by changing ReShade's single addon search path. Built-in Generic Depth remains available. It backs up ReShade.ini under `local/backups`, retains your old preset and shaders, and selects the new separate preset. Install again only after uninstalling the previous copy.

## Test in DI

1. Launch DI normally and enter a 3D gameplay scene. Initial setup can take several seconds while the host starts and builds its GPU resources.
2. Press Home. Confirm `Lumenite_Kernel` runs before `DLSS5_Feed`. DisplayDepth should be disabled in this preset.
3. In Add-ons > Generic Depth, confirm the main scene depth buffer is selected. Previously verified DI settings are depth reversed=1, upside down=0, logarithmic=0, with depth copy before clears enabled; the installer preserves these settings.
4. In Add-ons > DLSS 5 Feed, confirm frames are being delivered. Toggle its Enabled checkbox and compare faces, geometry, UI and moving edges. No change plus an idle/failed neural state is not a successful test.
5. Inspect `mods/di3-dlss5/native/host64/ReShade.log`: require `feature 18 created`, `feature 18 evaluation succeeded` and `state=ENGAGED`. DLAA alone does not establish neural rendering.
6. Try movement, scene transitions and exit; then resize on a separate run. Record FPS/frametime with Enabled on/off at the same scene. 640x360 synthetic test timing is not a 1440p game benchmark.

Initial working resolution is 100%, SDR, one neural pass, Lumenite provider=3. Reduce Feeder working resolution in its panel if needed after establishing correct output. Estimated optical flow and the final frame include the game's HUD, so motion artifacts and UI changes need visual checking.

## Automated checks and evidence

```powershell
python -m unittest discover -s .\tests -p test_package.py
python .\scripts\package.py test
& .\scripts\test-integration.ps1 -CrabeReShadeRoot 'PATH_TO_CRABERESHADE_CHECKOUT' -ReShadeDll 'PATH_TO_COMPANION_ReShade32.dll'
python .\scripts\package.py verify --game 'PATH_TO_YOUR_GAME_FOLDER'
```

The integration test needs VS2022/CMake and the ReShade source that CrabeReShade's `companion\build.ps1` prepares under `build\reshade-src`. It creates a hidden x86 D3D11 scene and checks successful shader compilation, delivered frames, clean client shutdown and actual neural engagement. Tests copy native components into isolated evidence directories so they do not alter assembled configuration. Logs and result JSON live under ignored `local/evidence`.

`verify` checks installed static files against the locally assembled manifest. INI/CFG files may change through the overlay and are intentionally treated as mutable; missing files still fail.

## Remove

```powershell
python .\scripts\package.py uninstall --game 'PATH_TO_YOUR_GAME_FOLDER'
```

This restores the installer-managed ReShade keys while retaining unrelated overlay changes, and moves the mod into its backup directory so logs and tuning survive. It preserves the existing custom DLL and loader. Restart DI after removal.

## Packaging and sharing

`scripts/bundle.py` creates a source-only ZIP by default. `--local-binaries` creates a private, assembled ZIP with the staged mod and installer. Extract either into a separate working folder and follow these instructions; copying only the mod directory does not configure ReShade's addon search path or preset.

The local combined archive is for this test installation. Third-party runtime and shader redistribution terms differ; public distribution should use the source/installer package until those permissions are established. See `docs/THIRD-PARTY.md`, `sources.lock.json` and `docs/PROGRESS.md`.
