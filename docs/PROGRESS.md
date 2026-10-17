# Progress and handoff

> Historical notes. The canonical current state and complete test matrix are now in [TROUBLESHOOTING.md](TROUBLESHOOTING.md). Earlier NEXT instructions and hypotheses below may be superseded.

## Existing prerequisite
- CrabeLoader fork: <CrabeLoader checkout>, fix/reshade-hosting commit 0977b9c.
- Custom ReShade 6.8.0 source, lifecycle and native D3D11 depth patches documented in that fork under docs/guides/reshade.md and tools/reshade.
- User confirmed Generic Depth detects buffers and DisplayDepth shows real geometry in-game.
- Game: <game>.
- RTX 4070, driver 616.56. Existing game mods and ReShade presets must be backed up and preserved.

## Packaging decisions
- New independent local Git repository <repo>.
- Feeder v1.19.0, source commit 3c09eabcd138a68d144b6cc396a23e6b493eea4d; matched addon32/host64 required (IPC v11).
- Keep addon and its host64 directory together, because Feeder resolves host64 relative to its addon file.
- Lumenite Kernel before DLSS5_Feed, DLSS5_MV_PROVIDER=3.
- A Crabe Lua mod alone cannot load NGX into a 32-bit process; package the native companion and isolated 64-bit host alongside it.
- Disabling a Lua mod alone cannot unload an already-loaded native ReShade addon. Install/uninstall must account for this.
- Stock 310.8 and Lecram neural runtimes do not support RTX 4070. Obtain the community Ada build, then test feature 18 creation and evaluation explicitly. DLAA success alone is insufficient.

## Current status
Installed for gameplay testing. Standalone and complete synthetic manual-runtime neural tests passed on RTX4070. The user-supplied compatibility runtime is deployed. Game visual/performance validation remains pending; see dated results below.

## Acceptance criteria
1. Pinned downloads recorded with hashes and source URLs.
2. Helper test runs on RTX 4070 and logs successful neural feature creation/evaluation.
3. Feeder + motion shader compile and run through the existing manual ReShade runtime.
4. Game survives launch, scene changes, resize and exit; compare neural on/off, observe valid depth/MV and output with no HUD corruption.
5. Reversible install, verified preservation of existing loader and settings, distributable layout with third-party notices.

Only criteria actually observed should be marked verified. Do not infer a working game integration from the helper test.

## 2026-10-17 results
- Downloaded public RTX40 310.8 archive from RankFTW/rhi-repo and matched the release SHA256. RTX4070 / 616.56: standalone helper test 300/300, feature18 created and evaluated. Evidence: local/evidence/20261017-005850-public-rtx40.
- User subsequently supplied nvngx_dlssnr_compat-fp16-310.9.16-cuda13.4.3/nvngx_dlssnr.dll. SHA256 cdfa6c1ec784867182164c7836f324f087b5c9f374d0c9fe46f54999feabf3ed. Upstream URL not supplied. Standalone helper test also passed 300/300 with feature18 creation/evaluation. Evidence: local/evidence/20261017-010058.
- Selected the user-supplied runtime for local deployment; the public RTX40 runtime remains the reproducible no-argument fallback in the builder. Both were tested independently, not assumed equivalent.
- Complete manual-runtime synthetic test: native x86 D3D11 640x360, 600 frames. Kernel and Feed compiled, Generic Depth supplied the real 640x360 resource, host connected IPC11, shared output delivered, RenoDX feature18 evaluation succeeded and verdict ENGAGED, client clean shutdown. Evidence: local/evidence/20261017-010206-manual-integration. First harness released its depth resource before destroying the runtime and logged a lifetime warning; adjusted harness teardown to keep it alive through destruction and added a repeatable integration script.
- Disposable deployment roundtrip passed, including original loader hashes, old preset/search path restoration, and preservation of a simulated unrelated overlay setting.
- Deployed to the actual game at 01:03 local time. ReShade.ini backup: <repo>/local/backups/20261017-010303/ReShade.ini. No loader/DLL replacement. Baseline custom ReShade DLL SHA256 f3275bfaa20707acd5708115e61f59b6f34c09868841c3923132c3a29b3dd428.
- Repeated full integration test passed with corrected resource lifetime; evidence local/evidence/20261017-010357-integration.
- Actual gameplay neural output, HUD quality, motion, transitions, resize and performance are PENDING user test. Previous in-game confirmation covered depth only, before this Feeder package.
- No push or commit performed for this new project. Existing Crabe fork commit remains separate.

## Resume checklist
1. Read README, this file, sources.lock.json and docs/user-runtime.json; inspect current game logs before guessing causes.
2. Package-owned files live at game/mods/di3-dlss5; game/ReShade.ini selects its preset and native addon folder. Native output logs are under native/ and native/host64/.
3. Require neural engagement in the CURRENT GAME session's host log; synthetic evidence does not prove gameplay quality.
4. If debugging requires reinstall, close DI/host and run uninstall; logs are retained in local/backups. Preserve user changes and the working custom ReShade32.dll.
5. Builder defaults to the older public Ada runtime; pass --nr explicitly to reproduce this deployment. Do not silently switch runtime versions.

## Performance diagnosis - 2026-10-17

Actual DI gameplay established successful neural rendering at 2560x1440, but a fixed 30 FPS plateau. Original work resolution=100, pipelined handoff=1, RTSS DI cap=60, Crabe frameLimit=0. Client CPU feeding approximately 0.25 ms/frame; neural GPU approximately 7 ms/frame. Full NGX path approximately 8.9 ms/frame (do not add overlapping telemetry timings as if independent).

Live work-size tests: 67% (1714x964) triggered repeated NGX shared-build failures; do not use this size as a proven profile. 75% (1920x1080) resumed neural output after helper recovery but still measured 30 FPS. 50% (1280x720) successfully created/evaluated neural output at approximately 2.8 ms neural GPU cost, but still measured 30 FPS. Resolution alone did not fix the plateau. Brief 60 FPS during failed builds was fallback rendering without active NGX and is NOT a successful neural-performance result.

A helper Stop-Process used during recovery subsequently latched Feeder stopped in the current game session. A full game restart is needed for clean recovery and driver changes. No game process was terminated; no code/DLL changes were made.

Root pacing evidence: read NVIDIA's global profile via official NVAPI and found VSYNCMODE_FORCEON (0x47814940), inherited by DI's existing profile 'disney infinity'. This overrides application's no-VSync requests. The existing profile contains one application. Applied VSYNCMODE_FORCEOFF (0x08416747) specifically to DisneyInfinity3.exe and to a newly created single-app profile 'DI3 DLSS5 - dlss5-feed-host64.exe'. Global profile unchanged. Backup and per-app previous values: local/driver-backups/20261017-013129. Script: scripts/nvidia-vsync.py (explicit --apply; NOT run by installer).

Current installed Feeder config: work_resolution=50, work_upscale=1, async_home=1. This trades processing resolution for speed and uses FSR1 to expand to the unchanged 2560x1440 game backbuffer. Original config and log evidence: local/evidence/performance-20261017. The source/staged package defaults remain 100% pending confirmation of the preferred gameplay preset.

NEXT: user closes and restarts DI so per-app driver override applies and Feeder starts cleanly; measure active neural output FPS again, with ReShade overlay closed. Verify host log ENGAGED and measure frame intervals. 60 FPS with neural output is NOT yet verified. If stable, try 75% for higher quality; avoid live retry loops and restart the host using its own overlay button if a rebuild fails.

Driver overrides are independent of the mod files: package uninstall does not remove them. To undo, select each app's profile in NVIDIA Control Panel and return Vertical sync to Use global setting (On), matching the saved inherited values. The complete prior driver profile export is retained privately in the backup directory.

### After restart (01:34 session)
DI PID45756, helper PID25184. Neural feature active at 1280x720; sustained client interval33.33ms/30FPS. Therefore the per-app VSync override did not resolve the plateau; forced global VSync was a potential confounder, NOT an established root cause. GPU spot sample:25% utilization,2505MHz,56W, consistent with a pacing issue (not proof).

Next controlled test: remove RTSS's DI3-specific60FPS cap temporarily. Profile is Program Files (x86)/RivaTuner Statistics Server/Profiles/DisneyInfinity3.exe.cfg. A read backup was saved as local/evidence/performance-20261017/RTSS-DisneyInfinity3-before.cfg. Attempted write failed with Windows access denied, and re-read confirmed Limit=60 remains. The shell printed a success string despite the non-terminating PowerShell error; that string was incorrect. User asked to set the RTSS DI3 profile Framerate limit to0 manually and close overlays, leaving game running. Wait for this result before changing other variables. No RTSS process killed, no profile change applied by the agent.

### Controlled diagnostics after RTSS=0
User set RTSS DI limit to0; still30FPS. Transport-only mode1 at1280x720 remained30FPS with~15% GPU utilization, so neural GPU cost is not the explanation for the plateau. Same-frame handoff async_home=0 also remained30FPS. Restored mode2 and async_home=1 afterwards.

Further NVAPI inspection found an APPLICATION-SPECIFIC FRL_FPS_ID=60 on the 'disney infinity' profile, despite global FRL_FPS_ID=0. Earlier check had covered only global FPS, so it missed this separate cap. At01:42 saved backup local/driver-backups/20261017-014207 and set per-app FRL_FPS_ID=0 for DI and helper. Global settings unchanged. Script nvidia-vsync.py --apply --uncap reproduces this action; a read-only invocation reports current per-app values. Original DI max-FPS value was60; helper inherited0.

Restoring full DLSS mode after transport-only again triggered NGX create0xBAD00000 on live rebuild. This is a reproducible separate recovery problem with this component combination: transport-only -> full evaluation needs a clean helper restart. Current cfg remains mode2/async_home1/work_resolution50/work_upscale1; game temporarily renders fallback60FPS while build retries. DO NOT report fallback60 as successful neural performance. Next required action: restart DI to apply the newly removed driver max-FPS setting and start NGX cleanly; then verify active neural output and frame timing. Need fix live rebuild lifecycle separately after performance baseline established.

To undo additional driver FPS change, restore Max Frame Rate=60 for DI in NVIDIA Control Panel; helper Max Frame Rate previously used global(Off). Mod uninstall does not undo driver profile settings.

### Second restarted session and threading diagnostic staged
01:44 session (DI44580, helper33936) confirmed neural ENGAGED at720p work size but still33.33ms/30FPS after RTSS0 and NVIDIA per-app caps off. Therefore none of those caps has been established as root cause.

Timed CPU sample over3seconds: game render-thread21632~100% of one CPU, game thread23232~100% of one CPU, helper render-thread34832~54% of one CPU. GPU load much lower. Short read-only stack/instruction samples placed render thread in D3D11/NVIDIA driver calls and the other busy thread mainly in Windows syscall code. Original game's threading state was OFF; Feeder turned ID3D11Multithread protection ON at its first frame. This is now a candidate for contention/overhead; still unproven.

Built opt-in diagnostic patch preserving original threading state. Exact patch tracked under patches/feeder-native-threading.patch; reproducible build script and pinned dependencies documented in docs/THREADING-DIAGNOSTIC.md. Default upstream behavior unchanged unless di3_preserve_native_threading=1. Synthetic manual-runtime test passed600frames with neural ENGAGED, original_protection=0, active_protection=0 and clean shutdown. Evidence local/evidence/20261017-015257-integration. This does not prove DI gameplay thread-safety or improvement.

At01:54 staged diagnostic addon for NEXT GAME LAUNCH by renaming the currently mapped stock addon to dlss5-feed.addon32.stock-disabled and copying the custom addon into the original filename. Backup of original binary/cfg and hashes: local/backups/threading-20261017-015450/state.json. Current running process retains original mapped code; full restart required. Config opt-in enabled. No other game binary replaced. Static package verification against the stock manifest will intentionally differ for this diagnostic addon; the ordinary distribution archives still contain the stock addon until gameplay validation.

NEXT: user saves and restarts DI; inspect new threading diagnostic line, neural engagement and sustained frame timing. If no improvement or instability, restore original addon/cfg from the above backup with DI closed. Do not declare60FPS until measured with active neural rendering.
