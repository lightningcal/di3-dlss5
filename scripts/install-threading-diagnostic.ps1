param([Parameter(Mandatory=$true)][string]$Game)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot
$addon=Join-Path $Game 'mods\di3-dlss5\native\dlss5-feed.addon32'
$cfg=Join-Path $Game 'mods\di3-dlss5\native\dlss5-feed.cfg'
$source=Join-Path $root 'build\threading-diagnostic\dlss5-feed.addon32'
if(!(Test-Path -LiteralPath $source)){throw 'Build the diagnostic first'}
if(!(Test-Path -LiteralPath $addon) -or !(Test-Path -LiteralPath $cfg)){throw 'Existing installed Feeder required'}
$backup=Join-Path $root ('local\backups\threading-'+(Get-Date).ToString('yyyyMMdd-HHmmss'))
New-Item -ItemType Directory $backup | Out-Null
Copy-Item -LiteralPath $addon -Destination "$backup\dlss5-feed.addon32"
Copy-Item -LiteralPath $cfg -Destination "$backup\dlss5-feed.cfg"
$originalHash=(Get-FileHash -LiteralPath $addon).Hash
$disabled=$addon+'.stock-disabled'
if(Test-Path -LiteralPath $disabled){throw 'Stock-disabled copy already exists; review before reinstall'}
# A loaded DLL may be renamed while its existing image remains mapped; never overwrite it in place.
Move-Item -LiteralPath $addon -Destination $disabled
try{
 Copy-Item -LiteralPath $source -Destination $addon
 $text=[IO.File]::ReadAllText($cfg)
 if($text -match '(?m)^di3_preserve_native_threading='){$text=$text -replace '(?m)^di3_preserve_native_threading=\d+','di3_preserve_native_threading=1'}else{$text+="`ndi3_preserve_native_threading=1`n"}
 [IO.File]::WriteAllText($cfg,$text)
}catch{
 if(Test-Path -LiteralPath $addon){Remove-Item -LiteralPath $addon}
 Move-Item -LiteralPath $disabled -Destination $addon
 Copy-Item -LiteralPath "$backup\dlss5-feed.cfg" -Destination $cfg -Force
 throw
}
@{game=$Game;originalSha256=$originalHash;diagnosticSha256=(Get-FileHash -LiteralPath $addon).Hash;backup=$backup;nextLaunchRequired=$true} | ConvertTo-Json | Set-Content "$backup\state.json"
Write-Output "Diagnostic staged for next launch. Original and cfg backup: $backup"
