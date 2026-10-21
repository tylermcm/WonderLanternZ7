"""Small checked Thumb instruction emitter."""
import struct


class Thumb:
    def __init__(self, address):
        if address % 2:
            raise ValueError('Thumb code address must be halfword aligned')
        self.address = address
        self.code = bytearray()
        self.labels = {}
        self.branches = []
        self.loads = []
        self.literals = {}

    def emit(self, hex_bytes):
        payload = bytes.fromhex(hex_bytes)
        if len(payload) % 2:
            raise ValueError('Instructions must be halfword aligned')
        self.code.extend(payload)

    def label(self, name):
        if name in self.labels:
            raise ValueError('Duplicate code label')
        self.labels[name] = len(self.code)

    def branch(self, condition, label):
        if not 0 <= condition <= 14:
            raise ValueError('Invalid branch condition')
        self.branches.append((len(self.code), condition, label))
        self.emit('0000')

    def load(self, register, name, value):
        if not 0 <= register <= 7 or not 0 <= value <= 0xFFFFFFFF:
            raise ValueError('Invalid literal register or value')
        if name in self.literals and self.literals[name] != value:
            raise ValueError('Conflicting literal values')
        self.literals[name] = value
        self.loads.append((len(self.code), register, name))
        self.emit('0000')

    def call(self, name, address):
        self.load(3, name, address)
        self.emit('9847')

    def finish(self):
        code = bytearray(self.code)
        while (self.address + len(code)) % 4:
            code.extend(bytes.fromhex('00bf'))
        positions = {}
        for name, value in self.literals.items():
            positions[name] = len(code)
            code.extend(struct.pack('<I', value))
        for offset, condition, label in self.branches:
            if label not in self.labels:
                raise ValueError('Undefined branch label')
            displacement = self.labels[label] - (offset + 4)
            low, high, mask, prefix = (-2048, 2046, 0x7FF, 0xE000) if condition == 14 else (-256, 254, 255, 0xD000 | condition << 8)
            if displacement % 2 or not low <= displacement <= high:
                raise ValueError('Branch target out of range')
            struct.pack_into('<H', code, offset, prefix | ((displacement // 2) & mask))
        for offset, register, name in self.loads:
            displacement = self.address + positions[name] - ((self.address + offset + 4) & ~3)
            if displacement % 4 or not 0 <= displacement <= 1020:
                raise ValueError('Literal load out of range')
            struct.pack_into('<H', code, offset, 0x4800 | register << 8 | displacement // 4)
        return bytes(code)
