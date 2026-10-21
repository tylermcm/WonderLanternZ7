"""Check Z7 menu contracts against stock data and actual native instructions.

This is offline regression evidence. It does not model display, card or speaker
hardware. The callback test uses the native no-widget path to expose a skipped
callee stack save without substituting any instructions.
"""
import argparse
import binascii
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.platform.z7_380 import BASE, SCATTER, StockImage
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (UC_CPU_ARM_CORTEX_A15, UC_ARM_REG_R0,
    UC_ARM_REG_R4, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)


def execute_cleanup(image, entry):
    u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A15)
    u.mem_map(BASE, (len(image) + 4095) & ~4095)
    u.mem_write(BASE, image)
    u.mem_map(0x50000000, 0x3000)
    u.mem_map(0xA1837000, 0x1000)
    u.mem_write(0x50002000, struct.pack('<2I', 0xBADC0FFE, 0xA1837BF8))
    u.reg_write(UC_ARM_REG_R0, 0)
    u.reg_write(UC_ARM_REG_R4, 0x12345678)
    u.reg_write(UC_ARM_REG_SP, 0x50002000)
    u.reg_write(UC_ARM_REG_LR, 0x50002F01)
    observation = {}

    def hook(emulator, address, size, unused):
        if address in (0x50002F00, 0xA1837BF8):
            observation['returned'] = address == 0x50002F00
            emulator.emu_stop()

    u.hook_add(UC_HOOK_CODE, hook)
    try:
        u.emu_start(entry, 0, count=100)
    except Exception as error:
        observation['error'] = str(error)
    observation.update(pc=hex(u.reg_read(UC_ARM_REG_PC)),
        r4=hex(u.reg_read(UC_ARM_REG_R4)), sp=hex(u.reg_read(UC_ARM_REG_SP)),
        thumb=bool(u.reg_read(UC_ARM_REG_CPSR) & 32),
        caller_stack=bytes(u.mem_read(0x50002000, 8)).hex())
    return observation


def verify(stock, image, report):
    im = StockImage(stock + binascii.crc_hqx(stock, 0).to_bytes(2, 'big'))
    sound = report['features']['shutter_sound']
    checks = []

    def read(address, size):
        source, destination, length, unused = SCATTER
        if destination <= address and address + size <= destination + length:
            address = source + address - destination
        offset = address - BASE
        if offset < 0 or offset + size > len(image):
            raise ValueError('Read outside candidate: ' + hex(address))
        return image[offset:offset + size]

    def words(address, count):
        return struct.unpack('<' + 'I' * count, read(address, count * 4))

    def check(name, passed, **evidence):
        checks.append(dict(name=name, passed=bool(passed), **evidence))

    setup = im.words(0xA1837BEC, 11)
    if setup[0] != 0x019B0002 or im.rom(setup[10], 28) != 0x11F10854:
        raise ValueError('Stock Setup identity is not Z7 C 3.80')
    setup_init = int(sound['functions']['setup_init'], 16)
    check('Actual Setup constructor seeds labels', words(setup[4], 1)[0] == setup_init)
    metadata = words(setup[10], 7)
    rows = metadata[5] & 0xFFFF
    last_row = words(metadata[3] + (rows - 1) * 28, 7)
    check('Setup has 36 rows and the named sound entry',
          rows == 36 and last_row[0] == 39 and last_row[6] == 0x2333)

    leaf = im.words(0xA1833548 + 0x2A * 44, 11)
    leaf_metadata = im.words(leaf[10], 7)
    native_layout = im.read(leaf_metadata[2], 96)
    native_cleanup = im.words(leaf[4], 8)[2]
    if (native_cleanup != 0x1040525F or leaf_metadata[0] != 0x1008
            or tuple(struct.unpack_from('<I', native_layout, i)[0] for i in (4, 36, 68)) != (1, 4, 0)):
        raise ValueError('Unexpected stock leaf template')
    baseline = execute_cleanup(stock, native_cleanup)
    if not baseline.get('returned') or baseline['sp'] != '0x50002000' or baseline['r4'] != '0x12345678':
        raise ValueError('Native callback fixture did not preserve its caller')
    for index in (0x1C5A, 0x1C5B, 0x1C5C):
        page = sound['pages'][str(index)]
        table = int(page['functions'], 16)
        meta = int(page['metadata'], 16)
        header = words(meta, 7)
        layout = read(header[2], 96)
        kinds = tuple(struct.unpack_from('<I', layout, i)[0] for i in (4, 36, 68))
        check(f'{index:x} layout terminates within owned allocation',
              kinds == (2, 4, 0) and header[0] == leaf_metadata[0], kinds=kinds)
        check(f'{index:x} native back icon preserved', layout[32:64] == native_layout[32:64])
        count = page['count']
        check(f'{index:x} viewport fits all rows', header[5] == (count << 16) | count)
        callbacks = words(table, 8)
        for slot in (2, 7):
            observed = execute_cleanup(image, callbacks[slot])
            check(f'{index:x} callback {slot} preserves caller', observed == baseline,
                  entry=hex(callbacks[slot]), native=baseline, candidate=observed)
        # Locate each immutable page template by its table and metadata,
        # independent of any source constants used to construct it.
        marker = struct.pack('<I', (index << 16) | 2)
        matches = []
        start = 0
        while True:
            offset = image.find(marker, start)
            if offset < 0:
                break
            start = offset + 1
            if offset + 44 <= len(image):
                template = struct.unpack_from('<11I', image, offset)
                if template[4] == table and template[10] == meta:
                    matches.append(template)
        check(f'{index:x} parent is native menu shell',
              len(matches) == 1 and matches[0][1] == leaf[1] == setup[1],
              parents=[hex(template[1]) for template in matches])
    return dict(passed=all(check['passed'] for check in checks), checks=checks,
        scope='Stock Setup identity, private layout bounds and native callback calling convention.',
        limitations='Callback executes its native no-widget path. Real menu rendering and no-file actions require the separate QEMU probe; physical audio remains untested.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.stock.read_bytes(), args.image.read_bytes(), json.loads(args.report.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(result['checks']),
                      'failed': [check['name'] for check in result['checks'] if not check['passed']]}))
    raise SystemExit(not result['passed'])
