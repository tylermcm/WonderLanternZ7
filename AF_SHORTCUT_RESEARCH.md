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

## Required remaining work

Identify native AF-area meanings, availability rules, five physical button
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
