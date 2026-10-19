# Opt-in D3D11 threading diagnostic

Not yet verified in DI gameplay. Keep the original addon available for rollback.

CPU observation: two DI threads consume about one full core each at30FPS, while GPU use remains low. Feeder enables ID3D11Multithread protection on a context whose original setting is OFF. This is a candidate source of overhead/contention, not an established root cause. The upstream implementation intentionally enables protection for concurrent context access, so preserving the original state needs actual DI stability testing.

The narrowly scoped patch adds a config opt-in `di3_preserve_native_threading=1`, read at first device adoption. It keeps the original setting rather than enabling protection. Default behavior remains upstream. It logs original and active protection plus render-thread ID. Device cleanup restores the initial state as before.

Build prerequisites: Git, VS2022 C++ Build Tools, Windows SDK. From repository root:

```powershell
& .\scripts\build-threading-diagnostic.ps1
& .\scripts\test-integration.ps1 -CrabeReShadeRoot 'PATH_TO_CRABERESHADE_CHECKOUT' -ReShadeDll 'PATH_TO_CUSTOM_ReShade32.dll' -FeederAddonOverride .\build\threading-diagnostic\dlss5-feed.addon32 -PreserveNativeThreading
```

Pinned Feeder v1.19.0 commit3c09eabcd138a68d144b6cc396a23e6b493eea4d, patch in patches/feeder-native-threading.patch. Vulkan-Headers v1.3.290 commitb379292b2ab6df5771ba9870d53cf8b2c9295daf supplies missing compile-time headers only. The upstream build script produces x86 Release addon code; the64-bit host is unchanged. Builder does not deploy automatically.

For a controlled gameplay test: back up the original game/native addon and cfg; replace only dlss5-feed.addon32; add the opt-in key; fully restart DI. Require the DI3 threading diagnostic log line with original_protection=0 and active_protection=0, neural engagement and stable output. Compare FPS, movement, scene transitions and exit. A successful synthetic test proves neither safety of concurrent DI context access nor a gameplay performance improvement.

Rollback: close DI, restore original addon and cfg from the recorded backup, then restart. Do not distribute this diagnostic as a proven performance fix until the gameplay test succeeds.

Local staged test (01:54): installer script install-threading-diagnostic.ps1 has placed the candidate addon for the next game launch, retaining stock code as .stock-disabled. Original addon/cfg backup: local/backups/threading-20261017-015450. Current running process continues using its mapped stock addon. After closing DI, rollback by copying the backed-up addon and cfg into game/mods/di3-dlss5/native and deleting the redundant .stock-disabled file. The ordinary builder/archives still use stock Feeder. package.py verify will report the intentional diagnostic binary difference until restored.
