"""Native C loader boundaries and relocated Thumb execution, without firmware.

The C core runs on the host; Keystone supplies a synthetic Thumb module and
Unicorn executes that relocated module. This does not execute Z7 boot/card APIs.
"""
import ctypes
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_z7_module import ABI, TARGET, MAX_FILE, MAX_MEMORY, from_elf, pack_module, seal


class Info(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('image_size', 'bss_size', 'entry_offset', 'relocation_count')]


def thumb_fixture():
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
    code, _ = Ks(KS_ARCH_ARM, KS_MODE_THUMB).asm(f'''
        push {{r4, lr}}
        cmp r0, #0
        beq fail
        ldr r1, [r0]
        cmp r1, #{ABI}
        bne fail
        ldr r1, [r0, #4]
        cmp r1, #12
        blo fail
        ldr r1, [r0, #8]
        ldr r2, expected_target
        cmp r1, r2
        bne fail
        ldr r1, result_pointer
        ldr r2, [r1]
        cmp r2, #0
        bne fail
        ldr r3, marker_pointer
        ldr r2, [r3]
        str r2, [r1]
        movs r0, #0
        pop {{r4, pc}}
      fail:
        movs r0, #1
        pop {{r4, pc}}
        .align 2
      expected_target: .word {TARGET}
      result_pointer: .word 128
      marker_pointer: .word 120
      thumb_pointer: .word 1
    ''', addr=0)
    image = bytearray(code)
    assert len(image) <= 120
    relocs = sorted(image.index(struct.pack('<I', value)) for value in (128, 120, 1))
    image.extend(bytes(128 - len(image)))
    struct.pack_into('<I', image, 120, 0x5a703801)
    return pack_module(image, 16, 0, relocs), relocs


def elf_fixture():
    """A linked ARM ELF with text, BSS, symbols and an ABS32 relocation."""
    names = b'\0__image_end\0__memory_end\0z7_main\0pointer\0'
    symbol = lambda name, value, index: struct.pack('<IIIBBH', names.index(name), value, 0, 0x10, 0, index)
    symbols = (bytes(16) + symbol(b'__image_end', 64, 0xfff1) +
               symbol(b'__memory_end', 80, 0xfff1) + symbol(b'z7_main', 1, 1) +
               symbol(b'pointer', 64, 2))
    image = bytearray(64)
    image[:2] = b'\x70\x47'  # bx lr
    struct.pack_into('<I', image, 4, 64)
    content = bytearray(52)
    sections = [(0,) * 10]
    def section(kind, flags=0, address=0, payload=b'', size=None, link=0, info=0, entsize=0):
        offset = len(content)
        content.extend(payload)
        sections.append((0, kind, flags, address, offset, len(payload) if size is None else size,
                         link, info, 4, entsize))
    section(1, 6, payload=image)
    section(8, 3, 64, size=16)
    section(3, payload=names)
    section(2, payload=symbols, link=3, entsize=16)
    section(9, payload=struct.pack('<II', 4, 4 << 8 | 2), link=4, info=1, entsize=8)
    shoff = len(content)
    content.extend(b''.join(struct.pack('<10I', *s) for s in sections))
    content[:16] = b'\x7fELF\x01\x01\x01' + bytes(9)
    struct.pack_into('<HHIIIIIHHHHHH', content, 16, 2, 40, 1, 1, 0, shoff, 0, 52, 0, 0, 40, len(sections), 0)
    return bytes(content)


class NativeModuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        local = ROOT / '.private/toolchain/msys64/ucrt64/bin/gcc.exe'
        compiler = os.environ.get('Z7_MODULE_CC') or (str(local) if local.exists() else shutil.which('gcc'))
        if not compiler:
            raise unittest.SkipTest('Native module C checks require GCC (Z7_MODULE_CC)')
        parent = ROOT / '.private/tests'
        parent.mkdir(parents=True, exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(prefix='native-modules-', dir=parent)
        cls.binary = Path(cls.temp.name) / ('loader.dll' if os.name == 'nt' else 'loader.so')
        environment = os.environ.copy()
        environment['PATH'] = str(Path(compiler).parent) + os.pathsep + environment.get('PATH', '')
        subprocess.run([compiler, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-shared', '-fPIC', '-I', str(ROOT / 'z7-native-modules/sdk'),
                        str(ROOT / 'z7-native-modules/host/module.c'), '-o', str(cls.binary)],
                       env=environment, check=True, capture_output=True)
        cls.dll_directory = os.add_dll_directory(str(Path(compiler).parent)) if os.name == 'nt' else None
        cls.library = ctypes.CDLL(str(cls.binary))
        cls.validate = cls.library.z7_module_validate
        cls.validate.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(Info)]
        cls.validate.restype = ctypes.c_uint32
        cls.prepare = cls.library.z7_module_prepare
        cls.prepare.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
                                ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(Info)]
        cls.prepare.restype = ctypes.c_uint32

    @classmethod
    def tearDownClass(cls):
        # Explicitly unload so Windows can remove the private temporary DLL.
        import _ctypes
        handle = cls.library._handle
        del cls.validate, cls.prepare, cls.library
        (_ctypes.FreeLibrary if os.name == 'nt' else _ctypes.dlclose)(handle)
        if cls.dll_directory:
            cls.dll_directory.close()
        cls.temp.cleanup()

    def prepared(self, packet, base=0x50000000, capacity=256):
        packet = bytes(packet)
        source = ctypes.create_string_buffer(packet)
        target = ctypes.create_string_buffer(b'\xa5' * (capacity + 32), capacity + 32)
        info = Info(*([0xeeeeeeee] * 4))
        status = self.prepare(source, len(packet), ctypes.byref(target, 16), capacity, base, ctypes.byref(info))
        self.assertEqual(target.raw[:16], b'\xa5' * 16)
        self.assertEqual(target.raw[16 + capacity:], b'\xa5' * 16)
        if status:
            self.assertEqual(target.raw, b'\xa5' * (capacity + 32))
            self.assertEqual(bytes(info), b'\xee' * 16)
        return status, target.raw[16:16 + capacity], info

    def test_relocated_native_thumb_init_at_three_bases_and_api_rejection(self):
        from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
        from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5,
            UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
            UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)
        packet, relocs = thumb_fixture()
        saved = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                 UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
        for base in (0x50000000, 0x51004000, 0x52000000):
            status, memory, info = self.prepared(packet, base)
            self.assertEqual(status, 0)
            self.assertEqual((info.image_size, info.bss_size, info.relocation_count), (128, 16, 3))
            self.assertEqual(memory[128:144], bytes(16))
            for offset in relocs:
                original = struct.unpack_from('<I', packet, 64 + offset)[0]
                self.assertEqual(struct.unpack_from('<I', memory, offset)[0], base + original)
            for abi, size, target, expected in ((ABI, 12, TARGET, 0), (2, 12, TARGET, 1),
                                               (ABI, 8, TARGET, 1), (ABI, 12, 0x01700072, 1)):
                u = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                u.mem_map(base, 4096)
                u.mem_write(base, memory[:144])
                u.mem_map(0x60000000, 0x20000)
                u.mem_write(0x60000000, struct.pack('<III', abi, size, target))
                def call():
                    u.reg_write(UC_ARM_REG_R0, 0x60000000)
                    u.reg_write(UC_ARM_REG_SP, 0x60010000)
                    u.reg_write(UC_ARM_REG_LR, 0x60018001)
                    for index, reg in enumerate(saved):
                        u.reg_write(reg, 0x12340000 + index)
                    u.emu_start(base + info.entry_offset + 1, 0x60018000, count=1000)
                    self.assertEqual(u.reg_read(UC_ARM_REG_PC), 0x60018000)
                    self.assertEqual(u.reg_read(UC_ARM_REG_SP), 0x60010000)
                    for index, reg in enumerate(saved):
                        self.assertEqual(u.reg_read(reg), 0x12340000 + index)
                    return u.reg_read(UC_ARM_REG_R0)
                self.assertEqual(call(), expected)
                self.assertEqual(struct.unpack('<I', u.mem_read(base + 128, 4))[0],
                                 0x5a703801 if expected == 0 else 0)
                if expected == 0:
                    self.assertEqual(call(), 1)  # Retained BSS is not silently reinitialized.

    def test_header_identity_bounds_and_reserved_words_rejected_before_writes(self):
        packet, _ = thumb_fixture()
        changes = [(0, 0x4d32375a), (4, 2), (8, 0x01700072), (12, len(packet) + 4),
                   (16, 0), (16, 63), (16, 0xffffffc0), (20, MAX_MEMORY),
                   (20, 0xffffffff), (24, 1), (24, 128), (28, 0xffffffff)]
        changes += [(off, 1) for off in range(36, 64, 4)]
        for off, value in changes:
            with self.subTest(offset=off, value=value):
                changed = bytearray(packet)
                struct.pack_into('<I', changed, off, value)
                self.assertEqual(self.prepared(seal(changed))[0], 2)
        for size in range(64):
            self.assertEqual(self.prepared(packet[:size])[0], 2)
        self.assertEqual(self.prepared(packet + b'\0')[0], 2)

    def test_crc_covers_header_image_and_relocations(self):
        packet, _ = thumb_fixture()
        for off in (32, 64, 150, len(packet) - 1):
            changed = bytearray(packet)
            changed[off] ^= 1
            self.assertEqual(self.prepared(changed)[0], 3)

    def test_relocations_are_validated_completely_before_destination_changes(self):
        packet, relocs = thumb_fixture()
        table = 64 + 128
        for index, value in ((0, 1), (0, 128), (0, 0xfffffffc),
                             (1, relocs[0]), (1, 0)):
            changed = bytearray(packet)
            struct.pack_into('<I', changed, table + 4 * index, value)
            self.assertEqual(self.prepared(seal(changed))[0], 4)
        for value in (144, 0xffffffff):
            changed = bytearray(packet)
            struct.pack_into('<I', changed, 64 + relocs[-1], value)
            self.assertEqual(self.prepared(seal(changed))[0], 4)

    def test_destination_size_alignment_overflow_and_alias_are_rejected(self):
        packet, _ = thumb_fixture()
        for base, capacity in ((0, 256), (0x50000001, 256), (0xffffffc0, 256), (0x50000000, 143)):
            self.assertEqual(self.prepared(packet, base, capacity)[0], 5)
        source = ctypes.create_string_buffer(packet + bytes(256))
        original = source.raw
        info = Info(*([0xeeeeeeee] * 4))
        self.assertEqual(self.prepare(source, len(packet), ctypes.byref(source, 64), 144,
                                      0x50000000, ctypes.byref(info)), 5)
        self.assertEqual(source.raw, original)
        self.assertEqual(bytes(info), b'\xee' * 16)
        self.assertEqual(self.validate(None, 64, ctypes.byref(info)), 1)
        self.assertEqual(self.validate(source, len(packet), None), 1)

    def test_exact_file_and_memory_limits_and_one_past(self):
        packet = pack_module(bytes(MAX_FILE - 64), 0, 0)
        source = ctypes.create_string_buffer(packet)
        self.assertEqual(self.validate(source, len(packet), ctypes.byref(Info())), 0)
        self.assertEqual(self.validate(source, len(packet) + 1, ctypes.byref(Info())), 2)
        packet = pack_module(bytes(64), MAX_MEMORY - 64, 0)
        status, memory, _ = self.prepared(packet, capacity=MAX_MEMORY)
        self.assertEqual(status, 0)
        self.assertEqual(memory, bytes(MAX_MEMORY))
        with self.assertRaises(ValueError):
            pack_module(bytes(64), MAX_MEMORY - 63, 0)

    def test_zero_bss_and_exact_destination_size(self):
        packet = pack_module(b'\x70\x47' + bytes(62), 0, 0)
        status, memory, info = self.prepared(packet, capacity=64)
        self.assertEqual(status, 0)
        self.assertEqual(memory, packet[64:])
        self.assertEqual(info.bss_size, 0)


class ModuleBuilderTests(unittest.TestCase):
    def test_optional_function_bounds_do_not_change_packet_or_default_report(self):
        data=bytearray(elf_fixture())
        shoff=struct.unpack_from('<I',data,32)[0]
        symoff=struct.unpack_from('<I',data,shoff+4*40+16)[0]+3*16
        struct.pack_into('<I',data,symoff+8,2)
        data[symoff+12]=0x12
        expected=from_elf(data)
        functions={'stale':{}}
        self.assertEqual(from_elf(data,functions),expected)
        self.assertEqual(functions,{'z7_main':dict(address=1,bytes=2,binding=1)})

    def test_optional_function_bounds_reject_size_outside_image(self):
        data=bytearray(elf_fixture())
        shoff=struct.unpack_from('<I',data,32)[0]
        symoff=struct.unpack_from('<I',data,shoff+4*40+16)[0]+3*16
        struct.pack_into('<I',data,symoff+8,66)
        data[symoff+12]=0x12
        with self.assertRaisesRegex(ValueError,'Invalid Thumb function bounds'):
            from_elf(data,{})

    def test_linked_elf_is_packaged_with_bss_and_pointer_relocation(self):
        packet, report = from_elf(elf_fixture())
        self.assertEqual(report['relocations'], [4])
        self.assertEqual(report['bss_bytes'], 16)
        self.assertEqual(packet[:4], b'Z7M1')
        self.assertEqual(len(packet), 132)

    def test_elf_bounds_unsupported_relocations_and_undefined_symbols(self):
        data = elf_fixture()
        for size in (0, 51, len(data) - 1):
            with self.assertRaises(ValueError):
                from_elf(data[:size])
        shoff = struct.unpack_from('<I', data, 32)[0]
        changes = [(shoff + 4 * 40 + 36, 0), (shoff + 5 * 40 + 24, 900),
                   (shoff + 5 * 40 + 28, 900), (shoff + 1 * 40 + 20, 0xffffffff),
                   (24, 0), (shoff + 5 * 40 + 4, 4)]
        for offset, value in changes:
            changed = bytearray(data)
            struct.pack_into('<I', changed, offset, value)
            with self.assertRaises(ValueError):
                from_elf(changed)
        reloc_offset = struct.unpack_from('<I', data, shoff + 5 * 40 + 16)[0]
        changed = bytearray(data)
        struct.pack_into('<I', changed, reloc_offset + 4, 4 << 8 | 255)
        with self.assertRaisesRegex(ValueError, 'Unsupported ARM relocation'):
            from_elf(changed)
        sym_offset = struct.unpack_from('<I', data, shoff + 4 * 40 + 16)[0]
        changed = bytearray(data)
        struct.pack_into('<H', changed, sym_offset + 4 * 16 + 14, 0)
        with self.assertRaisesRegex(ValueError, 'Undefined module symbol'):
            from_elf(changed)

    def test_packer_rejects_invalid_inputs(self):
        image = bytearray(64)
        for bss, entry, relocs in ((-1, 0, []), (MAX_MEMORY, 0, []), (0, 1, []),
                                  (0, 64, []), (0, 0, [4, 0]), (0, 0, [0, 0]),
                                  (0, 0, [1]), (0, 0, [64])):
            with self.assertRaises(ValueError):
                pack_module(image, bss, entry, relocs)
        struct.pack_into('<I', image, 0, 64)
        with self.assertRaises(ValueError):
            pack_module(image, 0, 0, [0])


if __name__ == '__main__':
    unittest.main()
