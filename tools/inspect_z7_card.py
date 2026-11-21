"""Read named Z7 card files into a new PRIVATE backup; never write to the card.

SPDX-License-Identifier: MIT. Requires an explicit external card drive. This
does not stage firmware, establish the installed camera image, or clear a flash.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from prepare_flash_review import ROOT, require_private_output

LIMITS = {'EG161080.BIN': 64 << 20, 'Z_7_0380.bin': 256 << 20,
          'Z7APP.BIN': 16 << 20, 'Z7CFG0.DAT': 4096, 'Z7CFG1.DAT': 4096}


def drive_identity(letter):
    if not re.fullmatch('[A-Za-z]', letter):
        raise ValueError('Specify one explicit card drive letter')
    environment = dict(os.environ, Z7_INSPECT_DRIVE=letter.upper())
    script = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$z7Letter = $env:Z7_INSPECT_DRIVE
$z7Volume = Get-Volume -DriveLetter $z7Letter
$z7Partition = Get-Partition -DriveLetter $z7Letter
$z7Disk = Get-Disk -Number $z7Partition.DiskNumber
[ordered]@{
    drive = $z7Letter
    system_drive = ($env:SystemDrive -replace ':', '')
    volume_id = $z7Volume.UniqueId
    label = $z7Volume.FileSystemLabel
    filesystem = $z7Volume.FileSystem
    volume_bytes = $z7Volume.Size
    disk_number = $z7Disk.Number
    disk_id = $z7Disk.UniqueId
    disk_name = $z7Disk.FriendlyName
    bus = [string]$z7Disk.BusType
    boot = [bool]$z7Disk.IsBoot
    system = [bool]$z7Disk.IsSystem
} | ConvertTo-Json -Compress
"""
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive',
                             '-Command', script], env=environment, check=True,
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    return json.loads(result.stdout)


def check_identity(identity):
    if (identity['drive'].upper() == identity['system_drive'].upper() or
            identity['boot'] or identity['system'] or
            identity['bus'] not in ('USB', 'SD', 'MMC')):
        raise ValueError('Selected drive is not an identified external card volume')


def digest(handle):
    result = hashlib.sha256()
    for block in iter(lambda: handle.read(1 << 20), b''):
        result.update(block)
    return result.hexdigest()


def inspect_card(card_root, output, identity, recheck):
    check_identity(identity)
    card_root = card_root.resolve(strict=True)
    output = require_private_output(output)
    if output.is_relative_to(card_root):
        raise ValueError('Backup output must not be on the source card')
    output.mkdir(parents=True, exist_ok=False)
    report = dict(schema=1, timestamp=datetime.now(timezone.utc).isoformat(),
                  source_identity=identity, files={}, complete=False,
                  source_access='read-only', card_written=False,
                  installation_cleared=False, installed_image_readback=False,
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        for name, maximum in LIMITS.items():
            source = card_root / name
            if not source.exists():
                report['files'][name] = dict(present=False)
                continue
            if source.is_symlink() or not source.is_file() or source.resolve().parent != card_root:
                raise ValueError('Named card input is not a regular root file: ' + name)
            before = source.stat()
            if before.st_size > maximum:
                raise ValueError('Named card input exceeds inspection limit: ' + name)
            target = output / name
            with source.open('rb') as incoming, target.open('xb') as backup:
                for block in iter(lambda: incoming.read(1 << 20), b''):
                    backup.write(block)
            with target.open('rb') as backup, source.open('rb') as incoming:
                saved, current = digest(backup), digest(incoming)
            after = source.stat()
            if saved != current or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise ValueError('Source changed or backup readback differs: ' + name)
            report['files'][name] = dict(present=True, bytes=after.st_size, sha256=saved,
                                         backup_readback_verified=True)
        observed = recheck()
        check_identity(observed)
        if observed != identity:
            raise ValueError('Card identity changed during inspection')
        report['complete'] = True
    except Exception as error:
        report['error'] = str(error)
        raise
    finally:
        (output / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n',
                                               encoding='utf-8', newline='\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--drive', required=True, help='Explicit external card drive letter, e.g. E')
    parser.add_argument('--output', type=Path, required=True, help='New lab .private/ backup directory')
    args = parser.parse_args()
    identity = drive_identity(args.drive)
    report = inspect_card(Path(args.drive.upper() + ':\\'), args.output, identity,
                          lambda: drive_identity(args.drive))
    print(json.dumps(dict(output=str(args.output.resolve()), complete=report['complete'],
                          backed_up=sum(item['present'] for item in report['files'].values()),
                          card_written=False, installation_cleared=False)))


if __name__ == '__main__':
    main()
