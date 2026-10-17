param([string]$SourceDir='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
if(!$SourceDir){$SourceDir=Join-Path $root '.cache\feeder-src'}
$commit='3c09eabcd138a68d144b6cc396a23e6b493eea4d'
if(!(Test-Path "$SourceDir\.git")){& git clone --depth 1 --branch v1.19.0 https://github.com/jlrouzies-fr/DLSS5-Feeder.git $SourceDir;if($LASTEXITCODE){throw 'Clone failed'}}
if((& git -C $SourceDir rev-parse HEAD).Trim() -ne $commit){throw 'Wrong Feeder commit'}
$patch=Join-Path $root 'patches\feeder-native-threading.patch'
& git -C $SourceDir apply --reverse --check $patch 2>$null
if($LASTEXITCODE){& git -C $SourceDir apply --check $patch;if($LASTEXITCODE){throw 'Patch cannot be applied'};& git -C $SourceDir apply $patch;if($LASTEXITCODE){throw 'Patch failed'}}
$vk=Join-Path $root '.cache\vulkan-headers'
if(!(Test-Path "$vk\.git")){& git clone --depth 1 --branch v1.3.290 https://github.com/KhronosGroup/Vulkan-Headers.git $vk;if($LASTEXITCODE){throw 'Vulkan clone failed'}}
if((& git -C $vk rev-parse HEAD).Trim() -ne 'b379292b2ab6df5771ba9870d53cf8b2c9295daf'){throw 'Wrong Vulkan header revision'}
foreach($d in @('vulkan','vk_video')){New-Item -ItemType Directory -Force "$SourceDir\external\vulkan\$d" | Out-Null; Copy-Item "$vk\include\$d\*.h" "$SourceDir\external\vulkan\$d" -Force}
& cmd.exe /c "$SourceDir\tools\build-addon32.bat"
if($LASTEXITCODE){throw 'Addon build failed'}
$output=Join-Path $root 'build\threading-diagnostic'
New-Item -ItemType Directory -Force $output | Out-Null
Copy-Item "$SourceDir\build\dlss5-feed.addon32" "$output\dlss5-feed.addon32" -Force
Get-FileHash "$output\dlss5-feed.addon32"
Write-Output 'Build only; not deployed. Set di3_preserve_native_threading=1 in the companion cfg to opt in.'
