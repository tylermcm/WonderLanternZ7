# SPDX-License-Identifier: LicenseRef-Wonder-Lantern-Community
"""Independent end-of-UI-paint spiral experiment, reviewed separately for trials.

The original Z7 dirty-widget walker completes before this callback. No timer,
capture callback, new settings value, workspace or custom flash writer is added.
The separate explicit-draw probe and ordinary grid builds remain unchanged.
"""
from ..assembly import assemble, constant, invoke, jump

SITE = 0x103FCC54


def tail(address):
    return f'.balign 4; ldr.w pc,[pc,#0]; .word {address | 1};'


def configure(plan, follow_display=False):
    im = plan.image
    # Pin the walker, post-paint flag and original visibility query from Z7.
    expected = bytes.fromhex('284698f6e4fd114a00215163')
    if (im.read(SITE, 12) != expected
            or im.words(0x103FCCA0, 1) != (0xA1821370,)
            or im.read(0x103FB7DC, 4) != bytes.fromhex('38f09abf')):
        raise ValueError('Unexpected original Z7 UI paint/visibility boundary')
    helper = plan.alloc(bytes(160))
    wrapper = plan.alloc(bytes(192))
    c, call = constant, invoke
    draw = int(plan.features['spiral_probe']['draw'], 16)
    display_gate = ('cmp r0,#1; beq accepted; cmp r0,#4; bne refused; accepted:'
                    if follow_display else 'cmp r0,#1; bne refused;')
    plan.put(helper, assemble(f'''
        push {{r4,lr}};
        {c('r0', 0xA24F182C)} ldr r0,[r0]; cmp r0,#3; bne refused;
        {c('r0', 0xA1829E40)} ldr r0,[r0,#4]; {display_gate}
        movs r1,#4; {call(0x103FB7DC)} cmp r0,#0; beq refused;
        {call(draw)} pop {{r4,pc}};
        refused: movs r0,#0; pop {{r4,pc}};
    ''', helper, 160))
    plan.put(wrapper, assemble(f'''
        mov r0,r5; {call(0x10295822)}
        push.w {{r0-r3,r12,lr}}; mrs r0,apsr; push {{r0,r1}};
        {call(helper)}
        pop {{r0,r1}}; msr APSR_nzcvq,r0; pop.w {{r0-r3,r12,lr}};
        {c('r2', 0xA1821370)} movs r1,#0; str r1,[r2,#0x34];
        {tail(0x103FCC60)}
    ''', wrapper, 192))
    plan.edit(SITE, jump(SITE, wrapper, 12),
              'Experimental spiral after original Z7 dirty-widget paint walker', expected)
    plan.features['spiral_lifecycle'] = dict(
        helper=hex(helper), wrapper=hex(wrapper), site=hex(SITE),
        original_paint_walker='0x10295822', native_grid_visibility='0x103FB7DC',
        display_grid_id=1, grid_property_value=3, owned_workspace=False,
        automatic_draw_hook=True, cleanup_hook=False, camera_verified=False,
        limitations=['Prototype attaches to original UI paint completion only.',
                     'No separate spiral menu choice or direct live-view erase hook.',
                     'LCD-only guarded surface; EVF/crop/DISP/concurrency/cost unverified.',
                     'Native PNG allocation/assertion behavior is unchanged.'])
    if follow_display:
        plan.features['spiral_lifecycle'].update(display_grid_ids=[1, 4],
            display_grid_id=None,
            limitations=['Active native LCD/EVF UI surface selected after original paint walk.',
                         'No separate spiral menu choice or direct erase hook.',
                         'Physical EVF, crop/DISP/concurrency and cost remain unverified.'])
