"""Execute an original-Z7 100-byte display-parameter handler candidate.

SPDX-License-Identifier: MIT. This read-only research audit does not install a
hook or establish highlight threshold/pattern semantics. Incoming packet/state buffers
and request completion are supplied; native copy/store instructions execute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_splash_image import NativePNG, MEM, BASE, STOCK_SHA
from build_z7_module_host import ROOT

ENTRY, COMPLETION = 0x1023e214, 0x102396c0
STATE_POINTER = 0xa180a588
TABLE_SLOTS = (0x1062a01c, 0x1062a058, 0x1062a094, 0x1062a0d0)


class ParametersFixture(NativePNG):
    def __init__(self, raw):
        super().__init__(raw)
        self.u.mem_map(0xa1d68000, 0x1000)  # Supplied initialized service-state bytes.
        self.completions = []
        self.native_handler_entries = []

    def hook(self, u, address, size, context):
        if address == ENTRY:
            self.native_handler_entries.append(u.reg_read(UC_ARM_REG_R0))
        if address == COMPLETION:
            self.completions.append((u.reg_read(UC_ARM_REG_R0), u.reg_read(UC_ARM_REG_R1)))
            self.ret(0)
        else:
            super().hook(u, address, size, context)


def audit(raw):
    digest = hashlib.sha256(raw).hexdigest()
    if digest != STOCK_SHA:
        raise ValueError('Exact private original-Z7 C3.80 main image required')
    checks = []

    def check(name, good):
        checks.append(dict(name=name, passed=bool(good)))
        if not good:
            raise AssertionError(name)

    check('four-original-native-table-slots-reference-this-handler', all(
        struct.unpack_from('<I', raw, slot - BASE)[0] == ENTRY | 1 for slot in TABLE_SLOTS))
    request, source, state = MEM + 0x1000, MEM + 0x2000, MEM + 0x3000
    payloads = [bytes(100), bytes([255]) * 100, bytes(range(100)), bytes((i * 73 + 19) & 255 for i in range(100))]
    for case, payload in enumerate(payloads):
        f = ParametersFixture(raw)
        state_before = b'\xa5' * 256
        source_before = b'\xc3' * 16 + payload + b'\xe7' * 20
        f.u.mem_write(state, state_before)
        f.u.mem_write(source - 16, source_before)
        f.u.mem_write(request, b'\x5a' * 64)
        f.u.mem_write(request + 0x14, struct.pack('<I', source))
        request_before = bytes(f.u.mem_read(request, 64))
        f.u.mem_write(STATE_POINTER, struct.pack('<I', state))
        result = f.call(ENTRY, request)
        expected_state = bytearray(state_before)
        expected_state[0x24:0x28] = struct.pack('<I', 1)
        expected_state[0x28:0x8c] = payload
        expected_source = bytearray(source_before)
        expected_source[116:120] = struct.pack('<I', 1)
        check(f'case{case}-native-return-and-completion-arguments', result == 1 and f.completions == [(request, 0)])
        check(f'case{case}-exact100-byte-copy-and-state-ready-word-only', bytes(f.u.mem_read(state, 256)) == bytes(expected_state))
        check(f'case{case}-source-acknowledgement-at100-preserves-payload-and-padding', bytes(f.u.mem_read(source - 16, len(source_before))) == bytes(expected_source))
        check(f'case{case}-request-descriptor-unchanged', bytes(f.u.mem_read(request, 64)) == request_before)
    decoder = ParametersFixture(raw)
    for selector in (0, 1):
        decoder.u.mem_write(0xa180a568, bytes([selector]))
        for family in (0, 1):
            command = 0x42060007 + family * 0x2000
            decoder.u.mem_write(request + 0x10, struct.pack('<I', command))
            decoder.u.mem_write(MEM + 0x4000, b'\xff' * 12)
            result = decoder.call(0x102396e2, request, MEM + 0x4000, MEM + 0x4004, MEM + 0x4008)
            normalized = [decoder.u.mem_read(MEM + 0x4000 + 4 * i, 1)[0] for i in range(3)]
            check(f'decoder-selector{selector}-family{family}-accepts-only-matching-output',
                  result == int(selector == family) and normalized == ([0, 6, family] if selector == family else [255] * 3))
    for selector in (0, 1):
        for native_state in range(1, 5):
            f = ParametersFixture(raw)
            payload = bytes((i * 17 + selector * 37 + native_state) & 255 for i in range(100))
            f.u.mem_write(state, b'\xa5' * 256)
            f.u.mem_write(STATE_POINTER, struct.pack('<I', state))
            f.u.mem_write(0xa180a568, bytes([selector]))
            f.u.mem_write(0xa1d68e54, bytes([native_state]))
            f.u.mem_write(request, bytes(64))
            f.u.mem_write(request + 0x10, struct.pack('<2I', 0x42060007 + selector * 0x2000, source))
            f.u.mem_write(source, payload + b'\xe7' * 4)
            result = f.call(0x10239840, request)
            check(f'router-selector{selector}-state{native_state}-calls-original-parameter-handler',
                  result == 1 and f.native_handler_entries == [request] and f.completions == [(request, 0)])
            check(f'router-selector{selector}-state{native_state}-publishes-exact-payload-and-ack',
                  bytes(f.u.mem_read(state + 0x28, 100)) == payload and
                  bytes(f.u.mem_read(state + 0x24, 4)) == bytes(f.u.mem_read(source + 100, 4)) == struct.pack('<I', 1))
    return dict(passed=True, checks=checks, stock_main_sha256=digest,
                native_handler=hex(ENTRY), native_state_pointer=hex(STATE_POINTER), payload_bytes=100,
                state_ready_offset=0x24, state_payload_offset=0x28, source_acknowledgement_offset=100,
                supplied_boundaries=['Incoming request and display-state buffers', 'Request completion callback'],
                original_memory_copy_and_stores_execute=True, commands_42060007_and42062007_route_to_parameter_handler=True,
                native_decoder_and_state_dispatcher_execute=True, highlight_parameter_semantics_verified=False,
                lcd_evf_or_movie_mapping_verified=False, highlight_threshold_or_pattern_semantics_verified=False,
                actual_pixels=False, module_installed=False, physical_camera_or_card_access=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    out = a.output.resolve()
    if not out.is_relative_to(ROOT / '.private') or out.exists():
        p.error('Choose a new private evidence output')
    result = audit(a.stock_main.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, checks=len(result['checks']))))


if __name__ == '__main__':
    main()
