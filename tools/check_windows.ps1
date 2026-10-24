param(
    [string]$MsysRoot = '',
    [string]$PythonPath = ''
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $MsysRoot) { $MsysRoot = Join-Path $root '.private/toolchain/msys64' }
if (-not $PythonPath) { $PythonPath = Join-Path $root '.venv/Scripts/python.exe' }
$previousPath = $env:PATH
$previousSystem = $env:MSYSTEM
$previousDirectory = $env:CHERE_INVOKING
Push-Location $root
try {
    function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
    }
    Invoke-Checked $PythonPath @('-m','unittest','discover','-s','tests','-v')
    Invoke-Checked $PythonPath @('-m','unittest','discover','-s','z7-qemu/tests','-p','test_*.py','-v')
    $env:MSYSTEM = 'UCRT64'
    $env:CHERE_INVOKING = 'yes'
    # All generated executables stay inside the ignored private workspace.
    $contracts = @'
set -eu
mkdir -p .private/tests
cc -std=c11 -O1 -g -Iz7-qemu/tests/include z7-qemu/tests/test_gpu.c $(pkg-config --cflags --libs glib-2.0) -lm -o .private/tests/gpu.exe
cc -std=c11 -O1 -g z7-qemu/tests/test_isp.c $(pkg-config --cflags --libs glib-2.0) -lm -o .private/tests/isp.exe
.private/tests/gpu.exe
.private/tests/isp.exe
'@
    Invoke-Checked (Join-Path $MsysRoot 'usr/bin/bash.exe') @('-lc',$contracts)
    $manifest = Get-Content -LiteralPath z7-qemu/.local/build-manifest.json -Raw | ConvertFrom-Json
    if ((Get-FileHash -LiteralPath $manifest.binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.binary_sha256) {
        throw 'QEMU executable fingerprint mismatch'
    }
    $env:PATH = $manifest.native_runtime_path + ';' + $env:PATH
    Invoke-Checked $PythonPath @('z7-qemu/tools/smoke_qemu.py',$manifest.binary)
    Write-Host 'Native host checks passed. Sanitizers and physical-camera behavior were not tested.'
} finally {
    $env:PATH = $previousPath
    $env:MSYSTEM = $previousSystem
    $env:CHERE_INVOKING = $previousDirectory
    Pop-Location
}
