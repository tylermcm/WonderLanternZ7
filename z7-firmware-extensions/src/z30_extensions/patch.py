"""Checked equal-length edits and aligned code append with a fresh EG CRC."""
import binascii
from dataclasses import dataclass
from .platform.z30_120 import sha256


@dataclass(frozen=True)
class Edit:
    offset: int
    expected: bytes
    replacement: bytes
    name: str


def apply_patch(source, edits, append, *, expected_sha256, base, capacity):
    source = bytes(source)
    append = bytes(append)
    if sha256(source) != expected_sha256:
        raise ValueError('Source SHA-256 mismatch')
    if len(source) < 4 or binascii.crc_hqx(source, 0):
        raise ValueError('Source CRC mismatch')
    start = len(source) - 2
    if append and (start % 4 or len(append) % 4):
        raise ValueError('Appended code must be aligned to four bytes')
    if start + len(append) > capacity:
        raise ValueError('Payload exceeds region capacity')
    ordered = sorted(edits, key=lambda e: e.offset)
    end = 0
    for edit in ordered:
        if not edit.expected or len(edit.expected) != len(edit.replacement):
            raise ValueError('Edits must be nonempty and equal in length')
        if edit.offset < end or edit.offset + len(edit.expected) > start:
            raise ValueError('Edits overlap or cross the source payload boundary')
        if source[edit.offset:edit.offset + len(edit.expected)] != edit.expected:
            raise ValueError(f'Expected bytes mismatch at {edit.offset:#x}')
        end = edit.offset + len(edit.expected)
    output = bytearray(source[:-2] + append)
    for edit in ordered:
        output[edit.offset:edit.offset + len(edit.expected)] = edit.replacement
    output += binascii.crc_hqx(output, 0).to_bytes(2, 'big')
    if binascii.crc_hqx(output, 0):
        raise ValueError('Output CRC mismatch')
    report = {
        'source_sha256': sha256(source), 'sha256': sha256(output),
        'size': len(output), 'crc_residue': 0,
        'append_address': hex(base + start), 'append_length': len(append),
        'offset_space': 'decoded_eg_module',
        'edits': [{'name': e.name, 'offset': hex(e.offset), 'size': len(e.expected),
                   'expected_hex': e.expected.hex(), 'replacement_hex': e.replacement.hex()} for e in ordered],
    }
    return bytes(output), report
