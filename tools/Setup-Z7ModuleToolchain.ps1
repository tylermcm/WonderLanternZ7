param()
$ErrorActionPreference = 'Stop'
# Independent optional addition to the root native-Windows laptop setup.
# Installs only inside .private; no system toolchain, WSL or camera changes.
$moduleLabRoot = Split-Path -Parent $PSScriptRoot
$moduleVersion = '0.15.2'
$moduleArchiveHash = '3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c'
$moduleArchiveName = "zig-x86_64-windows-$moduleVersion.zip"
$moduleDownload = Join-Path $moduleLabRoot '.private\downloads'
$moduleToolchain = Join-Path $moduleLabRoot '.private\toolchain'
New-Item -ItemType Directory -Force -Path $moduleDownload, $moduleToolchain | Out-Null
$moduleArchive = Join-Path $moduleDownload $moduleArchiveName
if (-not (Test-Path -LiteralPath $moduleArchive)) {
    $modulePartial = "$moduleArchive.part"
    if (Test-Path -LiteralPath $modulePartial) { throw "A prior partial download exists: $modulePartial" }
    Invoke-WebRequest -Uri "https://ziglang.org/download/$moduleVersion/$moduleArchiveName" -OutFile $modulePartial
    if ((Get-FileHash -LiteralPath $modulePartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $moduleArchiveHash) {
        throw 'Downloaded Zig archive checksum mismatch; partial file retained for inspection'
    }
    Move-Item -LiteralPath $modulePartial -Destination $moduleArchive
}
if ((Get-FileHash -LiteralPath $moduleArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $moduleArchiveHash) {
    throw 'Existing Zig archive checksum mismatch; file preserved'
}
$modulePackage = Join-Path $moduleToolchain "zig-x86_64-windows-$moduleVersion"
if (-not (Test-Path -LiteralPath $modulePackage)) {
    Expand-Archive -LiteralPath $moduleArchive -DestinationPath $moduleToolchain
}
$moduleCompiler = Join-Path $modulePackage 'zig.exe'
if (-not (Test-Path -LiteralPath $moduleCompiler)) { throw 'Incomplete private Zig extraction; preserve and inspect it' }
$moduleActualVersion = (& $moduleCompiler version).Trim()
if ($LASTEXITCODE -ne 0 -or $moduleActualVersion -ne $moduleVersion) { throw 'Unexpected private compiler version' }
$moduleRecord = [ordered]@{
    schema = 1
    version = $moduleActualVersion
    compiler = $moduleCompiler
    compiler_sha256 = (Get-FileHash -LiteralPath $moduleCompiler -Algorithm SHA256).Hash.ToLowerInvariant()
    archive_sha256 = $moduleArchiveHash
    source = "https://ziglang.org/download/$moduleVersion/$moduleArchiveName"
    scope = 'Optional private ARM/Thumb compiler; no firmware or camera operations'
}
$moduleRecord | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $moduleToolchain 'z7-module-toolchain.json') -Encoding utf8
$moduleRecord | ConvertTo-Json
