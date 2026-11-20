# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded read-only native OpenVG entry observer for the private RSP harness.

Breakpoint stepping follows module_file_fixture's unrelated-dispatch pattern.
No guest registers, code, argument buffers or return values are rewritten.
Single-stepping affects diagnostic timing; this is not a hardware timing test.
"""
import json
import struct

ENTRIES = {
    0x10450c4c: 'vgCopyImage', 0x10450c86: 'vgDrawImage',
    0x10450cbc: 'vgSetPixels', 0x10450d00: 'vgWritePixels',
    0x10450da4: 'vgCopyPixels', 0x10450df4: 'vgGetPixels',
    0x10450e3c: 'vgReadPixels',
}


def observing_remote(base_class, output):
    class GraphicsAPIRemote(base_class):
        api_enabled = False

        def api_start(self):
            if self.fixture_enabled:
                raise RuntimeError('Retire the module filesystem fixture before API observation')
            self.api_records = []
            self.api_points = set()
            for address in ENTRIES:
                if self.plain(f'Z1,{address:x},2') != 'OK':
                    raise RuntimeError('Cannot install native API observation')
                self.api_points.add(address)
            self.api_enabled = True
            self.api_save()

        def api_save(self):
            (output / 'graphics-api-observation.json').write_text(json.dumps(dict(
                scope='Native entry arguments/stack and original prologue single-step; no guest writes or returns supplied',
                limit=64, limit_reached=len(self.api_records) == 64, records=self.api_records), indent=2) + '\n',
                encoding='utf-8', newline='\n')

        def api_stop(self):
            for address in tuple(self.api_points):
                if self.plain(f'z1,{address:x},2') != 'OK':
                    raise RuntimeError('Cannot retire native API observation')
                self.api_points.remove(address)
            self.api_enabled = False
            self.api_save()

        def receive(self):
            while True:
                packet = super().receive()
                if not self.api_enabled or not packet.startswith('T05') or 'thread:' not in packet:
                    return packet
                thread = packet.split('thread:')[1].split(';')[0]
                if self.plain('Hg' + thread) != 'OK':
                    raise RuntimeError('Cannot select native API CPU')
                raw = bytes.fromhex(self.plain('g'))
                regs = struct.unpack_from('<16I', raw)
                pc, sp = regs[15], regs[13]
                if pc not in self.api_points:
                    return packet
                code = self.memory(pc, 4)
                first = int.from_bytes(code[:2], 'little')
                instruction_bytes = 4 if first & 0xf800 in (0xe800, 0xf000, 0xf800) else 2
                record = dict(api=ENTRIES[pc], pc=hex(pc), cpu=thread,
                    arguments=[hex(v) for v in regs[:4]], lr=hex(regs[14]), sp=hex(sp),
                    stack_words=[hex(v) for v in struct.unpack('<32I', self.memory(sp, 128))],
                    first_instruction=code[:instruction_bytes].hex())
                if self.plain(f'z1,{pc:x},2') != 'OK' or self.plain('Hc' + thread) != 'OK':
                    raise RuntimeError('Cannot step native API prologue')
                self.api_points.remove(pc)
                step = self.plain('s')
                if not step.startswith('T05') or self.plain('Hc-1') != 'OK':
                    raise RuntimeError('Unexpected native API prologue step')
                after = bytes.fromhex(self.plain('g'))
                following = struct.unpack_from('<16I', after)
                if following[15] != pc + instruction_bytes:
                    raise RuntimeError('Native API prologue did not execute its original instruction')
                record['native_prologue_next_pc'] = hex(following[15])
                self.api_records.append(record)
                self.api_save()
                if len(self.api_records) == 64:
                    self.api_stop()
                else:
                    if self.plain(f'Z1,{pc:x},2') != 'OK':
                        raise RuntimeError('Cannot restore native API observation')
                    self.api_points.add(pc)
                self.send('c')
    return GraphicsAPIRemote
