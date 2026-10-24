param(
    [string]$PythonPath = '',
    [string]$SourceFirmware = (Join-Path $env:USERPROFILE 'Downloads/Z_7_0380.bin'),
    [string]$BuildDirectory = '',
    [ValidateRange(1,64)][int]$Jobs = 4,
    [switch]$SkipQemu
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location $PSScriptRoot
try {
    function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) { throw "$Executable failed with exit code $LASTEXITCODE" }
    }
    function Write-Utf8([string]$Path, [string]$Content) {
        [IO.File]::WriteAllText($Path, $Content, (New-Object Text.UTF8Encoding $false))
    }
    New-Item -ItemType Directory -Path .private/stock,.private/downloads,.private/toolchain,.private/tmp -Force | Out-Null
    $stock = Join-Path $PSScriptRoot '.private/stock/Z_7_0380.bin'
    $expected = '07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2'
    if (-not (Test-Path -LiteralPath $stock)) {
        if ((Get-FileHash -LiteralPath $SourceFirmware -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
            throw 'Requires the original Nikon Z7 C 3.80 container; downloaded firmware hash differs.'
        }
        Copy-Item -LiteralPath $SourceFirmware -Destination $stock
    }
    if ((Get-FileHash -LiteralPath $stock -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Private stock firmware hash differs; original file preserved.'
    }
    $python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    $privatePython = Join-Path $PSScriptRoot '.private/python-runtime/python.exe'
    if (-not $PythonPath -and (Test-Path -LiteralPath $privatePython)) { $PythonPath = $privatePython }
    if (-not (Test-Path -LiteralPath $python)) {
        if ($PythonPath) { Invoke-Checked $PythonPath @('-m','venv','.venv') }
        elseif (Get-Command py -ErrorAction SilentlyContinue) { Invoke-Checked 'py' @('-3','-m','venv','.venv') }
        else { Invoke-Checked 'python' @('-m','venv','.venv') }
    }
    Invoke-Checked $python @('-c','import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"')
    Invoke-Checked $python @('-m','pip','install','-r','requirements-lab.txt')
    $packages = (& $python -c 'import sysconfig; print(sysconfig.get_path("purelib"))').Trim()
    if ($LASTEXITCODE -ne 0) { throw 'Could not locate virtual environment packages' }
    Write-Utf8 (Join-Path $packages 'wonderlantern-source.pth') ((Join-Path $PSScriptRoot 'z7-firmware-extensions/src') + "`n")
    $msys = Join-Path $PSScriptRoot '.private/toolchain/msys64'
    if (-not $SkipQemu) {
        if (-not (Test-Path -LiteralPath (Join-Path $msys 'usr/bin/bash.exe'))) {
            $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/msys2/msys2-installer/releases/latest'
            $asset = $release.assets | Where-Object name -Match '^msys2-base-x86_64-.*\.sfx\.exe$' | Select-Object -First 1
            if (-not $asset -or $asset.digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'MSYS2 release lacks a SHA-256 digest' }
            $archive = Join-Path $PSScriptRoot '.private/downloads/msys2-base.sfx.exe'
            Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archive
            if ('sha256:' + (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.digest) {
                throw 'MSYS2 release archive digest mismatch'
            }
            $asset | ConvertTo-Json -Depth 5 | Set-Content .private/downloads/msys2-release.json
            Invoke-Checked $archive @('-y',('-o' + (Join-Path $PSScriptRoot '.private/toolchain')))
        }
        $env:MSYSTEM = 'UCRT64'
        $env:CHERE_INVOKING = 'yes'
        $bash = Join-Path $msys 'usr/bin/bash.exe'
        Invoke-Checked $bash @('-lc','pacman -Syu --noconfirm')
        # Reopen after core updates, as required by MSYS2.
        Invoke-Checked $bash @('-lc','pacman -Syu --noconfirm')
        Invoke-Checked $bash @('-lc','pacman -S --needed --noconfirm make diffutils mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-glib2 mingw-w64-ucrt-x86_64-pixman mingw-w64-ucrt-x86_64-pkgconf mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-meson mingw-w64-ucrt-x86_64-dtc mingw-w64-ucrt-x86_64-zlib')
        $qemuArgs = @('z7-qemu/tools/build.py','--work-dir','.private/qemu','--msys-root',$msys,'--jobs',"$Jobs")
        if (Test-Path -LiteralPath .private/downloads/qemu-10.2.4.tar.xz) { $qemuArgs += @('--archive','.private/downloads/qemu-10.2.4.tar.xz') }
        Invoke-Checked $python $qemuArgs
    }
    & (Join-Path $PSScriptRoot 'tools/check_windows.ps1') -MsysRoot $msys -PythonPath $python
    if (-not $BuildDirectory) { $BuildDirectory = '.private/builds/' + (Get-Date -Format 'yyyyMMdd-HHmmss') }
    if (Test-Path -LiteralPath $BuildDirectory) { throw 'Use a new BuildDirectory to preserve earlier candidates.' }
    Invoke-Checked $python @('z7-qemu/tools/make_cmos.py')
    Invoke-Checked $python @('tools/build_firmware.py','--output',$BuildDirectory)
    Invoke-Checked $python @('tools/check_candidate_inputs.py','--build',$BuildDirectory)
    $configuration = @{
        runtime = 'windows-native'
        windows_python = $python
        msys_root = $msys
        build_directory = $BuildDirectory
    } | ConvertTo-Json
    Write-Utf8 (Join-Path $PSScriptRoot '.private/lab-environment.json') ($configuration + "`n")
    Write-Host 'Build, native host and candidate checks passed. Start the local app with .\Run-Z7.ps1'
} finally { Pop-Location }
