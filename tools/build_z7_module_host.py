"""Build an original-Z7 SD module host experiment in a new private directory.

SPDX-License-Identifier: MIT. Independent emulator-only research. No update
container, card staging, installation clearance or physical camera operation.
"""
import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'z7-firmware-extensions/src'))
from z30_extensions.assembly import assemble, constant, invoke, jump
from z30_extensions.container import extract_eg, Z7_CONTAINER_SHA256
from z30_extensions.plan import Plan
from z30_extensions.platform import z7_380 as platform

COMPONENT = ROOT / 'z7-native-modules'
STATE, STATE_BYTES, MAGIC = 0xa9700000, 256, 0x5a37484d
CURSOR, HEAP_SITE, AUTOOP_BINDING = 0xa18fd738, 0x101e3da0, 0xa1822db0
HEAP_EXPECTED = bytes.fromhex('504933480860bde8104005e7')
ZIG = ROOT / '.private/toolchain/zig-x86_64-windows-0.15.2/zig.exe'
PRESET = 'sd-module-host-emulator-only'
DISPLAY_PRESET = 'sd-display-host-emulator-only'


def add_display_hooks(plan, symbols):
    """Thin stock-fallback bridges; module callbacks are staged by the C host."""
    helpers = {name: plan.alloc(bytes(size)) for name, size in
               dict(grid_source=128, grid_geometry=192, scalar_original=64,
                    scalar=224, histogram=192, widget=160, before_paint=192, after_paint=192, before_update=192,
                    disp_cycle=224, information_cycle=256).items()}
    c, call = constant, invoke
    tail = lambda address: f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'
    code = {}
    code['grid_source'] = f'''
        push.w {{r1-r4,r12,lr}}; {call(symbols['z7_display_grid_source'])}
        pop.w {{r1-r4,r12,lr}}; add.w r7,r0,r6,lsl #5;
        ldrh r0,[r7,#10]; mov r9,r0; adds r0,#1; {tail(0x10376e9c)}
    '''
    code['grid_geometry'] = f'''
        push.w {{r0-r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {call(symbols['z7_display_grid_geometry'])}
        pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r12,lr}};
        ldrb.w r0,[sp,#0x28]; cmp r0,#0; bne finished;
        movs r1,#0; movs r0,#0x33; {call(0x103ea7b6)}
        finished: {tail(0x10376f8a)}
    '''
    code['scalar_original'] = f'push {{r3-r5,lr}}; mov r4,r1; movs r1,#0; str r1,[r4]; {tail(0x1007023c)}'
    code['scalar'] = f'''
        push {{r4-r8,lr}}; mov r4,r0; mov r5,r1; {call(helpers['scalar_original'])}
        mrs r7,apsr; push.w {{r0-r3,r12,lr}}; cmp r0,#1; bne done;
        mov r0,r4; ldr r1,[r5]; {call(symbols['z7_display_scalar'])} str r0,[r5];
        done: pop.w {{r0-r3,r12,lr}}; msr APSR_nzcvq,r7; pop {{r4-r8,pc}};
    '''
    for name, prologue, yes, no in (('histogram', True, 0x103ebb7a, 0x103ebba0),
                                     ('widget', False, 0x1036d594, 0x1036d59c)):
        begin = f'{c("r0", 0xa201d4d0)} push {{r4,lr}}; movs r4,#0;' if prologue else ''
        code[name] = f'''
            {begin} ldrb.w r0,[r0,#0x18a]; push.w {{r0-r3,r12,lr}};
            {call(symbols['z7_display_histogram_gate'])} cmp r0,#0; beq rejected;
            pop.w {{r0-r3,r12,lr}}; cmp r0,#2; {tail(yes)}
            rejected: pop.w {{r0-r3,r12,lr}}; cmp r0,#2; {tail(no)}
        '''
    preserve = lambda function: f'''
        push.w {{r0-r3,r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {call(function)} pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r3,r12,lr}};
    '''
    code['before_paint'] = f'''
        push {{r4-r6,lr}}; mov r4,r1; mov r5,r0;
        movw r0,#0x2710; {call(0x103fa97c)}
        {preserve(symbols['z7_display_before_paint'])} mov r1,r4; {tail(0x103fcc54)}
    '''
    code['after_paint'] = f'''
        mov r0,r5; {call(0x10295822)}
        {preserve(symbols['z7_display_after_paint'])}
        {c('r2', 0xa1821370)} movs r1,#0; str r1,[r2,#0x34]; {tail(0x103fcc60)}
    '''
    code['before_update'] = f'''
        push {{r4,lr}};
        {preserve(symbols['z7_display_before_update'])}
        bl original_first; bl original_second; {tail(0x1036ae4e)}
        original_first: {tail(0x1036ad1a)}
        original_second: {tail(0x1036a83a)}
    '''
    code['disp_cycle'] = f'''
        push.w {{r0-r3,r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {call(symbols['z7_display_disp_cycle'])} cmp r0,#0; beq native_cycle;
        str r0,[sp,#8]; pop {{r0,r1}}; msr APSR_nzcvq,r0;
        pop.w {{r0-r3,r12,lr}}; bx lr;
        native_cycle: pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r3,r12,lr}};
        {c('r0', 0xa201d4d0)} movw r1,#0x138d; push {{r4-r6,lr}};
        {c('r5', 0x1064db04)} {tail(0x10370626)}
    '''
    code['information_cycle'] = f'''
        push.w {{r0-r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {call(symbols['z7_display_information_cycle'])} cmp r0,#0; beq information_native;
        pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r12,lr}};
        {tail(0x102fd9b4)}
        information_native: pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r12,lr}};
        bl information_first; cbnz r0,information_busy;
        bl information_monitor; cmp r0,#3;
        {c('lr', 0x102fd7e5)} {tail(0x102fd7e6)}
        information_busy: {c('lr', 0x102fd7df)} {tail(0x102fd7e8)}
        information_first: {tail(0x1040a4ae)}
        information_monitor: {tail(0x103fec18)}
    '''
    sizes = dict(grid_source=128, grid_geometry=192, scalar_original=64, scalar=224,
                 histogram=192, widget=160, before_paint=192, after_paint=192, before_update=192,
                 disp_cycle=224, information_cycle=256)
    for name, text in code.items():
        plan.put(helpers[name], assemble(text, helpers[name], sizes[name]))
    for site, name, expected in (
        (0x10376e90, 'grid_source', 'f74800eb461778898146401c'),
        (0x10376f7a, 'grid_geometry', '9df82800002803d10021332073f016fc'),
        (0x10070234, 'scalar', '38b50c4600212160'),
        (0x103ebb6c, 'histogram', '2e4810b5002490f88a01022812d1'),
        (0x1036d58c, 'widget', '90f88a01022803d1'),
        (0x103fcc44, 'before_paint', '70b50c46054642f21070fdf795fe2146'),
        (0x103fcc54, 'after_paint', '284698f6e4fd114a00215163'),
        (0x1036ae44, 'before_update', '10b5fff768fffff7f6fc'),
        (0x1037061c, 'disp_cycle', '674841f28d3170b5644d'),
        (0x102fd7da, 'information_cycle', '0cf168fe18b901f11afa0328')):
        window = bytes.fromhex(expected)
        plan.edit(site, jump(site, helpers[name], len(window)),
                  'Module-owned display bridge: ' + name, expected=window)
    # Original shooting-app key, event and periodic GUI-update bindings. Only
    # the update initializer word changes; the original update body stays native.
    if plan.image.words(0xa1829b0c, 3) != (0x1030da57, 0x1030dd1f, 0x1030db43):
        raise ValueError('Unexpected original shooting-app callback table')
    plan.edit(0xa1829b14, struct.pack('<I', symbols['z7_gui_update_bridge']),
              'Run an optional owned callback after the original shooting GUI update',
              expected=struct.pack('<I', 0x1030db43))
    helpers['gui_update'] = symbols['z7_gui_update_bridge'] & ~1
    if plan.image.words(0xa182d180, 3) != (0x102fd647, 0x102fdaef, 0x102fda09):
        raise ValueError('Unexpected original information-app callback table')
    plan.edit(0xa182d188, struct.pack('<I', symbols['z7_information_update_bridge']),
              'Run an optional owned callback before the original information update',
              expected=struct.pack('<I', 0x102fda09))
    helpers['information_update'] = symbols['z7_information_update_bridge'] & ~1
    return helpers


def sha(data):
    return hashlib.sha256(data).hexdigest()


def add_highlight_hooks(plan, symbols, owned_frame_coordination_hooks=False):
    """Whole-function bridges with exact native fallback and owned-only cancel."""
    helpers = {name: plan.alloc(bytes(size)) for name, size in
               dict(highlight_source_original=64, highlight_consumer_original=64,
                    highlight_source=384, highlight_consumer=512).items()}
    tail = lambda address: f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'
    save = 'push.w {r0-r3,r12,lr}; mrs r0,apsr; push {r0,r1};'
    restore = 'pop {r0,r1}; msr APSR_nzcvq,r0; pop.w {r0-r3,r12,lr};'
    lane_enter = (f"mov r0,r4; {invoke(symbols['z7_owned_parameter_enter'])} mov r7,r0;"
                  if owned_frame_coordination_hooks else '')
    lane_cancel = ('cmn r7,#1; bne lane_admitted; cmp r6,#1; bne lane_admitted; movs r6,#2; lane_admitted:'
                   if owned_frame_coordination_hooks else '')
    lane_leave = (f"mov r0,r4; mov r1,r7; {invoke(symbols['z7_owned_parameter_leave'])}"
                  if owned_frame_coordination_hooks else '')
    plan.put(helpers['highlight_source_original'], assemble(f'''
        push {{r4-r6,lr}}; mov r5,r1; mov.w r4,#0;
        cbz r0,zero_output; {tail(0x10348678)}
        zero_output: {tail(0x10348686)}
    ''', helpers['highlight_source_original'], 64))
    plan.put(helpers['highlight_consumer_original'], assemble(f'''
        push {{r1-r5,lr}}; movs r4,r0; mov.w r2,#5; {tail(0x10239848)}
    ''', helpers['highlight_consumer_original'], 64))
    plan.put(helpers['highlight_source'], assemble(f'''
        push.w {{r4-r8,lr}}; mov r4,r0; mov r5,r1;
        {save} mov r0,r4; mov r1,r5; {invoke(symbols['z7_highlight_source_enter'])}
        mov r6,r0; cmp r1,#0; beq fallback;
        {restore} bl native_source;
        {save} mov r0,r4; mov r1,r5; mov r2,r6;
        {invoke(symbols['z7_highlight_source_leave'])}
        {restore} pop.w {{r4-r8,pc}};
        fallback: {restore} pop.w {{r4-r8,lr}};
        native_source: {tail(helpers['highlight_source_original'])}
    ''', helpers['highlight_source'], 384))
    plan.put(helpers['highlight_consumer'], assemble(f'''
        push.w {{r4-r8,lr}}; mov r4,r0;
        {save} {lane_enter} mov r0,r4; {invoke(symbols['z7_highlight_consumer_enter'])}
        mov r6,r0; {lane_cancel} cmp r6,#0; beq fallback;
        cmp r6,#1; beq consume; cmp r6,#2; beq cancel;
        {lane_leave} {restore} mov.w r0,#0; pop.w {{r4-r8,pc}};
        consume: {restore} bl native_consumer; b completed;
        cancel: {restore} mov r0,r4; movs r1,#0;
        {invoke(0x102396c0)} mov.w r0,#0;
        completed: {save} mov r0,r4; mov r1,r6;
        {invoke(symbols['z7_highlight_consumer_leave'])}
        {lane_leave}
        {restore} pop.w {{r4-r8,pc}};
        fallback: {lane_leave} {restore} pop.w {{r4-r8,lr}};
        native_consumer: {tail(helpers['highlight_consumer_original'])}
    ''', helpers['highlight_consumer'], 512))
    for site, name, expected in (
        (0x1034866e, 'highlight_source', '70b50d464ff0000430b1'),
        (0x10239840, 'highlight_consumer', '3eb504004ff00502')):
        window = bytes.fromhex(expected)
        plan.edit(site, jump(site, helpers[name], len(window)),
                  'Resident highlight bridge: ' + name, expected=window)
    return helpers


def add_frame_permission_hook(plan, symbols):
    """Filter the consumed permission without changing stored pending frames."""
    address = plan.alloc(bytes(192))
    code = f'''
        push.w {{r0-r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        mov r0,r5; ldr r1,[r4,#0x30];
        {invoke(symbols['z7_primary_frame_permission'])}
        str r0,[sp,#8]; pop {{r0,r1}}; msr APSR_nzcvq,r0;
        pop.w {{r0-r12,lr}};
        ldr r1,[r6,#0x20]; str r0,[r1,#0x20]; ldrb r0,[r4,#1];
        .balign 4; ldr.w pc,[pc,#0]; .word 0x1023bab9;
    '''
    plan.put(address, assemble(code, address, 192))
    plan.edit(0x1023bab0, jump(0x1023bab0, address, 8),
              'Optional primary frame permission consumption filter', expected=bytes.fromhex('316a206b08626078'))
    return dict(primary_frame_permission=address)


def add_cached_frame_hooks(plan, symbols):
    """Filter both fresh cached metadata and NULL cached-state gate refresh."""
    helpers = {n: plan.alloc(bytes(192)) for n in ('cached_frame_input', 'cached_frame_gate')}
    save = 'push.w {r0-r12,lr}; mrs r0,apsr; push {r0,r1};'
    restore = 'pop {r0,r1}; msr APSR_nzcvq,r0; pop.w {r0-r12,lr};'
    tail = lambda p: f'.balign 4; ldr.w pc,[pc,#0]; .word {p | 1};'
    plan.put(helpers['cached_frame_input'], assemble(f'''
        {save} mov r0,r4; ldr r1,[r4,#0x30];
        {invoke(symbols['z7_cached_frame_permission'])} str r0,[sp,#12]; {restore}
        ldr r0,[r5,#0x20]; str r1,[r0,#0x20]; ldrb.w r1,[r0,#0x250];
        {tail(0x1023d834)}
    ''', helpers['cached_frame_input'], 192))
    plan.put(helpers['cached_frame_gate'], assemble(f'''
        {save} ldr r1,[r5,#0x20]; ldr r1,[r1,#0x20]; movs r0,#0;
        {invoke(symbols['z7_cached_frame_permission'])}
        ldr r1,[r5,#0x20]; str r0,[r1,#0x20]; {restore}
        ldr r0,[r5,#0x20]; ldrb.w r0,[r0,#0x250];
        bl native_gate; {constant('lr', 0x1023d895)} {tail(0x1023d894)}
        native_gate: {tail(0x1023b76e)}
    ''', helpers['cached_frame_gate'], 192))
    for site, name, expected in ((0x1023d82a, 'cached_frame_input', '286a216b016290f85012'),
                                  (0x1023d88a, 'cached_frame_gate', '286a90f85002fdf76dff')):
        plan.edit(site, jump(site, helpers[name], 10), 'Optional cached primary permission: ' + name,
                  expected=bytes.fromhex(expected))
    return helpers


def add_owned_frame_coordination_hooks(plan, symbols):
    """Nonblocking whole primary-frame bodies versus owned consumer work.

    Foreign parameter requests and indirect native gate callers remain open.
    The original frame may wait on Nikon's mutex; owned work never waits for it.
    """
    tail = lambda p: f'.balign 4; ldr.w pc,[pc,#0]; .word {p | 1};'
    save = 'push.w {r0-r3,r12,lr}; mrs r0,apsr; push {r0,r1};'
    restore = 'pop {r0,r1}; msr APSR_nzcvq,r0; pop.w {r0-r3,r12,lr};'
    helpers = {}
    for name, site, expected, native in (
            ('primary', 0x1023b9d0, '2de9fc41664e0546',
             f"push.w {{r2-r8,lr}}; {constant('r6', 0xa180a568)} mov r5,r0; {tail(0x1023b9d8)}"),
            ('cached', 0x1023d794, '7cb5754d04000e46',
             f"push {{r2-r6,lr}}; {constant('r5', 0xa180a5a0)} movs r4,r0; mov r6,r1; {tail(0x1023d79c)}")):
        original, bridge = plan.alloc(bytes(64)), plan.alloc(bytes(384))
        plan.put(original, assemble(native, original, 64))
        code = f'''
            push.w {{r4-r8,lr}}; mov r5,sp;
            {save} mov r0,r5; {invoke(symbols['z7_owned_frame_enter'])}
            mov r4,r0; cmp r4,#0; beq fallback; cmn r4,#1; beq busy;
            {restore} bl native_body;
            {save} mov r0,r5; mov r1,r4; {invoke(symbols['z7_owned_frame_leave'])}
            {restore} pop.w {{r4-r8,pc}};
            busy: {restore} mov.w r0,#0; pop.w {{r4-r8,pc}};
            fallback: {restore} pop.w {{r4-r8,lr}};
            native_body: {tail(original)}
        '''
        plan.put(bridge, assemble(code, bridge, 384))
        plan.edit(site, jump(site, bridge, 8), 'Owned parameter coordination: ' + name,
                  expected=bytes.fromhex(expected))
        helpers[name], helpers[name + '_original'] = bridge, original
    return helpers


def compile_host(base, zig=ZIG, highlight_hooks=False, parameter_hooks=False, frame_permission_hooks=False, cached_frame_permission_hooks=False, owned_frame_coordination_hooks=False):
    """Fixed-address, BSS-free host; all writable state is explicitly reserved."""
    temporary = ROOT / '.private/tmp'
    temporary.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment['ZIG_GLOBAL_CACHE_DIR'] = str(ROOT / '.private/toolchain/zig-cache')
    environment['ZIG_LOCAL_CACHE_DIR'] = str(ROOT / '.private/tmp/zig-cache')
    with tempfile.TemporaryDirectory(prefix='z7-module-host-', dir=temporary) as directory:
        folder = Path(directory)
        objects = []
        for index, source in enumerate(('module.c', 'z7_380.c')):
            obj = folder / f'{index}.o'
            subprocess.run([str(zig), 'cc', '-target', 'thumb-freestanding-eabi', '-mcpu=cortex_a9',
                '-mfloat-abi=soft', '-Os', '-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
                '-fno-asynchronous-unwind-tables', '-fno-stack-protector', '-Wall', '-Wextra', '-Werror',
                '-I', str(COMPONENT / 'sdk'), '-I', str(COMPONENT / 'host'),
                *(['-DZ7_HOST_HIGHLIGHTS=1'] if highlight_hooks else []),
                *(['-DZ7_HOST_PARAMETERS=1'] if parameter_hooks else []),
                *(['-DZ7_HOST_FRAME_PERMISSION=1'] if frame_permission_hooks else []),
                *(['-DZ7_HOST_CACHED_FRAME=1'] if cached_frame_permission_hooks else []),
                *(['-DZ7_HOST_OWNED_FRAME_COORDINATION=1'] if owned_frame_coordination_hooks else []),
                '-c', str(COMPONENT / 'host' / source), '-o', str(obj)], check=True, env=environment)
            objects.append(str(obj))
        linker = folder / 'host.ld'
        linker.write_text(f'''ENTRY(z7_autoop_init)
SECTIONS {{
 . = {base};
 .host : {{ *(.text .text.*) *(.rodata .rodata.*) *(.data .data.*) }}
 .bss (NOLOAD) : {{ *(.bss .bss.*) *(COMMON) }}
 /DISCARD/ : {{ *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) }}
}}
ASSERT(SIZEOF(.bss) == 0, "Host must not contain unreserved BSS");
''', encoding='utf-8')
        elf = folder / 'host.elf'
        subprocess.run([str(zig), 'ld.lld', '-T', str(linker), '--no-undefined',
                        *objects, '-o', str(elf)], check=True, env=environment)
        data = elf.read_bytes()
    shoff = struct.unpack_from('<I', data, 32)[0]
    stride, count = struct.unpack_from('<HH', data, 46)
    if stride != 40:
        raise ValueError('Unexpected host ELF')
    sections = [struct.unpack_from('<10I', data, shoff + i * stride) for i in range(count)]
    allocated = [s for s in sections if s[2] & 2 and s[5]]
    if len(allocated) != 1 or allocated[0][1] != 1 or allocated[0][3] != base:
        raise ValueError('Host must have exactly one allocated fixed-address image')
    section = allocated[0]
    code = data[section[4]:section[4] + section[5]]
    if not 0 < len(code) < 16384:
        raise ValueError('Unexpected host image size')
    symbols = {}
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        names = data[strings[4]:strings[4] + strings[5]]
        for offset in range(section[4], section[4] + section[5], 16):
            name, value, _, _, _, index = struct.unpack_from('<IIIBBH', data, offset)
            label = names[name:].split(b'\0', 1)[0].decode()
            if label and index == 0:
                raise ValueError('Unresolved host symbol: ' + label)
            if label.startswith('z7_'):
                symbols[label] = value
    return code, symbols


def build_image(container, zig=ZIG, display_hooks=False, highlight_hooks=False, parameter_hooks=False, frame_permission_hooks=False, cached_frame_permission_hooks=False, owned_frame_coordination_hooks=False):
    if highlight_hooks and not display_hooks:
        raise ValueError('Highlight host requires the display host profile')
    if parameter_hooks and not highlight_hooks:
        raise ValueError('Parameter host requires the highlight host profile')
    if frame_permission_hooks and not parameter_hooks:
        raise ValueError('Frame permission host requires the parameter host profile')
    if cached_frame_permission_hooks and not frame_permission_hooks:
        raise ValueError('Cached frame host requires the primary frame host profile')
    if owned_frame_coordination_hooks and not cached_frame_permission_hooks:
        raise ValueError('Owned frame coordination requires cached frame hooks')
    state_bytes = 324 if owned_frame_coordination_hooks else 304 if cached_frame_permission_hooks else 288 if frame_permission_hooks else 272 if parameter_hooks else STATE_BYTES
    workspace_bytes = (state_bytes + 63) & ~63
    if sha(container) != Z7_CONTAINER_SHA256:
        raise ValueError('Requires exact original Z7 C 3.80 container')
    plan = Plan(extract_eg(container), platform)
    # Original AUTOOP callback binding and original APPIDLE task descriptor.
    if plan.image.words(AUTOOP_BINDING, 1) != (0x102697f5,):
        raise ValueError('Unexpected original AUTOOP callback')
    descriptor = plan.image.read(0x11f9a92c, 28)
    if struct.unpack_from('<4I', descriptor) != (1, 28, 8192, 0) or descriptor[16:24] != b'APPIDLE\0':
        raise ValueError('Unexpected native task descriptor')
    if plan.image.words(0x101e3ee4, 1) != (CURSOR,) or plan.image.words(0x101e3e70, 1) != (STATE,):
        raise ValueError('Unexpected native workspace')
    code, symbols = compile_host(plan.address, zig, highlight_hooks, parameter_hooks, frame_permission_hooks, cached_frame_permission_hooks, owned_frame_coordination_hooks)
    host_address = plan.alloc(code)
    cold_size = 192 if owned_frame_coordination_hooks else 160
    cold_address = plan.alloc(bytes(cold_size))
    # Preserve original initializer's stack unwind and tail continuation. R0
    # still reports the original workspace base; only the monotonic cursor moves.
    cold = f'''push {{r2,r3}}; mrs r2,apsr; push {{r2,r3}};
        {constant('r0', STATE)} mov r2,r0; movs r3,#0; movs r1,#{state_bytes // 4};
        clear: str r3,[r2],#4; subs r1,#1; bne clear;
        {constant('r2', STATE + 240)} {constant('r3', 0xa5a5a5a5)}
        str r3,[r2]; str r3,[r2,#4]; str r3,[r2,#8]; str r3,[r2,#12];
        {(constant('r2', STATE + 264) + ' str r3,[r2]; str r3,[r2,#4];') if parameter_hooks else ''}
        {(constant('r2', STATE + 280) + ' str r3,[r2]; str r3,[r2,#4];') if frame_permission_hooks else ''}
        {(constant('r2', STATE + 296) + ' str r3,[r2]; str r3,[r2,#4];') if cached_frame_permission_hooks else ''}
        {(constant('r2', STATE + 316) + ' str r3,[r2]; str r3,[r2,#4];') if owned_frame_coordination_hooks else ''}
        {constant('r2', STATE + 32)} {constant('r3', MAGIC)} str r3,[r2];
        dmb sy; pop {{r2,r3}}; msr APSR_nzcvq,r2; pop {{r2,r3}};
        {constant('r1', CURSOR)} {constant('r0', STATE + workspace_bytes)} str r0,[r1];
        {constant('r0', STATE)} pop.w {{r4,lr}};
        .balign 4; ldr.w pc,[pc,#0]; .word {0x101e3bb9};
    '''
    plan.put(cold_address, assemble(cold, cold_address, cold_size))
    plan.edit(HEAP_SITE, jump(HEAP_SITE, cold_address, 12),
              'Reserve isolated module host state before native workspace allocations', expected=HEAP_EXPECTED)
    plan.edit(AUTOOP_BINDING, struct.pack('<I', symbols['z7_autoop_init']),
              'Call original AUTOOP initializer before scheduling the isolated module loader',
              expected=struct.pack('<I', 0x102697f5))
    display_bridges = add_display_hooks(plan, symbols) if display_hooks else {}
    highlight_bridges = add_highlight_hooks(plan, symbols, owned_frame_coordination_hooks) if highlight_hooks else {}
    frame_permission_bridges = add_frame_permission_hook(plan, symbols) if frame_permission_hooks else {}
    cached_frame_bridges = add_cached_frame_hooks(plan, symbols) if cached_frame_permission_hooks else {}
    owned_frame_bridges = add_owned_frame_coordination_hooks(plan, symbols) if owned_frame_coordination_hooks else {}
    output, report = plan.finish()
    report.update(preset=DISPLAY_PRESET if display_hooks else PRESET, emulator_only=True, candidate_cleared=False,
        container_sha256=Z7_CONTAINER_SHA256, main_payload_size=len(output) - 2,
        main_payload_sha256=sha(output[:-2]), host_address=hex(host_address),
        host_bytes=len(code), host_sha256=sha(code), symbols=symbols,
        state=hex(STATE), state_bytes=state_bytes, cold=hex(cold_address),
        display_hooks=bool(display_hooks), display_bridges=display_bridges,
        module_path='A:\\Z7APP.BIN', module_target='0x03800007',
        source_files={str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes())
                      for p in sorted([*(COMPONENT / 'host').glob('*'), *(COMPONENT / 'sdk').glob('*')]) if p.is_file()})
    report['limitations'] += ['Boot, filesystem, cache and task contracts need scoped validation; no hardware clearance.',
                             'Separate stock-based no-feature probe; does not include the installed grid trial.']
    if highlight_hooks:
        report.update(highlight_hooks=True, highlight_bridges=highlight_bridges, api_bytes=48)
    if parameter_hooks:
        report.update(parameter_hooks=True, api_bytes=52, workspace_reserved_bytes=workspace_bytes)
    if frame_permission_hooks:
        report.update(frame_permission_hooks=True, api_bytes=56, frame_permission_bridges=frame_permission_bridges)
    if cached_frame_permission_hooks:
        report.update(cached_frame_permission_hooks=True, api_bytes=60, cached_frame_bridges=cached_frame_bridges)
    if owned_frame_coordination_hooks:
        report.update(owned_frame_coordination_hooks=True, api_bytes=64, owned_frame_bridges=owned_frame_bridges)
        report['limitations'] += ['Owned-frame exclusion only; foreign native parameters remain uncoordinated.',
                                  'Lane generation exhaustion refuses admission; diagnostic has no shutdown handling.']
    return output, report


def validate_candidate(path, report_path, stock_path, zig=ZIG):
    actual = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if actual.get('preset') not in (PRESET, DISPLAY_PRESET):
        raise ValueError('Unknown module-host profile')
    expected, report = build_image(Path(stock_path).read_bytes(), zig, actual['preset'] == DISPLAY_PRESET,
                                   actual.get('highlight_hooks', False), actual.get('parameter_hooks', False),
                                   actual.get('frame_permission_hooks', False), actual.get('cached_frame_permission_hooks', False),
                                   actual.get('owned_frame_coordination_hooks', False))
    if (Path(path).read_bytes() != expected[:-2] or actual != report or binascii.crc_hqx(expected, 0)):
        raise ValueError('Module host candidate or report differs from independent rebuild')
    return dict(modified=True, independently_rebuilt=True, sha256=sha(expected[:-2]),
                size=len(expected)-2, preset=report['preset'], camera_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / '.private/stock/Z_7_0380.bin')
    parser.add_argument('--zig', type=Path, default=ZIG)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--display-hooks', action='store_true', help='Install guarded stock-fallback display bridges')
    parser.add_argument('--highlight-hooks', action='store_true', help='Opt in to experimental API48 source/consumer bridges; requires --display-hooks')
    parser.add_argument('--parameter-hooks', action='store_true', help='Opt in to API52 native highlight payload callback; requires --highlight-hooks')
    parser.add_argument('--frame-permission-hooks', action='store_true', help='Opt in to API56 primary frame permission filter; requires --parameter-hooks')
    parser.add_argument('--cached-frame-permission-hooks', action='store_true', help='Opt in to API60 cached primary permission filter; requires --frame-permission-hooks')
    parser.add_argument('--owned-frame-coordination-hooks', action='store_true', help='Opt in to diagnostic API64 owned parameter / primary frame exclusion; requires cached frame hooks')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.private') or output.exists():
        parser.error('Choose a new output directory under .private')
    if args.highlight_hooks and not args.display_hooks:
        parser.error('--highlight-hooks requires --display-hooks')
    if args.parameter_hooks and not args.highlight_hooks:
        parser.error('--parameter-hooks requires --highlight-hooks')
    if args.frame_permission_hooks and not args.parameter_hooks:
        parser.error('--frame-permission-hooks requires --parameter-hooks')
    if args.cached_frame_permission_hooks and not args.frame_permission_hooks:
        parser.error('--cached-frame-permission-hooks requires --frame-permission-hooks')
    if args.owned_frame_coordination_hooks and not args.cached_frame_permission_hooks:
        parser.error('--owned-frame-coordination-hooks requires --cached-frame-permission-hooks')
    eg, report = build_image(args.source.read_bytes(), args.zig.resolve(), args.display_hooks, args.highlight_hooks, args.parameter_hooks, args.frame_permission_hooks, args.cached_frame_permission_hooks, args.owned_frame_coordination_hooks)
    repeated, second = build_image(args.source.read_bytes(), args.zig.resolve(), args.display_hooks, args.highlight_hooks, args.parameter_hooks, args.frame_permission_hooks, args.cached_frame_permission_hooks, args.owned_frame_coordination_hooks)
    if eg != repeated or report != second or binascii.crc_hqx(eg, 0):
        raise RuntimeError('Host build is not deterministic or CRC failed')
    output.mkdir(parents=True)
    (output / 'module-host.emulator.eg.bin').write_bytes(eg)
    (output / 'module-host.emulator.main.bin').write_bytes(eg[:-2])
    (output / 'module-host.emulator.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(main_bytes=len(eg)-2, main_sha256=sha(eg[:-2]),
                         host_bytes=report['host_bytes'], symbols=report['symbols'],
                         reproducible=True, eg_crc_zero=True, emulator_only=True)))


if __name__ == '__main__':
    main()
