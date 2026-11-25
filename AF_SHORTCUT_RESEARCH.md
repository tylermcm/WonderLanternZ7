# Original-Z7 AF-area shortcut port

The target is the pinned JKWTCN
[AF-area shortcut feature](https://github.com/JKWTCN/z7ii-extensions/blob/f298964fdf6b0d20df0d3c6cad48a74aa5f5c339/docs/af-area-shortcut.md):
five independently assigned photo buttons, press once to select and retain an
area, native Custom controls integration and saved assignments. This independent
MIT port credits its press-edge capture and GUI-task deferral design to JKWTCN.
It is currently a policy component and binding investigation, **not an integrated
camera feature**. No input callback or AF property writer has been installed.

## Implemented policy component

`z7-native-modules/plugins/af_shortcut_policy.h` keeps five assignments and an
atomic pending-button mask. The input side accepts logical press edges supplied
by a future original-Z7 decoder. The GUI side consumes at most one action:

- All assignments start unassigned. Five buttons and thirteen logical targets
  are representable, including the upstream extended targets.
- Busy rendering defers without consuming the request. Leaving admitted photo
  context cancels it, including while busy.
- Only buttons whose native assignment remains None can act. Native functions
  keep priority; disabled or unavailable targets are skipped.
- Multiple press edges coalesce; the first admitted button wins. Other captured
  bits are consumed, so release or a held state without a new edge does not act.
- Invalid indices/targets are rejected. Corrupt target values cannot produce an
  out-of-range shift or an action.

The returned action contains a logical button and target. There are no AF
property writes, autofocus starts, settings I/O, context queries, raw button
decoding or hook publication in this component. Logical target support does not
establish that the original body supports any corresponding extended AF mode.

Build the private probe with `tools/build_z7_af_shortcut.py --output` and a new
private directory. The reproducible 448-byte probe SHA256 is
`c863f07aa5c99c3d06a7b1e80d834573e545ae89a48e5842c2ace865b504c6a8`.
It must not be staged on a camera. Its initialization only clears its own state.

474 compiled ARM checks cover all five buttons and thirteen logical targets,
busy deferral, context cancellation, one-shot consumption, native-assignment and
availability guards, coalescing, invalid/corrupt values and no GUI publication.
The 103 root tests pass. This does not simulate simultaneous physical task
execution or establish raw press/hold/release decoding.

## Original property lookup investigation

`tools/audit_z7_af_property_bindings.py` executes original C 3.80 group admission,
descriptor lookup and scalar getter instructions. It passes 215 checks with
supplied scalar storage. Native group 5 contains 128 entries: keys `0x058A` and
`0x058B` used for subtypes by the pinned Z7II implementation are rejected by the
original lookup. Reading adjacent descriptor bytes without checking that bound
would identify unrelated properties. A native getter's zero return alone cannot
distinguish an absent property from a present zero-valued property.

The candidate keys `0x056C`, `0x0579`, `0x1145`, `0x114A`, `0x114F`, `0x1153` and
`0x1156` do have scalar descriptors. Their presence **does not establish their
human meaning on the original Z7**. The original paired selector at `0x1033E738`
reads two of these scalars and scans nine rows. Its numeric behavior is checked;
the rows have not been qualified as AF targets. Do not use the Z7II setter enums
or button-assignment property IDs on the original body from this evidence.

Private native-menu observations use an isolated stock QEMU guest and original
key paths. These are baseline UI observations, not a modified shortcut menu or
hardware proof. Firmware, property snapshots and screenshots remain private.

## AF-area mode and focus mode, measured in Nikon's menu (November 25, 2026)

Read-only walks of Nikon's own Photo shooting menu in assisted QEMU
(`tools/probe_z7_menu_walk.py`) pressed the original key events, confirmed one
AF-area mode at a time, and diffed the property RAM after each confirmation. Each
confirmation changed exactly one word, `0xA24E33F8`; Nikon's scalar getter
`0x104065A4` maps property **`0x568`** (and no other key in `0x540`–`0x59F`) to it.
Focus mode is property **`0x567`** (`0xA24E33F4`, mirrored at `0xA24F7C04`).

| `0x568` value | Photo AF-area mode | Availability seen in the menu |
| --- | --- | --- |
| 0 | Pinpoint AF | Greyed in AF-C |
| 1 | Single-point AF | Always |
| 2 | Dynamic-area AF | Greyed in AF-S |
| 3 | Wide-area AF (S) | Always |
| 4 | Wide-area AF (L) | Always |
| 6 | Auto-area AF | Always |

| `0x567` value | Focus mode |
| --- | --- |
| 1 | AF-S |
| 2 | AF-C |

The values match the area numbers in upstream's Z7II shortcut table
(`0,1,2,3,4,…,6`), so the shortcut's targets can use the same area numbers on
the Z7, written through property `0x568`. Upstream's subtype keys `0x058A`/`0x058B`
stay outside the Z7's group, as found earlier, and the Z7 menu lists no custom wide-area modes.
`tools/audit_z7_af_area_property.py` (24 checks) re-checks the getter mapping and
the recorded walks, including every screenshot hash. Manual focus, the
`0x56C`/`0x579` selector rows, the setter path and movie-mode AF are still open.

## Setter path (November 25, 2026)

Nikon's property setter `0x104065B0` (→ `0x101D61EE`) takes a lock, stores the
value, and sends change notifications. In assisted QEMU, calling it in the paused
GUI task with `0x568` = 3, 2, 5 and then 4 returned success each time and stored
each value, including Dynamic-area while in AF-S and the nonexistent 5. Opening
Nikon's AF-area menu afterwards showed Wide-area AF (L) selected, so menu state
follows the setter. Because the setter validates nothing,
`z7-native-modules/plugins/af_area_native.h` enforces the menu's rules first:
known values only, Pinpoint only in AF-S, Dynamic-area only in AF-C, nothing in
any focus mode not yet measured (including manual focus), no write when the mode
is already selected, and a readback after each write.
`tools/audit_z7_af_area_apply.py` (22 checks) runs it with Nikon's real getter
and a recorded setter, and re-checks the QEMU setter run.

## Button input (November 25, 2026)

Nikon's `ID_SW` name table names each switch with its word and mask, and the
AutoOperation table at `0x10634144` maps test-key indices to the same pairs.
`0x101B4A60` returns the switch object `0xA1F90AA0`; Nikon's edge routine
`0x101AE622` keeps one 0x14-byte group per word (+0 current, +4 previous, +8
changed, +0xC pressed, +0x10 released). Groups: SW0 `0xA1F90AA4`, SW1 `0xA1F90AB8`,
SW2 `0xA1F90ACC`.

| Button | Word / mask | AO index | Pressed in assisted QEMU (`tools/probe_z7_switch_watch.py`) |
| --- | --- | --- | --- |
| Fn1 | SW0 `0x4000` | 59 | Set while held, cleared on release (writer `0x101AE622`) |
| AF-ON | SW0 `0x200000` | 27 | Set while held, cleared on release |
| Sub-selector center | SW2 `0x8000` | 51 | Set while held |
| Fn2 | SW2 `0x4000` | 60 | No change observed |
| Movie record | SW1 `0x2000` | 9 | No change observed |

`z7-native-modules/plugins/af_shortcut_runtime.h` polls the three verified buttons
once per GUI update, turns presses into edges, feeds `af_shortcut_policy.h`, and
applies the target with `af_area_native.h`. Z7 targets are the six measured
AF-area modes (target = value + 1). `tools/audit_z7_af_shortcut_runtime.py`
(25 checks) covers press, hold, release, already-selected, busy deferral,
photo-context drop, native-None exclusion, availability by focus mode, the
unverified buttons being ignored, and non-Z7 targets. Polling can miss a press
shorter than one GUI update; that is measured on the camera.

## Required remaining work

Native AF-area values and the setter path are now measured (above). Identify
the remaining availability rules (manual focus, movie mode), Fn2 and movie-button
input (three of five buttons verified above), physical button
events and native assignments through the original menus and input paths. Then
connect GUI-side writes with readback and exclusion rules for menus, playback,
information display, magnified view, movie mode, LCD and EVF. The existing
direction-only navigation API is not a substitute for raw five-button input.

Port the native f2 assignment list, overview names/icons, submenus/help,
confirmation/cancellation and native None behavior, preserving original controls.
Persist assignments without overwriting earlier display/highlight journals.
Custom C1/C2 and subject tracking need their own original-Z7 implementations and
availability gates. Finish cumulative integration, visible UI checks, lifecycle
and hardware verification before claiming feature parity. No camera installation
or recovery assessment is supplied by this checkpoint.
