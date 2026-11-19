# Original Z7 clean shooting display research

## Scope and result, October 27, 2026

The owner wants only the live image and composition grid, including removal of
the bottom shutter/aperture/ISO/metering/card information. This is separate from
the spiral color/display correction. No clean-display firmware patch or camera
trial has been prepared.

In assisted QEMU, diagnostic changes to the original Z7's shooting-widget
visibility masks remove the top and bottom readouts in simplified DISP mode,
while the live scene and native 3x3 grid remain. Two empty card-count brackets
still appear at bottom right. They survive a native MENU clear and return, so
the result does not yet meet the requested completely clean display.

## Native structures and reversible experiment

The native binding table at `0x1064D610` contains 61 descriptor pointers. The
original walker compares against `0x3D`; these are not inferred from another
model. Each descriptor has nine 32-bit visibility masks at `+4`. Clearing
`0x22222` in each of those masks, then cycling DISP back to mode 1, hides the
ordinary shooting widgets in the assisted LCD fixture. The 2,196 original mask
bytes were saved and restored exactly. A final resumed capture shows normal
readouts again.

These are emulator RAM fixtures, not edits to firmware code, settings storage,
pixel buffers or camera memory. The host supplies diagnostic native calls and
DISP/MENU key inputs. QEMU's camera/controller inputs are assisted, as in the
grid experiments. Generated screenshots, raw structures and logs remain private
under `.private/research/display/20261027-clean-mask-03/`.

Additional negative experiments:

- Zeroing all nine masks does not remove the remaining brackets.
- Original component permission function `0x103FB5BE(1, 0, 0)` returns success,
  but does not maintain the desired hidden UI after normal tasks resume.
- Original bitmap fill `0x103FAE10(buffer, 720, 480, 0)` on native component 0
  (`0xB0B09600`) and component 2 (`0xB0FB9600`) does not remove those brackets
  from the resumed screenshot. These calls do not establish ownership of them.

The next step is to trace the card-count bracket painter and its own visibility
conditions, then design an explicit setting with restoration on DISP/MENU,
playback, warnings, capture and wake. The main UI bitmap also hosts the spiral;
hiding that entire bitmap would hide the curve too. Combining a clean display
with the spiral is not yet tested.

## Card-bracket control flow, November 19, 2026

`tools/audit_z7_card_brackets.py` now executes the original card updater
`0x102F3F8A`, its native control-visibility query `0x102F2F1E`, and shared helper
`0x102F7E24`. Widget16's fifteen controls start at `0xA1824684`. The updater's
ordinary count-text branch depends on active controls, but its tail still enters
the shared bracket helper when the visibility query returns zero. That helper
updates controls4/2 (and3/1 for output0) through original glyph-update wrapper
`0x102F2F80`, whose native body makes the GUI object visible. This explains a
concrete path that survives descriptor-mask exclusion.

Eighteen instruction cases pass. Twelve cover supplied visibility0/1, output0/1/2 and
snapshot exclusion byte `0xA201D4D0+0x192` values0/1. The native exclusion remains
effective. Six further cases execute the original glyph/style wrapper, geometry
copy and native visibility setter using synthetic GUI objects: inactive controls
still make exactly objects1/2/3/4 visible for output0, or2/4 for outputs1/2.
Image/style payload application and count-text helpers are supplied boundaries;
these checks identify control flow and object visibility, not actual clean pixels.
Private result: `.private/evidence/20261119-card-brackets-02.json`. No clean-display module or
camera patch has been enabled. A future callback must suppress the shared path
or hide its owned native objects during the GUI paint phase, with exact native
restoration across DISP/menu/playback and output changes. Mask changes alone
remain insufficient.

## Disabled SD diagnostic

`examples/clean_display_probe.c` includes the combined display module with an
optional pre-paint callback. Its BSS request starts at zero, so startup leaves
the native UI alone. An explicit emulator request saves all61x9 current mask
words and clears only simplified-state bits `0x22222`; LCD-photo/page exclusions
restore owned values. Each word is restored only while it still equals this
diagnostic's masked value, preserving unrelated writes. Four independently
identified bracket objects are hidden with the original native visibility setter
only in simplified mode; their initial visible states are retained for exit.
Object class, painter and native parent are checked before access.

Private probe01 is5,716 bytes, SHA
`aeb6da1b5d8d58f29e031290c26aa57569282a8f6969f67184f61236468a7d70`.
`tools/audit_z7_clean_display.py` passes13 compiled cases: default-off,
exact mask changes/restoration, four native visibility setters, repeat paints,
menu/EVF/movie exclusions, unknown request, a foreign mask write, invalid final
descriptor and foreign bracket painter. GUI objects
and incoming state remain supplied. The existing combined module rebuilds to
the same previously validated SHA. Assisted-QEMU live01 passes six checks across
three frames: explicit request plus native DISP cycling produces only the scene
and golden grid, without the old brackets; all549 native mask words restore on
disable. Clean/restored frames were visually inspected. A separate full RGB
comparison finds the entire restored frame byte-identical to the baseline.
The native scene is an assisted test pattern, not sensor imagery. No camera-side
DISP setting is implemented: native key handler/presets and broader lifetime/output
coverage remain to be implemented.

## Native page selector contract

The earlier live experiment already queried original selector `0x103673AC` and
observed photo LCD property `0x2F15`. New `tools/audit_z7_disp_selector.py` executes
that selector and original setter `0x103673DE`:24 cases pass. Supplied property
`0x138D` zero selects photo properties2F15/2F16; nonzero selects movie2F17/2F18.
Native display-kind getter `0x103FEF80` result1 selects the LCD property; result4
selects the alternate property. Other display-kind semantics are not established.
The setter writes only snapshot `0xA201D4D0+0x18A`, reselects the matching property
and calls original property setter `0x104065B0` with the new page. Values0..4
were exercised with neighboring snapshot bytes unchanged. Display-kind/property
storage are supplied boundaries; this does not establish persistence or every
page's meaning. Private result: `.private/evidence/20261119-disp-selector-01.json`.
Native key callback ownership and its existing admission checks remain to derive.

## Original shooting-key route

Independent Z7 disassembly finds the initialized callback word at RAM
`0xA1829B0C` (scatter source `0x11EC5D20`) pointing to `0x1030DA57`. The outer
callback includes native pre-dispatch admission; its internal dispatcher is
`0x1030D7AC`. Internal key `0x29` reaches native DISP admission `0x103673F6`,
then page cycle `0x1037061C`. Key `0x28` reaches another handler `0x1036763C`.
These are original-Z7 routes, not translations of the pinned Z7II key or slot.

`tools/audit_z7_disp_input.py` passes20 cases. Fourteen run the original internal
dispatcher/admission instructions, with supplied native service results. They
cover admitted cycling, snapshot states2/5/11, native mode/monitor exclusions,
both final exclusions, fallback gate acceptance/rejection, and the distinct28
route. Six further cases execute the outer callback through admitted routing,
its first admission guard, two early key filters, the final key filter and an
inner exclusion, with explicit native service results. The broader service
environment is still supplied. Private input02 is the current instruction result.
A live trace first stopped on a
background key0 event; it is retained as a failed observation, not contrary
proof of the instruction route. The revised probe filters a bounded sequence of
native dispatches without changing the callback. That after-injection experiment
was stopped explicitly after its observation point proved insufficient; input-live02
is retained. Current input-live03 arms instruction traces during the native AO
press and bounded native task delays, so it can also observe another CPU handling
the event before the injection returns. The press remains a supplied diagnostic
input, not physical-button evidence. Input-live03 now passes seven checks across
two frames: AO injection itself captures dispatcher key29, original admission
and original page cycle; the subsequent task-delay call captures background0.
Native mode changes0->1, and callbackA1829B0C remains1030DA57. This confirms that
the first late breakpoint missed the real request because it ran before the AO
injection returned. No pixels/register values were forced to create that route.

Selector audit02 expands to104 checks, adding80 native page-cycle cases over
all five starting pages, supplied photo/movie/output/exposure/eligibility states.
Original instructions retain native histogram-page skips and alternate-output/
movie information-page skips. Photo LCD page4 reaches two native app-transition
calls and returns2; those calls are supplied boundaries, so this is routing
evidence rather than a completed information-app transition. No custom page
handler has yet been installed.

## Display routing relevant to the spiral

Original descriptor getter `0x10433B80(kind, display_id, dataset)` accepts LCD
1, external 2 and EVF 4. Component **1**, dataset 0 is the relevant UI surface:
LCD is 720x480; EVF is 1280x960. The bitmap address is at `+0x24`, packed shape
at `+8`, format selector at `+0x34`. Component 0 is a different 720x480 plane
and cannot be used to infer the main EVF drawing size.

The current LCD registry has a 720x480 entry at `0xB045F200`; the inactive EVF
descriptor uses the same address with a different shape. A display-aware helper
must require an exact existing active registry entry for the selected native
descriptor and size. The new spiral helper refuses a mismatch instead of
assuming the LCD registry is suitable for EVF. Native descriptor inspection and
supplied routing are not evidence of a physical eye-sensor transition or EVF
scanout.
