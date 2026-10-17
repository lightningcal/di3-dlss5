param(
 [Parameter(Mandatory=$true)][string]$CrabeRoot,
 [Parameter(Mandatory=$true)][string]$ReShadeDll,
 [string]$FeederAddonOverride='',
 [switch]$PreserveNativeThreading
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
$cmake=(Get-Command cmake -ErrorAction SilentlyContinue).Source
if(!$cmake){$cmake='C:\Program Files\CMake\bin\cmake.exe'}
& $cmake -S "$root\tests" -B "$root\build\tests" -A Win32 "-DRESHADE_SOURCE=$CrabeRoot/build/reshade-src"
if($LASTEXITCODE){throw 'CMake configure failed'}
& $cmake --build "$root\build\tests" --config Release
if($LASTEXITCODE){throw 'CMake build failed'}
$stage="$root\local\stage\mods\di3-dlss5"
if(!(Test-Path "$stage\native\dlss5-feed.addon32")){throw 'Run package.py prepare first'}
$evidence="$root\local\evidence\$((Get-Date).ToString('yyyyMMdd-HHmmss'))-integration"
New-Item -ItemType Directory -Force $evidence | Out-Null
# Isolate all writable native configuration and logs from the assembled package.
Copy-Item "$stage\native" "$evidence\native" -Recurse
if($FeederAddonOverride){Copy-Item -LiteralPath $FeederAddonOverride -Destination "$evidence\native\dlss5-feed.addon32" -Force}
if($PreserveNativeThreading){Add-Content "$evidence\native\dlss5-feed.cfg" "`ndi3_preserve_native_threading=1"}
@"
[GENERAL]
EffectSearchPaths=$stage\shaders\Shaders\**
TextureSearchPaths=$stage\shaders\Textures\**
PresetPath=$stage\DI3-DLSS5.ini
PreprocessorDefinitions=DLSS5_MV_PROVIDER=3,RESHADE_DEPTH_INPUT_IS_REVERSED=0
[ADDON]
AddonPath=$evidence\native
[DEPTH]
DepthCopyBeforeClears=1
"@ | Set-Content "$evidence\ReShade.ini"
& "$root\build\tests\Release\di3_dlss5_integration.exe" $ReShadeDll $evidence "$evidence\ReShade.ini" | Tee-Object "$evidence\console.txt"
if($LASTEXITCODE){throw "Integration executable failed; inspect $evidence"}
$client=Get-Content "$evidence\native\dlss5-feed.log" -Raw
$neural=Get-Content "$evidence\native\host64\ReShade.log" -Raw
if($client -notmatch 'frame 3 delivered' -or $client -notmatch 'shut down cleanly' -or $neural -notmatch 'feature 18 evaluation succeeded' -or $neural -notmatch 'state=ENGAGED'){throw "Full path did not pass; inspect $evidence"}
@{passed=$true;scene='synthetic x86 D3D11 640x360';frames=600;gameVisualTest='pending'} | ConvertTo-Json | Set-Content "$evidence\result.json"
Write-Output "PASS: confirmed neural engagement through the manual runtime. Evidence: $evidence"
