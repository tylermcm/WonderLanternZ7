param(
    [ValidateSet('stock','full','liveview-dual','shutter-sound','m900')]
    [string]$Preset = 'full',
    [int]$Port = 8787,
    [string]$BuildDirectory = '.private/builds/20261020-09',
    [string]$WslDistro = 'Ubuntu',
    [switch]$MenuOnly
)
$ErrorActionPreference = 'Stop'
$buildPath = if ([IO.Path]::IsPathRooted($BuildDirectory)) { $BuildDirectory } else { Join-Path $PSScriptRoot $BuildDirectory }
$launchArgs = @((Join-Path $PSScriptRoot 'tools/launch_z7.py'),'--preset',$Preset,'--port',"$Port",'--build-directory',$buildPath,'--wsl-distro',$WslDistro)
if ($MenuOnly) { $launchArgs += '--menu-only' }
$localPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $localPython) { $pythonCommand = $localPython }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $pythonCommand = (Get-Command py).Source; $launchArgs = @('-3') + $launchArgs }
else { $pythonCommand = (Get-Command python -ErrorAction Stop).Source }
$quotedArgs = $launchArgs | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }
$process = Start-Process -FilePath $pythonCommand -ArgumentList $quotedArgs -WindowStyle Hidden -Wait -PassThru
if ($process.ExitCode -ne 0) { throw "Emulator exited with code $($process.ExitCode)" }
