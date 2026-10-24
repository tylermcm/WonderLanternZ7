"""Check Z7 playback admission against stock metadata and native instructions.

File/device scheduling, allocation and UI rendering are controlled boundaries.
Callback packets are unit-test inputs; this is not physical audio evidence.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_CPU_ARM_CORTEX_A15, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.platform.z7_380 import StockImage, BASE, SCATTER

STATE, STACK, RETURN, MESSAGE = 0x50010000, 0x500F0000, 0x500FF000, 0x50000200
ANCHOR, AUDIO, NATIVE_BUSY, FORMATS = 0xA1833548, 0xA21AB994, 0xA188D190, 0xA188D1A0
BUSY, ENABLED, LENGTH, PENDING, RESULT = 32, 36, 40, 48, 52
PCM_OFFSET, PCM_LENGTH = 17472, 172800


class Fixture:
    def __init__(self, stock, image, report, *, native_busy=0, enabled=0,
                 movie=0, silent=1, legacy_silent=0):
        self.f = {key: int(value, 16) & ~1 for key, value in
                  report['features']['shutter_sound']['functions'].items()}
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
        self.u.mem_map(BASE, (len(image) + 4095) & ~4095)
        self.u.mem_write(BASE, image)
        self.u.mem_map(0xA1800000, 0x110000)
        self.u.mem_map(0xA2100000, 0x100000)
        self.u.mem_map(0xA2400000, 0x100000)
        self.u.mem_map(0x50000000, 0x100000)
        source, destination, size, _ = SCATTER
        self.u.mem_write(destination, stock[source - BASE:source - BASE + size])
        # Independent stock descriptor addresses: execute the original getter
        # and lookup tables instead of returning values for the patch's key.
        self.word(0xA24E1E00, movie)       # native property 0x138D
        self.word(0xA24E3430, silent)      # native Z7 property 0x576
        self.word(0xA24E3444, legacy_silent)  # unrelated Z30-port key 0x57B
        self.word(ANCHOR + 16, STATE)
        self.word(STATE + 56, 0x5A33534E)
        self.word(STATE + LENGTH, PCM_LENGTH)
        self.word(STATE + ENABLED, enabled)
        self.word(STATE + 64, (0x1C5A << 16) | 2)
        self.u.mem_write(STATE + 64 + 22, struct.pack('<2H', 0, 2))
        self.u.mem_write(NATIVE_BUSY, bytes([native_busy]))
        self.heap = 0x50070000
        self.jobs, self.parser, self.data, self.callbacks = [], [], [], []
        self.property_queries = []
        self.gate = self.config_reached = False
        self.u.hook_add(UC_HOOK_CODE, self.hook)

    def word(self, address, value):
        self.u.mem_write(address, struct.pack('<I', value))

    def words(self, address, count):
        return struct.unpack('<' + 'I' * count, self.u.mem_read(address, count * 4))

    def ret(self, value):
        self.u.reg_write(UC_ARM_REG_R0, value)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def hook(self, u, address, size, context):
        r0, r1, r2 = (u.reg_read(reg) for reg in (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2))
        if self.gate and address == 0x1006BD54:
            self.config_reached = True
            u.emu_stop()
        elif self.gate and address == self.f['complete']:
            self.callbacks.append((r0, self.words(r1 + 4, 1)[0]))
            self.ret(1)
        elif address == 0x1016FE38:
            if r0 > 64:
                raise AssertionError('Unexpected playback allocation')
            result = self.heap
            self.heap += (r0 + 7) & ~7
            self.ret(result)
        elif address == 0x1016FE4A:
            self.ret(0)
        elif address == 0x10170A80:
            u.mem_write(r0, bytes(r1))
            self.ret(0)
        elif address == 0x10170A1C:
            u.mem_write(r0, bytes(u.mem_read(r1, r2)))
            self.ret(r0)
        elif address == 0x1016FEF2:
            self.property_queries.append(r0)  # Let the actual getter execute.
        elif address == 0x100A2D78:
            record = self.words(r1, 1)[0]
            self.jobs.append(dict(event=r0, job=r1, record=record,
                                 kind=u.mem_read(record + 28, 1)[0]))
            self.ret(1)
        elif address in (self.f['render'], 0x103FAC5A):
            self.ret(0)
        elif address == 0x100CF90A:
            u.mem_write(r0, b'\x01')
            self.ret(1)
        elif address == 0x100CF98C:
            self.ret(0)
        elif address == 0x1006B794:
            self.parser.append(self.words(r0, 3))
            self.ret(1)
        elif address == 0x1006B94A:
            self.data.append(dict(descriptor=self.words(r0, 6), caller=r1,
                                  stack_aligned=u.reg_read(UC_ARM_REG_SP) % 8 == 0))
            self.ret(1)
        elif address == 0x100A2DAC:
            self.ret(0x50060000)  # stock resource resolver boundary

    def call(self, address, args=()):
        for reg, value in zip((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3), args):
            self.u.reg_write(reg, value)
        self.u.reg_write(UC_ARM_REG_SP, STACK)
        self.u.reg_write(UC_ARM_REG_LR, RETURN | 1)
        self.u.reg_write(UC_ARM_REG_R4, 0xCAFEBABE)
        self.u.emu_start(address | 1, RETURN, count=30000)
        if not self.config_reached and self.u.reg_read(UC_ARM_REG_PC) != RETURN:
            raise AssertionError('Playback probe exceeded its instruction bound')
        return self.u.reg_read(UC_ARM_REG_R0)

    def preview(self):
        return self.call(self.f['action'], (STATE + 64, 0x239))

    def completion(self, event, result):
        self.word(MESSAGE, 17)
        self.word(MESSAGE + 4, result)
        return self.call(self.f['complete'], (event, MESSAGE))


def verify(stock, image, report):
    stock = StockImage(stock).data
    checks = []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))

    probe = Fixture(stock, image, report)
    check('stock_metadata_is_not_busy_state', probe.words(FORMATS, 1)[0] == 2
          and probe.call(0x1006B540) == 0)
    check('native_accepts_kind_17', probe.call(0x100A2C04, (17, 0, 18)) == 1)
    check('native_rejects_kind_18', probe.call(0x100A2C04, (18, 0, 18)) == 0)
    probe.preview()
    check('idle_preview_queues_with_nonzero_format_metadata', len(probe.jobs) == 1
          and probe.words(STATE + RESULT, 1)[0] == 0)
    check('preview_works_while_enabled_off', probe.words(STATE + ENABLED, 1)[0] == 0
          and len(probe.jobs) == 1)

    busy = Fixture(stock, image, report, native_busy=1)
    busy.preview()
    check('native_busy_blocks_preview', not busy.jobs and busy.words(STATE + RESULT, 1)[0] == 5)

    trigger = Fixture(stock, image, report, enabled=1)
    trigger.call(trigger.f['trigger'])
    check('idle_silent_shot_queues_with_nonzero_format_metadata', len(trigger.jobs) == 1)
    busy_trigger = Fixture(stock, image, report, native_busy=1, enabled=1)
    busy_trigger.call(busy_trigger.f['trigger'])
    check('native_busy_blocks_shot_trigger', not busy_trigger.jobs)

    request = Fixture(stock, image, report)
    request.call(request.f['start'], (STATE,))
    check('start_queues_expected_native_request', len(request.jobs) == 1
          and request.jobs[0]['event'] == 0x0418001E)
    job = request.jobs[0]
    check('queued_kind_is_within_native_exclusive_bound',
          request.call(0x100A2C04, (job['kind'], 0, 18)) == 1)
    request.word(MESSAGE + 20, job['job'])
    request.gate = True
    request.call(0x1006BC46, (MESSAGE,))
    check('actual_native_consumer_reaches_config', request.config_reached and not request.callbacks)

    custom = Fixture(stock, image, report)
    custom.call(custom.f['start'], (STATE,))
    record = custom.jobs[0]['record']
    custom.u.mem_write(AUDIO, bytes(custom.u.mem_read(record, 36)))
    custom.call(custom.f['config'], (MESSAGE, 0x12345678))
    check('owned_config_supplies_format_and_complete_length', custom.parser == [(0x01010502, PCM_LENGTH, 0)])
    custom.call(0x1006BFE6, (MESSAGE,))
    check('owned_data_supplies_pcm_pointer_length_and_flags', len(custom.data) == 1
          and custom.data[0]['descriptor'] == (STATE + PCM_OFFSET, PCM_LENGTH, 1, 0, 0, 0)
          and custom.data[0]['caller'] == MESSAGE and custom.data[0]['stack_aligned'])

    foreign = Fixture(stock, image, report)
    foreign.word(AUDIO + 24, 1)
    foreign.u.mem_write(AUDIO + 28, b'\x11')
    foreign.word(AUDIO + 32, 0x10020001)
    sentinel = (0x22223333, 0x12345678, 0)
    foreign.u.mem_write(MESSAGE, struct.pack('<3I', *sentinel))
    foreign.call(foreign.f['config'], (MESSAGE, 0x76543210))
    check('same_kind_foreign_callback_keeps_stock_config', foreign.parser == [sentinel])
    foreign.call(0x1006BFE6, (MESSAGE,))
    native_size = foreign.words(FORMATS + 17 * 12 + 4, 1)[0]
    # The native sixth word is an output-status slot and is not initialized by
    # the stock caller. Compare only its five actual input fields here.
    check('same_kind_foreign_callback_keeps_stock_audio_data', len(foreign.data) == 1
          and foreign.data[0]['descriptor'][:5] == (0x50060000, native_size, 1, 0, 0)
          and foreign.data[0]['caller'] == MESSAGE and foreign.data[0]['stack_aligned'])

    callback = Fixture(stock, image, report)
    callback.word(STATE + BUSY, 2)
    callback.completion(0x04180022, 0)
    check('native_started_packet_moves_to_playing', callback.words(STATE + BUSY, 1)[0] == 3)
    callback.completion(0x04180023, 0)
    check('native_finished_packet_releases_busy', callback.words(STATE + BUSY, 1)[0] == 0)
    callback.word(STATE + BUSY, 3)
    callback.completion(0x04180023, 1)
    check('native_failure_packet_releases_busy_and_reports_error',
          callback.words(STATE + BUSY, 1)[0] == 0 and callback.words(STATE + RESULT, 1)[0] == 7)

    return dict(passed=all(item['passed'] for item in checks), checks=checks,
                scope='Actual compiled playback routines, original property getter and descriptor tables, stock initialized audio metadata, native bounds and consumer admission.',
                limitations='Property RAM values, heap, UI, ready-state and queue boundaries controlled; callbacks synthetic. No card I/O, physical audio, DSP execution or device completion evidence.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock-eg', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.stock_eg.read_bytes(), args.image.read_bytes(), json.loads(args.report.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    raise SystemExit(not result['passed'])
