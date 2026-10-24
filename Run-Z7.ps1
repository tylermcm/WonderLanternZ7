param(
    [ValidateSet('stock','full','liveview-dual','shutter-sound','m900')]
    [string]$Preset = 'full',
    [ValidateRange(1,65535)][int]$Port = 8787,
    [string]$BuildDirectory = '',
    [string]$WslDistro = 'Ubuntu',
    [switch]$MenuOnly,
    [switch]$Native,
    [switch]$OpenBrowser
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$configuration = Join-Path $PSScriptRoot '.private/lab-environment.json'
if (-not $BuildDirectory) {
    $local = if (Test-Path -LiteralPath $configuration) { Get-Content -LiteralPath $configuration -Raw | ConvertFrom-Json } else { $null }
    $BuildDirectory = if ($local.build_directory) { $local.build_directory } else { '.private/builds/20261020-09' }
}
$buildPath = if ([IO.Path]::IsPathRooted($BuildDirectory)) { $BuildDirectory } else { Join-Path $PSScriptRoot $BuildDirectory }
$currentFile = Join-Path $PSScriptRoot 'z7-qemu/.local/sessions/current.json'
if (Test-Path -LiteralPath $currentFile) {
    $current = Get-Content -LiteralPath $currentFile -Raw | ConvertFrom-Json
    $status = $null
    try { $status = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/status" -TimeoutSec 2 } catch { }
    if ($status -and $current.session -eq $status.session -and $current.url -eq "http://127.0.0.1:$Port") {
        $payloadName = if ($Preset -eq 'stock') { 'stock-main.bin' } else { "$Preset.main.bin" }
        $expectedFirmware = [IO.Path]::GetFullPath((Join-Path $buildPath $payloadName))
        $expectedPhoto = -not [bool]$MenuOnly
        if ($current.firmware_path -and [IO.Path]::GetFullPath($current.firmware_path) -eq $expectedFirmware -and [bool]$current.photo_liveview -eq $expectedPhoto) {
            if ($OpenBrowser) { Start-Process "$($current.url)/" }
            Write-Host "The selected app is already available at $($current.url)/"
            return
        }
        throw "A different lab session is using port $Port. Select another -Port."
    }
}
$launchArgs = @((Join-Path $PSScriptRoot 'tools/launch_z7.py'),'--preset',$Preset,'--port',"$Port",'--build-directory',$buildPath,'--wsl-distro',$WslDistro)
if ($MenuOnly) { $launchArgs += '--menu-only' }
if ($Native) { $launchArgs += '--native' }
elseif ($PSBoundParameters.ContainsKey('WslDistro')) { $launchArgs += '--wsl' }
$localPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $localPython) { $pythonCommand = $localPython }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $pythonCommand = (Get-Command py).Source; $launchArgs = @('-3') + $launchArgs }
else { $pythonCommand = (Get-Command python -ErrorAction Stop).Source }
$quotedArgs = $launchArgs | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }
$logDirectory = Join-Path $PSScriptRoot '.private'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$logStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$errorLog = Join-Path $logDirectory "launcher-$logStamp.stderr.log"
$process = Start-Process -FilePath $pythonCommand -ArgumentList $quotedArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDirectory "launcher-$logStamp.stdout.log") -RedirectStandardError $errorLog
if ($OpenBrowser) {
    $deadline = (Get-Date).AddSeconds(60)
    while (-not $process.HasExited -and (Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/status" -TimeoutSec 2
            if ($response.StatusCode -eq 200) { Start-Process "http://127.0.0.1:$Port/"; break }
        } catch { Start-Sleep -Milliseconds 250 }
        $process.Refresh()
    }
}
$process.WaitForExit()
$process.Refresh()
if ($process.ExitCode -ne 0) { Get-Content -LiteralPath $errorLog -Tail 30 | Write-Host }
if ($process.ExitCode -ne 0) { throw "Emulator exited with code $($process.ExitCode)" }
