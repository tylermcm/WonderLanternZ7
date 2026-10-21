# SPDX-License-Identifier: GPL-2.0-or-later
"""Validate stock MAIN or explicitly requested, reproducibly rebuilt Z7 patches."""
import binascii
import hashlib
import json
from pathlib import Path

STOCK_SIZE = 33052088
STOCK_SHA256 = 'e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff'


def validate_firmware(path, report_path=None, stock_container=None):
    payload = Path(path).read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    if report_path is None:
        if stock_container is not None:
            raise ValueError('--stock-container requires --candidate-report')
        if len(payload) != STOCK_SIZE or sha != STOCK_SHA256:
            raise ValueError('Requires stock Z7 C 3.80 MAIN or an explicitly verified candidate')
        return {'modified': False, 'sha256': sha, 'size': len(payload)}
    if stock_container is None:
        raise ValueError('Candidate mode requires --stock-container for independent rebuilding')
    from z30_extensions.build import build, PRESETS
    from z30_extensions.container import extract_eg, Z7_CONTAINER_SHA256
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if report.get('model') != 'Nikon Z7' or report.get('firmware') != 'C 3.80' or report.get('preset') not in PRESETS:
        raise ValueError('Unsupported candidate model, version or preset')
    container = Path(stock_container).read_bytes()
    if hashlib.sha256(container).hexdigest() != Z7_CONTAINER_SHA256:
        raise ValueError('Stock container fingerprint mismatch')
    stock = extract_eg(container)
    expected, expected_report = build(stock, report['preset'], model='z7')
    if payload != expected[:-2] or binascii.crc_hqx(expected, 0):
        raise ValueError('Candidate differs from independently rebuilt patch; preserve the entire appended tail')
    if (report.get('sha256') != expected_report['sha256'] or
            report.get('main_payload_sha256') != sha or report.get('main_payload_size') != len(payload)):
        raise ValueError('Candidate report fingerprint or size mismatch')
    return {'modified': True, 'sha256': sha, 'size': len(payload),
            'preset': report['preset'], 'report': str(Path(report_path).resolve()),
            'stock_container_sha256': Z7_CONTAINER_SHA256,
            'independently_rebuilt': True, 'camera_verified': False}
