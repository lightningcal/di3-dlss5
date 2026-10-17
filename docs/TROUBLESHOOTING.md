# DI3 DLSS 5 troubleshooting log

**Updated:** 2026-10-17 (America/Chicago). This is the canonical running test log. Read this before more experiments. `PROGRESS.md` preserves earlier chronological notes, including hypotheses and instructions that have since been superseded.

## Objective and current conclusion

Run Disney Infinity 3.0 Gold Edition with verified DLSS 5 neural rendering at **60 FPS minimum**, while retaining CrabeLoader, MSI Afterburner and RTSS. Neural rendering was verified in earlier sessions. **Latest: the fixed30FPS ceiling is removed after global Background Application Max Frame RateOff; user screenshot69FPS and client logs~75-78FPS. Current faster helper session lacks fresh feature18/ENGAGED evidence, so the complete neural-performance objective remains unverified.** See P41 result/P43 below.

Historical comparison before the global background-cap fix (superseded by P41/P43):

- DLSS5_Feed enabled: **30 FPS**.
- DLSS5_Feed disabled: approximately **138–141 FPS** (earlier reports were about 200 FPS).
- Lumenite Kernel, iMMERSE Launchpad and CAS remain checked in both latest screenshots; Feed is the visible changed checkbox. Provider shown by Feed remains Lumenite Kernel (definition 3).
- RTSS's selected DI3 profile shows a 141 FPS limit. The on/off comparison does not establish RTSS as the cause. It does demonstrate that the Feed path triggers the slowdown in this setup.

**User constraint:** MSI Afterburner and RTSS need to remain running. Do not make quitting or uninstalling either a prerequisite. The previous request to exit RTSS is superseded; that comparison was not performed.

## Verified findings versus open hypotheses

| Finding | Evidence / limitation |
| --- | --- |
| Actual neural rendering activates on this RTX 4070 | Host logs show feature 18 creation/evaluation and `state=ENGAGED`; not just DLAA. |
| Feed-on reaches a steady 33.33 ms / 30 FPS | Repeated live Feeder logs and user screenshots across several scenes/restarts. |
| Lowering neural resolution did not remove the plateau | 100%, 75% and 50% tests; the model's own GPU cost fell substantially. |
| Bypassing NGX evaluation did not remove the plateau | Transport-only mode remained 30 FPS. |
| Changing pipelined versus same-frame handoff did not remove it | Both measured 30 FPS in the transport comparison. |
| Preserving DI's original D3D11 threading protection did not help | Diagnostic log confirmed the candidate change was active; game still 30 FPS. It has been rolled back on disk. |
| The standalone helper can reproduce a ~33 ms native Present wait | Timing probe: rendering/overlay CPU generally under 0.3 ms, native Present approximately 28–33 ms. Reproduced without RenoDX and without the extra Feeder client addon. |
| A raw D3D12 program can reproduce it without ReShade/Feeder/NGX | `di3_native_present`: flags=64, average Present ~33.08 ms. RTSSHooks64 was loaded. This is a dependency clue, not proof RTSS caused it. |
| Root cause remains unconfirmed | Driver, external interception and swap-chain/compositor behavior remain possibilities. Do not label a hypothesis a confirmed fix. |

## Environment and architecture

- Game: `<game>`; 32-bit D3D11.
- GPU/driver measured during setup: RTX 4070 / 616.56.
- Project: `<repo>` (local Git repository; no project commit/push made during initial work).
- CrabeLoader fork: `<CrabeLoader checkout>`, ReShade feature branch `fix/reshade-hosting`, commit `0977b9c` for custom manual-addon lifecycle/native depth work.
- Game bridge uses `Crabe\ReShade32.dll`; native game D3D11 COM objects are preserved. Root ordinary ReShade proxy remains disabled.
- Path: game -> custom ReShade x86 -> Lumenite motion/depth + Feeder addon32 -> shared textures/fences -> matched x64 host -> RenoDX + NGX -> output back to game.
- Feeder v1.19.0, source commit `3c09eabcd138a68d144b6cc396a23e6b493eea4d`, IPC v11.
- RenoDX addon 8.5.0-rc10; SR runtime 310.9.16.
- Selected NR runtime: user supplied `nvngx_dlssnr_compat-fp16-310.9.16-cuda13.4.3/nvngx_dlssnr.dll`, SHA256 `cdfa6c1ec784867182164c7836f324f087b5c9f374d0c9fe46f54999feabf3ed`. Upstream URL not supplied. Provenance: `user-runtime.json`.
- Other downloads, hashes and pinned shaders: `../sources.lock.json`. Original package dependency/layout notes: `../README.md` and `THIRD-PARTY.md`.

RTX 50-series compatibility was discussed from upstream requirements; no RTX 50 hardware test was performed in this session.

## Setup and functionality history

| ID | Change / test | Observed result | Conclusion |
| --- | --- | --- | --- |
| S01 | Investigate ReShade not loading through Crabe | Earlier filename had an extra dot (`ReShade32..dll`); corrected to `ReShade32.dll`. | Correct loading path is essential. |
| S02 | Install ordinary full-addon ReShade through the manual runtime | Initially empty Add-ons page. Manual runtime did not initialize addon lifecycle. | Installing the full-addon binary alone was insufficient for this hosting route. |
| S03 | Add custom ReShade manual-addon lifecycle | Generic Depth and Effect Runtime Sync appeared. | Addon initialization fixed; did not yet provide depth events. |
| S04 | Test DisplayDepth after addon lifecycle fix | Generic Depth reported no depth buffers; flat purple/white output. | Presence of Generic Depth alone did not mean capture worked. |
| S05 | Add native D3D11 draw/clear/deferred-command capture while retaining COM identities | User confirmed real depth buffers and geometry/normal/depth visualization in gameplay. Native immediate/deferred tests, depth preservation and resize tests passed. | Depth functionality verified before DLSS package work. |
| S06 | Commit Crabe/ReShade work and DLL build documentation | Fork commit `0977b9c`; guide `docs/guides/reshade.md`, builder `tools/reshade/build.ps1`. | Reproducible prerequisite maintained separately from this mod repo. |
| S07 | Create independent mod repository and assemble Feeder/host/shaders/runtime package | Crabe manifest and Lua status entry; reversible Python installer; hashes and notices recorded. | Lua entry does not unload a native ReShade addon when disabled. |
| S08 | Public RTX40 NR 310.8 standalone test | 300/300 evaluations; feature 18 created/evaluated. | Functional on tested 4070; not proof of gameplay performance. |
| S09 | User-supplied FP16 NR 310.9.16 standalone test | 300/300 plus confirmed feature 18 evaluation. | Selected for local deployment. |
| S10 | Complete custom x86 manual-runtime synthetic scene | 600 frames; Kernel/Feed compiled, correct depth, IPC connected, frames delivered, neural ENGAGED, clean shutdown. | Integration works in synthetic scene. No 60 FPS gameplay claim follows. |
| S11 | Correct synthetic harness resource lifetime and rerun | Passed; depth resource kept alive through runtime destruction. | Initial lifetime warning addressed in test harness. |
| S12 | Disposable installer/uninstaller roundtrip | Static hashes verified, original loader preserved, previous search paths/preset restored, unrelated overlay setting retained. | Reversible deployment checked. |
| S13 | Deploy actual game package | Config backed up; Crabe loader and custom ReShade DLL hashes unchanged. | Original install backup `local/backups/20261017-010303`. |

## Performance experiments and results

These are historical experiments, not instructions to reapply all changes. Read Current state below before acting. Earlier log timestamps are retained in evidence as written; do not infer a timezone for each original log from this document's timezone.

| ID | Controlled change / observation | Result | Interpretation / follow-up |
| --- | --- | --- | --- |
| P01 | Full 2560x1440 processing, work_resolution=100, async_home=1 | Sustained 30 FPS; feed CPU ~0.25 ms; neural GPU ~7 ms; host NGX-path timing ~8.9 ms. | Model works but target missed. Do not add overlapping timing estimates together. |
| P02 | Work resolution 67% (1714x964), FSR1 expand-back enabled | Shared build failed repeatedly with NGX `0xBAD00000`. | Not a validated setting. Dimension support versus live-rebuild failure was not isolated. |
| P03 | Work resolution 75% (1920x1080), helper recovery | Neural output resumed; still 30 FPS; neural cost around 5.3 ms. | Reduced work did not remove plateau. |
| P04 | Work resolution 50% (1280x720) | Neural active; still 30 FPS; neural GPU approximately 2.8–3.2 ms. | GPU model cost alone does not explain fixed 33.33 ms. |
| P05 | Failed build / missing helper intervals | Some logs showed 60 FPS with no active evaluation. | Fallback rendering; explicitly NOT success with DLSS5. |
| P06 | Stop helper during recovery | Feeder could latch stopped instead of automatically recovering. | Direct process termination is not a reliable live restart method. Use its own restart control or clean launch. |
| P07 | Read NVIDIA global profile; inherited forced VSync found | Per-app VSync-off overrides applied for DI and helper; global profile unchanged. After clean restart, still 30 FPS with neural active. | Potential confounder addressed; not root cause. Backup `local/driver-backups/20261017-013129`. |
| P08 | Agent attempted to edit protected RTSS DI3 profile | Windows access denied. A subsequent shell success string was incorrect; readback confirmed old value remained. | No agent RTSS profile change occurred. |
| P09 | User set RTSS DI3 limit to 0, then tested/restarted | User and logs still reported 30 FPS. | DI3-specific numerical RTSS cap not sufficient explanation. Latest user later selected 141 FPS. |
| P10 | Transport-only mode=1, same 720p shared textures and active shaders; no NGX evaluate | Still 30 FPS; GPU spot sample ~15%. | Slow path exists without the neural model's work. |
| P11 | Same-frame handoff async_home=0 in transport-only comparison | Still 30 FPS. Restored async_home=1. | Simple pipelining toggle not a fix. |
| P12 | Inspect NVIDIA per-app FPS setting | DI profile had independent 60 FPS limit although global limit was off. Disabled DI/helper per-app limit and restarted; still 30 FPS with neural active. | Another cap removed, but not established as cause. Backup `local/driver-backups/20261017-014207`. |
| P13 | Switch transport-only back to full DLSS live | Repeated NGX create `0xBAD00000`; fallback faster until clean restart. | Separate reproducible live-rebuild/recovery defect; do not mistake fallback FPS for success. |
| P14 | CPU/GPU sampling | Two game threads each consumed about one CPU core; helper thread about half a core; GPU much less utilized. Samples included D3D11/NVIDIA and Windows syscall code. | Motivated threading hypothesis; did not establish it. |
| P15 | Build optional addon preserving DI's original multithread protection OFF | Synthetic 600-frame neural test passed with original_protection=0, active_protection=0. | Candidate only; needed real-game test. |
| P16 | Deploy threading candidate and restart DI | Log confirmed flag active; sustained 30 FPS; user reported no improvement. | Hypothesis did not produce a useful fix. Stock addon restored on disk; currently mapped code changes only on next launch. |
| P17 | Add timing-only helper probe; standalone test with RenoDX | Native Present callback interval approximately 28–33 ms; rendering/overlay interval under 0.3 ms. Neural evaluation still passed. | Locates a blocking interval in host presentation; CPU intervals are not GPU execution times. |
| P18 | Repeat standalone timing with RenoDX disabled | Native Present still about 28–33 ms. | RenoDX neural evaluation not required to reproduce this wait. |
| P19 | Compare helper shown-behind and hidden modes, no consumer | Both warm-up tests about 32–33 ms per native Present. | A hidden/shown-behind switch alone did not remove it. Not a test of every possible foreground/composition state. |
| P20 | Remove extra `dlss5-feed-helper.addon64` from isolated host too | Bare ReShade host plus timing probe still approximately 33 ms. | Extra client addon not necessary for this reproduction; its game-package placement still needs correction/review. |
| P21 | Opt-in helper swap-chain tearing override in isolated test | Callback confirmed override requested; native Present still approximately 32–33 ms. | Tested override was ineffective; not deployed to game. |
| P22 | Raw D3D12 Present program, no ReShade/Feeder/NGX | With waitable flag64, average native Present ~33.08 ms; `RTSS=1` confirmed hook DLL loaded. | Wait can occur below the Feeder layer. RTSS presence is correlation, not proof of causation. |
| P23 | Raw-test harness cleanup | Initial version called queue Signal with null fence after first result and exited abnormally; removed that invalid unused call. | First flags64 timing was already printed. Do not claim a valid flags0 result from that initial run. |
| P24 | Try stopping RTSS for a no-injection comparison | Windows access denied. User requires Afterburner/RTSS running. | No RTSS-free comparison completed. Stop requesting global exit as a prerequisite. |
| P25 | Latest same-scene user A/B, RTSS DI3 limit shown at141 | Feed on30 FPS; Feed off~138–141 FPS with other visible shaders still active. | Confirms practical trigger. Preserve this baseline for future controlled tests. |

## Current state (read-only snapshot, 2026-10-17)

Snapshot: `local/evidence/performance-20261017/documentation-state.json`. Settings were read, not reset, while creating this document.

| Setting / artifact | Current observed state |
| --- | --- |
| Feeder enabled / mode | enabled=1, mode=2 (full path) |
| Work resolution | **100%** now; earlier 50% is historical. Do not silently overwrite the user's current value. |
| Expansion / pipeline | work_upscale=1, async_home=1, settle_evals=0 |
| Host window | host_window=0; prior sessions logged automatic --hide on reported exclusive fullscreen. |
| Color / depth | hdr=0; depth_inverted=-1 (Auto); shader depth reversed was1 in supplied screenshots. |
| Motion provider | 3, Lumenite Kernel; user also has Launchpad enabled. No provider switch was tested. |
| RTSS DI3 / Global file limits | DI3=141; Global=117 in disk snapshot. These are not a complete measurement of runtime driver behavior. |
| Original x86 addon restored on disk | SHA256 `34c767bd53a99f51a6cb5d87b267734e04314d16bf495a6c69ab98acd62d0874`, 195584 bytes. |
| Failed diagnostic retained | `native/dlss5-feed.addon32.threading-diagnostic-disabled`; opt-in key removed from cfg. Current process may still map old diagnostic until restarted. |
| Game host addons | `renodx-dlss5.addon64` and `dlss5-feed-helper.addon64`. Timing probe and tearing override have NOT been deployed there. |
| NVIDIA overrides last applied | Per-app VSync Off and Max Frame Rate Off for DI/helper; global unchanged. No additional readback performed for this documentation-only update. |
| Crabe display limit | Last read frameLimit=0 (unlimited). |
| Existing Crabe bridge/loader binaries | Performance experiments did not replace them. |
| Distribution archives | Earlier stock package snapshots; do not assume they include latest diagnostics or this current log. Rebuild deliberately before sharing. |

### Packaging audit issue

During isolation, the assembler was found to place `dlss5-feed-helper.addon64` inside host64. Upstream's build script identifies it as the **in-game client for 64-bit games using a helper**, not the host executable. DI3 uses addon32 as its in-game client. The additional helper64 client is unnecessary in DI's host. Removing it from the isolated test did NOT eliminate the measured wait, so do not call this the performance fix. The assembler has now been corrected to omit this extra client on future builds. The running game deployment is intentionally unchanged while P29 is pending, so the A/B remains controlled. This cleanup is not a proven FPS fix.

## Evidence and rollback map

All paths below are relative to `<repo>` unless a game-root path is stated.

| Artifact | Location |
| --- | --- |
| Initial public RTX40 runtime evidence | `local/evidence/20261017-005850-public-rtx40` |
| User runtime standalone test | `local/evidence/20261017-010058` |
| Initial manual integration | `local/evidence/20261017-010206-manual-integration` |
| Repeated corrected integration | `local/evidence/20261017-010357-integration` |
| Threading synthetic integration | `local/evidence/20261017-015257-integration` |
| Work-resolution/RTSS snapshots | `local/evidence/performance-20261017` |
| Host timing comparisons | `local/probe-test/with-renodx-timing.txt`, `no-consumer-timing.txt`, `behind-timing.txt`, `hide-timing.txt`, `di3-helper-timing.log` |
| Probe/native-test source | `tests/timing/probe.cpp`, `tests/timing/native-present.cpp`, `tests/timing/CMakeLists.txt` |
| Original game ReShade config backup | `local/backups/20261017-010303/ReShade.ini` |
| Original addon/cfg before threading trial | `local/backups/threading-20261017-015450` |
| NVIDIA profile backups / prior values | `local/driver-backups/20261017-013129`, `20261017-014207` |
| Current game client log | `<game>/mods/di3-dlss5/native/dlss5-feed.log` |
| Current game helper logs | `<game>/mods/di3-dlss5/native/host64/dlss5-feed-host.log` and `ReShade.log` |
| Crabe custom ReShade rebuild guide | `<CrabeLoader checkout>\docs\guides\reshade.md` |

Runtime logs are overwritten on subsequent starts. Copy them to a named evidence directory before replacing a component or restarting. Driver profile changes are independent of the mod: ordinary package uninstall does not reverse them. Prior values were inherited global VSync On for both applications, DI Max Frame Rate 60, helper Max Frame Rate inherited Off. Read the recorded changes before restoring; do not overwrite newer user choices.

## How to continue

1. Preserve Afterburner/RTSS and the user's current141 FPS baseline. Further tests must accommodate that constraint.
2. Re-read current cfg and loaded session before choosing a test. Distinguish restored files on disk from code already mapped into a running process.
3. Focus on the **measured native Present wait**, rather than lowering quality again or changing unrelated frame limits.
4. Establish an isolated test that separates external interception/driver/composition behavior while keeping required software running. A per-helper integration configuration may be worth investigating, but no such test has been completed and no specific component is blamed yet.
5. Correct the host addon layout independently, with backup and clear labeling that this is packaging cleanup rather than a proven FPS fix.
6. Resolve live NGX rebuild failures separately once a stable performance baseline exists.
7. Claim success only after logs confirm active neural rendering and sustained >=60 FPS in actual gameplay. Synthetic 300/300 evaluation success and faster fallback rendering do not satisfy this.

## Required record for every new experiment

Append the hypothesis, exact single variable changed, baseline, backup/rollback path and expected discriminating result **before** changing anything. Afterwards append measured FPS/frame time, neural active/inactive status, relevant CPU/GPU/presentation timings, evidence paths and outcome (supported, rejected, or inconclusive). Update Current state if a change remains installed. Record failed attempts and access denials; never replace them with a success claim. Keep this document updated throughout the session.

### Next experiment template

- ID / date:
- Hypothesis and one variable:
- Baseline and user constraints:
- Backup / rollback:
- Exact action:
- Measured result (including neural status):
- Evidence files:
- Conclusion / remaining uncertainty:
- State left installed:

## Continued testing - 2026-10-17

### P26 - Latest user GPU comparison
- User reports Feed enabled still30FPS with~43% GPU utilization; Feed disabled~60% GPU utilization (latest baseline~141FPS).
- Interpretation: consistent with a wait/pacing/CPU limitation; utilization alone does not identify the component. Preserve Afterburner and RTSS running.
- No settings changed by this observation.

### P27 - Read vendor-supported RTSS profile API
- Hypothesis: the supported SDK can inspect and configure a profile for ONLY an isolated test executable, allowing an injection A/B while RTSS/Afterburner remain running.
- Baseline: prior raw D3D12 test flags64 Present~33.08ms and RTSSHooks64 loaded. DI-specific141FPS profile and global settings must remain unchanged.
- Action planned: use installed SDK's RTSSHooks64 LoadProfile/GetProfileProperty for read-only values first. No global/process shutdown.
- Evidence will be saved under local/evidence/performance-20261017/rtss-sdk-read.json.
- Mutation, if needed, will be documented as a separate experiment with readback/rollback; SDK success calls alone are not proof a profile was saved.
- P27 result: SDK agrees with disk for tested fields: Global limit117/detectionLow; DI3 limit141/detectionLow; helper and raw probe inherit117/detectionLow. No numerical30FPS cap found in these fields. Evidence: rtss-sdk-read.json. Read-only; no state change.

### P28 - Isolated raw-test profile, RTSS remains running
- Hypothesis: excluding ONLY di3_native_present.exe from RTSS application detection will distinguish injected interception from the native presentation path without touching DI or global settings.
- One variable: raw probe AppDetectionLevel1 ->0. Other inherited global properties retained.
- Baseline: raw probe Present~33ms with RTSSHooks64 present.
- Rollback: delete only the newly created di3_native_present.exe profile through the same SDK if it was successfully saved. There was no pre-existing matching profile.
- Planned action: LoadProfile(Global), SetProfileProperty(AppDetectionLevel0), SaveProfile(di3_native_present.exe), UpdateProfiles. Verify file exists and fresh SDK reload reads0; if not, record write failure and do not count an A/B test.
- P28 result: SetProfileProperty returned true, but no profile file appeared and fresh SDK reload returned detection1. The save did not persist. Evidence: rtss-probe-profile.json. No exclusion test occurred and no game/global profile changed. Access limitation remains; do not report it as successful configuration.

### P29 - Helper-only RTSS exclusion requested through UI
- Hypothesis: interception of the x64 helper's Present path causes the wait even though the game itself renders141FPS with Feed off. This is an A/B hypothesis, not a conclusion.
- One variable: RTSS Application detection level for dlss5-feed-host64.exe only, Low/inherited -> None. Keep DI profile141FPS and Global117 unchanged, and Afterburner/RTSS running.
- Baseline: current Feed on30FPS, user reports43% GPU; Feed off~141FPS /60% GPU. Helper native Present reproduces~33ms in standalone tests.
- Action requested: user adds game/mods/di3-dlss5/native/host64/dlss5-feed-host64.exe in RTSS, selects detectionNone, restarts only the helper with ReShade's Restart the DLSS5 host button.
- Rollback: remove that newly added helper profile or restore detectionLow/inherited. No pre-existing helper-specific profile was found by the agent.
- Result: PENDING user action/readback. Require new helper PID, module check where accessible, neural ENGAGED and sustained FPS; no claim based only on checkbox state.
- P29 result: user reports still30FPS. Helper restarted as PID44184 at10:11. SDK readback AppDetectionLevel=0; profile file shows EnableHooking=0, HookDXGI=0, HookDirect3D12=0. RTSSHooks64 module remains loaded, which does not by itself prove active hooks. Client returned to33.33ms/30FPS. This exclusion setting did not solve the issue. New host reported consumer did not intercept after300 evaluations, while host/ReShade.log still contained older-session entries; neural status for this restart is therefore NOT verified. Do not cite the old ENGAGED log as evidence for this new PID. Settings left: helper-specific detectionNone; DI/global unchanged. Evidence captured below before subsequent restarts.

### P30 - Read distinct NVIDIA background limiter
- Used primary NVIDIA Profile Inspector source mapping: Frame Rate Limiter - Background Application ID0x10835005 (different from foreground0x10835002 and idle0x10835016 checked earlier).
- Read global, DI and helper profiles: GetSetting status-160 (setting not present) for background limiter; foreground limits remained0 in DI/helper.
- No explicit configured30FPS background value found. Missing-setting status is NOT a measured zero/default. Read-only; no driver settings changed.
- Source: https://github.com/Orbmu2k/nvidiaProfileInspector/blob/master/nvidiaProfileInspector/CustomSettingNames.xml

### P31 - Raw Present swap-chain flag/identity matrix (isolated)
- Hypothesis: the frame-latency-waitable flag or executable-specific interception changes raw Present timing.
- Baseline: standalone raw D3D12 probe flags64, hidden window, sync0+DO_NOT_WAIT, ~33ms. No ReShade/Feeder/NGX.
- Plan: run each flag in a fresh process/window (0 versus64), then repeat with a copy named dlss5-feed-host64.exe in an isolated local folder. That name currently has RTSS detectionNone and NVIDIA per-app overrides; name comparison is therefore not a single-component attribution test.
- Only isolated diagnostic files/processes change. DI, Afterburner, RTSS and game configuration remain running/unchanged. Remove diagnostic copy to roll back. Record return codes and module presence, not only timing.
- P31 result: fresh raw probe averaged33.082ms (flags0) and33.082ms (flags64); helper-named copy averaged33.062ms (flags0) and33.063ms (flags64). All reported RTSS module loaded. Neither removing waitable flag nor this identity/profile control removed the native wait. Evidence: P31-raw-matrix.txt. No game state changed.
- Additional read-only check: NvAPI base and CURRENT global profiles both resolve to Base Profile; no separate global profile was missed. No explicit background/idle/battery setting found. Evidence: active-global-driver.json.

### P32 - Explicit helper-only background limiter Off (isolated raw control)
- Hypothesis: an implicit background limiter can be overridden explicitly even when GetSetting reports no configured value.
- One variable: set NVIDIA background limiter0x10835005=0 only on existing single-app helper profile; do not touch global or DI profiles.
- Baseline: helper-named raw probe ~33.06ms native Present, no ReShade/NGX. Afterburner/RTSS remain running.
- Backup: export full profiles and save original helper setting status. Original status=-160 (absent). Rollback by deleting the newly added profile setting if timing does not improve.
- Result pending. Missing-setting status alone is not proof of a30FPS default.
- P32 result: driver rejected SetSetting(0x10835005) with status-160 before SaveSettings. No override was applied and no timing comparison occurred. Backup: local/evidence/performance-20261017/P32. This test is inconclusive, not a successful explicit-Off test.

### P33 - Raw Present return status and window visibility
- Hypothesis: positive DXGI_STATUS_OCCLUDED has been counted as SUCCEEDED by the diagnostic, and hidden/covered helper windows are throttled by the native presentation path.
- Baseline: all previous raw windows hidden or behind the fullscreen game; ~33ms perPresent. Prior output counted any nonfailure HRESULT as success without printing the status.
- Single variable: hidden versus a small shown/topmost, nonactivating diagnostic window in a raw test. Log exact Present HRESULT counts for both. Test may briefly display a small timing window; no game/driver settings change. Keep Afterburner/RTSS running.
- Rollback: diagnostic process/window exits automatically. Need distinguish genuine successful presents from positive occlusion status before a helper code change.
- P33 result: hidden window33.095ms versus shown/topmost nonactivating window33.081ms; all120calls in each returned S_OK(0), not DXGI_STATUS_OCCLUDED. Hypothesis that positive occlusion status was miscounted is rejected for these runs. Visibility without foreground activation did not help. Evidence: P33-visibility.txt. Diagnostic windows exited; no game/driver settings changed.

### P34 - Read available driver setting names
- Hypothesis: the installed driver may expose a distinct background limiter under a different setting ID than the external mapping tested in P30/P32.
- Action: enumerate public available setting IDs/names and filter background/frame/idle/power terms. Read-only; no global/DI/helper settings changed.
- In parallel, asked the user to inspect NVIDIA Control Panel's actual Global Background Application Max Frame Rate without changing it, because API reads have been absent/unsupported rather than a reliable Off value.
- P34 result: enumeration succeeded, returning130 supported IDs. Matching names included Idle Application Max FPS Limit0x10835016 and Frame Rate Limiter0x10835002, already inspected; no separate background-named setting was exposed. No settings changed. Evidence: local/evidence/performance-20261017/P34-driver-names.json. This does not establish the Control Panel background value; user read-only UI question remains pending.

### P35 - Foreground versus nonactivating raw presentation
- Hypothesis: the helper is being paced specifically as a background application even when visible. P33 did not activate its window.
- One variable: activation of the isolated raw D3D12 test window. Log whether it actually became foreground; a denied activation makes the comparison inconclusive.
- Baseline: shown but nonactivating raw test33.08ms, all S_OK. No ReShade/NGX, hence neural inactive by design.
- Action: extend the raw test with optional activation mode2, preserve previous foreground HWND, run control mode1 then mode2, restore focus when done. A small diagnostic window may briefly appear.
- Rollback: process exits, previous foreground window restored; no game/driver/RTSS settings change. Afterburner and RTSS remain running.
- P35 result: nonactivating foreground=0 averaged33.0827ms; activated foreground=1 averaged8.50815ms (~117.5FPS). All120 calls in both returned S_OK, RTSS module loaded in both. Evidence: P35-foreground.txt. Strong evidence for background-specific pacing in the isolated raw test; not yet a proven driver/RTSS attribution or gameplay fix. Previous foreground restored after each process; neural inactive by design.

### P36 - Supported idle FPS override, helper profile only
- Hypothesis: the installed driver's supported Idle Application Max FPS Limit (0x10835016) governs the measured background-only pacing.
- One variable: temporary explicit0 for that setting in the existing helper-only NVIDIA profile. No global or DI profile changes. RTSS/Afterburner remain running.
- Baseline: fresh helper-named raw test in background ~33ms. Record fresh timing before mutation.
- Backup/rollback: export full profiles, record original setting value/status. Restore original value or delete the temporary setting if originally absent, save and verify. Always restore after isolated comparison, including exceptions. No actual gameplay success claim from this test.
- Planned result: supported API write plus fresh background raw helper timing distinguishes this setting; rejected write means no test.
- P36 result: accepted explicit helper Idle Application Max FPS Limit0; readback verified0. Fresh helper-named raw test33.0646ms before versus33.0621ms after, all120 S_OK, foreground=0. No improvement. Restored original absent setting and verified status-160 again. Evidence: local/evidence/performance-20261017/P36/result.json and profiles-before.txt. This supported idle setting is not a demonstrated fix.

### P37 - Fresh live neural-status capture (read-only)
- Observation: user/helper settings changed/restarted during ongoing diagnostics; do not assume earlier PID44184 or its failed interception remains current. No restart initiated by this agent for this observation.
- Latest client log records helper spawn PID24860 at10:40:51 and full2560x1440 work resolution. Host reports neural feature18 created/evaluated at10:41:06; matching ReShade log reports state=ENGAGED and GPU cost7.58ms with frame33.33ms at10:41:22. This resolves the earlier P29 neural-status uncertainty for this newer session, while performance remains unresolved.
- Preserve current logs below before more restart tests. No game/settings mutations. Helper-specific RTSS detectionNone remains on disk, Global117 and DI141 unchanged. P36 NVIDIA change fully rolled back.

### P38 - NVIDIA Control Panel background cap confirmed; helper-only exception
- User verified Global Background Application Max Frame Rate is30FPS in NVIDIA Control Panel. This is direct UI evidence, unlike the inconclusive/unsupported NVAPI mapping in P30/P32/P34. The supported idle setting in P36 is distinct and did not override it.
- Hypothesis: the background x64 helper inherits this30FPS cap; the game waits for the helper even when its own foreground renderer can run141FPS. P35 foreground/background timing supports this, but gameplay A/B is still required.
- Single variable requested: NVIDIA Control Panel -> Manage3D settings -> Program Settings -> exact game-installed dlss5-feed-host64.exe -> Background Application Max Frame Rate -> Off -> Apply. Keep global30FPS, DI profile, Afterburner/RTSS and neural settings unchanged.
- Helper path: <game>\mods\di3-dlss5\native\host64\dlss5-feed-host64.exe.
- Rollback: restore that single helper program setting to Use global setting(30FPS). Prior program-specific value not directly verified in UI; if it already differs, record before changing.
- Preserve P37 evidence. After Apply, restart only the helper via ReShade Restart the DLSS5 host, return to gameplay, close overlay, measure FPS. Check fresh PID/logs for neural feature18 and ENGAGED before claiming success.
- Result: pending user UI change and gameplay comparison. No Control Panel settings changed by agent; no game restart needed for the requested comparison.
- P38 result: user reports still30FPS and screenshot shows helper Background Application Max Frame Rate Off. Screenshot also shows helper VSync Global-On, while existing bare-name NVAPI lookup still returns explicitOff in profile DI3 DLSS5 - dlss5-feed-host64.exe. This discrepancy requires executable/profile matching investigation; do not reapply old overrides blindly. Game restarted10:46:42; helper PID1512 started10:48:19. New host reports consumer did not intercept, so current neural active status is unverified despite prior sessions working. Client confirms33.33ms steady30FPS. Preserve logs in P39.

### P39 - Read NVIDIA profile executable matching
- Hypothesis: NVIDIA App edits a full-path helper profile distinct from the basename-only profile our earlier overrides targeted, explaining contradictory VSync display.
- Read-only: enumerate profiles/application names and compare bare/full-path FindApplicationByName. Export current profiles and preserve live logs; no settings changed. Baseline remains30FPS after helper backgroundOff user change. No rollback needed.
- P39 result: all matching applications enumerated; only one helper profile, basename and full installed path both resolve to DI3 DLSS5 - dlss5-feed-host64.exe. Explicit VSyncOff and foreground limit0 remain in that profile. Duplicate-profile hypothesis rejected. NVIDIA App screenshot differs from NVAPI; reason unresolved. Evidence: P39/matching.json, profiles.txt and preserved runtime logs.

### P40 - Recheck helper-named background raw test after user exception
- Hypothesis: the applied NVIDIA App helper backgroundOff exception changes the isolated native Present wait even if gameplay remains30FPS.
- One changed condition versus P36 baseline: user-applied helper background exception. No additional settings change. Same helper-named raw test, nonactivating window,120presents; no neural rendering by design.
- Rollback: test exits and restores foreground automatically. RTSS/Afterburner remain running; game configuration untouched. Record whether foreground=0; do not count a foreground test as background success.
- P40 result: helper-named raw test remains33.0633ms with foreground=0,120S_OK; RTSS module present. Thus the displayed helperOff exception has not removed background pacing in the isolated reproduction either. No setting changed during this test. Gameplay30FPS and isolated30FPS remain unresolved; no new root-cause claim.

### P41 - Temporary global background cap A/B through NVIDIA Control Panel
- Hypothesis: the displayed per-program exception is not taking effect, while global30FPS background pacing remains active. A temporary GLOBAL Off test distinguishes effective global policy from a per-program UI/profile problem.
- Requested single variable: NVIDIA Control Panel (not NVIDIA App) -> Manage3D settings -> Global Settings -> Background Application Max Frame Rate30FPS toOff -> Apply. Keep VSync, foreground caps, DI/helper overrides, RTSS and Afterburner unchanged. This is a diagnostic comparison, not a permanent global recommendation.
- Baseline: P40 background raw33.0633ms; foreground P35~8.51ms; gameplay30FPS. User screenshot helper backgroundOff has not changed the raw wait.
- Rollback: restore global Background Application Max Frame Rate30FPS after the comparison (unless user chooses otherwise). Agent cannot perform native desktop UI control with current enabled tool surface; needs user to make this UI setting change.
- After user confirms Apply, run raw comparison first; only if it improves request helper restart and validate current-session feature18/ENGAGED with gameplayFPS. Avoid another full game restart.
- Result: pending user action. No global setting changed by agent.

### P42 - User confirms helper VSync Off, still30FPS
- User screenshot shows NVIDIA App Program Settings for dlss5-feed-host64.exe: Vertical SyncOff and Background Application Max Frame RateOff. User reports gameplay still30FPS. Do not recommend repeating helper VSyncOff as a fix.
- This screenshot is Program Settings, not Global Settings. P41 temporary GLOBAL Background Application Max Frame RateOff comparison remains pending; do not record it as performed or failed. Global background30FPS was last directly verified by user before P38.
- No agent settings changes. Current-session neural status requires fresh log validation before any eventual performance success claim.

### P41 result / P43 - Global backgroundOff removes fixed30FPS ceiling
- User reports the global backgroundOff change appears to work; supplied gameplay screenshot shows69FPS with Enable DLSS Neural Rendering checked. This is observed FPS, not by itself proof that feature18 is executing.
- Fresh background raw helper-named control (foreground=0) averaged0.446062ms perPresent versus P40 33.0633ms. All120 returned S_OK, RTSS module present in both. Evidence: P41-raw-after.txt. Strong controlled support for global background pacing as the cause of the fixed30FPS ceiling; previous program-specificOff and VSyncOff did not resolve it.
- Live game client windows:75.3,75.7,77.8,76.5FPS at10:54:13-10:54:36. Host windows70.6,75.7,76.7,68.1evaluates/s across10:53:48-10:55:01. Full2560x1440 work resolution, onePresent/evaluate, no skipped/owedPresents in sampled host log.
- Important limitation: current helper PID16156 started10:52:54; its host log reports consumer did not intercept at10:53:02. ReShade.log last updated10:52:49, BEFORE current helper, so its earlier ENGAGED entries cannot validate this faster session. Current-session feature18 activation remains unverified. Do not mark the full >=60FPS-with-neural objective complete yet or call this confirmed neural performance.
- State left: user global background capOff, helper program backgroundOff/VSyncOff as shown earlier; RTSS and Afterburner remain running. No agent settings changes or restart. Do not automatically restore global30FPS because it would reintroduce the demonstrated wait; a working program-specific exception remains a separate follow-up if desired.
- Evidence preserved in local/evidence/performance-20261017/P41-after (client.log,host.log,ReShade-stale.log,RenoDX-session.log). Next step: obtain fresh-session neural feature18/ENGAGED evidence at uncapped performance without citing stale logs. Avoid changing quality or unrelated caps.


### V01 - Brightness/tone adjustment guidance (not yet tested)
- User supplied same-scene screenshots and reports DLSS5-enabled output appears darker; prefers a lighter result. Screenshots alone do not verify feature18 execution in the latest helper.
- Verified installed Feeder source src/dlss5-feed32.cpp exposes Global Tone Intensity, Local Tone Intensity and Overall Intensity(default1.0, range0-2). These are effect strengths, not direct brightness/exposure sliders. Diffuse White is documented as ignored for the SDR bridge used here.
- Proposed first single-variable visual test: Add-ons -> DLSS5Feed -> DLSS5 neural-rendering settings -> Global Tone Intensity1.0 to0.8, Apply to the DLSS5host. Compare the same stationary view. This may reduce model-imposed darkening; it does not guarantee brighter output. Rollback1.0. Applying restarts the helper; let it settle and check current neural state.
- Separate alternative if desired: restore Global Tone1.0 and test Overall Intensity0.8 to blend down total relighting. Do not change both at once. Local Tone can be explored separately for local contrast.
- No settings changed by agent, no visual result claimed. FPS/background cap configuration remains unchanged. Await user preference/test result. A separate post-Feed exposure shader is an available fallback if an actual brightness boost is needed.
- V01 result: user reports Global Tone Intensity1.0->0.8 made little noticeable difference. Do not present this as an effective brightness fix. No agent settings mutations; whether host apply completed/current feature18 active remains unverified.

### V02 - Direct post-Feed exposure adjustment (proposed)
- Hypothesis: a direct color exposure multiplier after Feed will visibly brighten the completed frame, independently of neural tone-strength controls.
- Verified installed shader: reshade-shaders/Shaders/SweetFX/Tonemap.fx. Exposure multiplies color by2^Exposure, default0; Gamma then applies pow(color,Gamma), default1.
- Single-variable proposal: restore Global Tone Intensity1.0 if V01 is unwanted; enable Tonemap and place AFTER DLSS5Feed, keep all shader controls neutral except Exposure+0.20 (about15% RGB increase). Compare same view; raise to+0.30 only if needed. Can clip bright highlights and affects HUD too.
- Baseline: user says Global Tone0.8 has little effect; desires lighter output. Rollback: disable Tonemap or Exposure0. No helper restart needed for this game-side shader control. No driver/FPS settings change. Proposed only; no result yet and no agent preset edit.
- V02 result: user confirms the resulting appearance looks good after the Tonemap guidance. Brightness preference satisfied by user visual assessment. Exact chosen exposure is recorded below only if read from the current preset; do not assume the suggested+0.20 was the final value. No FPS or neural-activation validation follows from this visual approval. Preserve the user's current preset; no further brightness changes needed.
- Saved game preset readback on approval: [Tonemap.fx] Exposure=0.202000, Gamma=1.000000, Bleach=0.030000, Saturation=0.000000, Defog=0.000000. These reflect user-selected values, including slight shadow brightening from Bleach; agent did not alter them.

### Settings snapshot - 20261017-111503
- User requested saving current ReShade settings. AutoSavePreset=1 and active preset mods/di3-dlss5/DI3-DLSS5.ini verified. Saved four configuration/preset files with game-relative paths under presets/user-approved-20261017-111503, plus SHA256 manifest and restore instructions. All copied hashes match source. No active files or Git commits changed. Driver settings/shader binaries are outside this settings-only snapshot.

### Complete appearance backup - 20261017-111648
- User clarified all additional effects must be saved. Saved all preset sections, technique states/order and full shader/texture dependencies, plus four configuration files. Verified 90 copied file hashes and ZIP CRC. Backup: local\backups\complete-look-20261017-111648; ZIP alongside it. Private ignored backup includes local third-party shaders; no redistribution or active preset changes. Native DLL/driver settings remain prerequisites.
- Live enabled techniques at capture: Lumenite_Kernel@lumenite_Kernel.fx, DLSS5_Feed@DLSS5_Feed.fx, Tonemap@Tonemap.fx, ContrastAdaptiveSharpen@CAS.fx, HDR@FakeHDR.fx, Vibrance@Vibrance.fx. Preserve these exact on-disk values rather than inferring state from an earlier screenshot.

### Machine setup guide
- Added docs/SETUP.md with verified machine requirements, custom DLL build, pinned runtime installation, decisive global background-cap fix, failed per-helper/VSync comparisons, RTSS coexistence, current-session neural validation, optional visual tuning and complete appearance backups. Explicitly separates cap removal from still-unverified neural activity in the faster session; no universal60FPS or RTX50 test claim. Linked README, included guide in future prepare output, and copied guide into the installed mod as SETUP.md. No active configuration or native binaries changed.
- Validation: existing installer/uninstaller roundtrip unit test passed; package script parses; installed guide SHA256 matches repository guide. Future assembly includes SETUP.md. Previously generated binary archives were not rebuilt and remain older snapshots.

### Guide before/after screenshots
- Added the user-designated before11:08:25_10 and after11:08:15_9 PNGs to docs/images and embedded them in the optional visual-look section of SETUP.md. Originals copied byte-for-byte, without cropping or color edits. Caption explicitly attributes after to DLSS5 plus Tonemap/CAS/FakeHDR/Vibrance and describes separate-frame pose/HUD differences; not a DLSS-only comparison or neural-activation proof. Guide and image assets copied into installed mod, and future preparation includes image dependencies. Verified original/copied hashes and image links in both guide locations. No preset/native changes.

### Personal-information cleanup
- Removed personal author attribution and original local checkout/game paths from distributable documentation and script defaults. Diagnostic scripts now require explicit paths. Removed Windows cache-path usernames from shareable saved presets and refreshed their checksums. Runtime metadata retains filename/hash without the source directory. Local shortcuts ignored. Public component author/license attributions retained. Private ignored backups/logs and active gameplay settings preserved. Staged and installed mod attribution/setup documentation refreshed; source and private assembled archives will be rebuilt from sanitized shareable inputs.
- Validation: installer roundtrip test passed; scans found no original personal name/username/checkout/game paths in shareable files or rebuilt archive text entries; ZIP CRC, Python/PowerShell syntax and sanitized saved-preset checksum checks passed. Private ignored evidence and original backups remain local. No commit or push performed.

### README dependency clarification
- Added prominent required-dependency section explaining the separately developed CrabeLoader patch for ReShade hosting and native D3D11 scene-depth capture. Requires both patched loader and custom32-bit companion DLL, identifies reference branch/commit, and states this mod installer does not apply that prerequisite. Expanded build section and linked setup instructions. No personal attribution added; no binaries/configuration changed.

### Combined CrabeLoader deployment
- User requested merging latest local ReShade fix into combined fixes, building and deploying. Clean merge fix/reshade-hosting commit0977b9c into test/combined-fixes produced mergecommitbe703ae. Loader/bootstrap and companion Win32ReShade rebuilt.120Lua tests passed; native smoke passed120GPU depth checks,3resizes and3addon load/unload cycles. Deployed CrabeLoader.asi,dinput8.dll,Crabe/ReShade32.dll with verified backups/hashes under CrabeLoader checkout build/deploy-backups/20261017-114048-combined-reshade. All four active ReShade/Feeder configuration files verified unchanged. Game/helper closed during deployment. No in-game launch or fresh neural benchmark performed; no push.

### Initial repository commit
- User requested committing all DLSS5 mod work. Commit scope includes source/installer, mod configuration, setup guide/screenshots, experiment record, sanitized saved preset, diagnostic patch and tests. Ignored runtime downloads, build outputs, logs, archives, private backups and local shortcut remain excluded. Existing installer roundtrip and privacy/archive audit passed before staging. This commit does not establish current-session neural performance success; recorded validation limits remain applicable.

### Main README screenshot comparison
- Added before/after images to the main README using existing original PNG assets. Caption explicitly identifies DLSS5 plus Tonemap/CAS/FakeHDR/Vibrance and separate-frame differences. Verified image targets; linked visual setup instructions.
