# Upside-down photo EXIF orientation — original-Z7 bindings

Status: **works on the camera, November 25, 2026.** In the
[field test](SHUTTER_SOUND_FIELD_TEST.md#camera-result-november-25-2026) the
upside-down photo was saved with EXIF Orientation 3 and a vertical photo with 8,
so the Z7 records pose 3 and no roll-angle fallback is needed for that case.
Now built into the everyday LCD module with shutter sound
([test plan](LCD_EXIF_ORIENTATION_TEST.md)); not yet staged. Thumbnail IFD and
NEF were not checked.

## Problem

Upstream fixed this on the Z7II in `2b596ab` (MIT): photos taken with the camera
upside down are saved with EXIF Orientation 1, so a computer shows them upside
down. The Z7 has the same gap.

Nikon's IFD0 writer table on the Z7 is at `0x11532D94`: 38 entries of
`{type|tag, count, flags, writer}`, the same layout as the Z7II. Entry 9 is
Orientation (`0x0112`, SHORT, count 1) with writer `0x102868D9`:

| Capture pose byte (`capture+0x24FD`) | EXIF Orientation written |
| --- | --- |
| 0 | 1 (normal) |
| 1 | 8 |
| 2 | 6 |
| anything else | 1 |

Two independent pieces of Nikon code suggest 3 means upside down:

- The camera's orientation API `0x101B331B` returns 0 landscape, 1 and 2 for
  the two portrait poses, **3 for inverted landscape**, and 4 when unavailable
  (`PORTRAIT_RESEARCH.md`).
- Nikon's EXIF *reader* (`0x10283AF0`) decodes Orientation 1, 8 and 6 to poses
  0, 1 and 2, and everything else to 4, leaving 3 unused on read.

The capture record's pose is copied from a source structure (`+0x13E8`) in the
capture builder `0x101B8B44` (store at `0x101B8E24`). Whether that byte is 3 for
an upside-down exposure has not been observed; upstream notes that on the Z7II the
discrete pose can stay horizontal while the roll angle shows an inversion. That
is why the field test logs every pose.

## Binding

Nikon's IFD consumer `0x1028BB2C` takes descriptor *n* from the ROM table
`0x11533C14`. Entries 0 and 1 (IFD0) both point to the RAM descriptor
`0xA18D3410`, whose first two words are the getter `0x1028BB5F` (returns the
table) and the count `0x1028BB8B` (returns `0x26`). A read-only RAM search in
assisted QEMU (`tools/probe_z7_ram_pattern.py`) found that pair only at
`0xA18D3410`.

`z7-native-modules/plugins/photo_orientation_exif.h` copies the 38 entries to RAM,
swaps entry 9's writer, and replaces the descriptor's getter word, only while the
descriptor still holds the stock pair, entry 9 matches, and the writer's first
instructions match. Pose 3 writes Orientation 3; every other pose calls Nikon's
writer unchanged.

## Verified

`tools/audit_z7_exif_orientation.py` (12 checks) executes the host loader, the
module, the getter and Nikon's real Orientation writer for poses 0, 1, 2, 4 and
7, which give 1, 8, 6, 1 and 1 as before; pose 3 gives 3. Only the entry's
value field changes, a foreign descriptor is left alone, and a firmware mismatch
fails init. A mutation of the pose constant is caught. The field-test audit
re-checks it in the combined module and checks the pose log.

Not established: that the camera records pose 3 for an upside-down photo, the
thumbnail/second IFD behavior, and NEF. One upside-down photo in the field test
answers the first.

## In-camera playback (traced, not built)

Upstream released inverted playback for the Z7II on November 25 (`94be0b3`,
MIT). It needed three pieces: a lookup that reports a half turn for
upside-down files, a rotation table entry for that half turn, and a graphics
path that draws it. The original-Z7 playback chain was traced on November 25
and checked by `tools/audit_z7_playback_rotation.py` (42 checks), which runs
Nikon's own code in an instruction fixture.

| Step | Original-Z7 code | What it does with an upside-down photo |
| --- | --- | --- |
| Rotation field on the image record | 2-bit field, byte `+0x16` bits 4-5 (`0x103397B0`) | Filled at capture from the pose (1→1, 2→2, else 0) and when a file is indexed from its EXIF Orientation (8→1, 6→2, else 0). Orientation 3 and pose 3 both store 0. |
| Per-image turn lookup | `0x103D4C10`, cache at `0xA18E4DB8` | Maps the field 0→0, 1→1, 2→3, 3→0. Turn 2 (half turn) is never produced. |
| Rotation decision | `0x10306586`, ROM table `0x11545DE4` `{0,0,0,0, 0,1,0,3}`, Rotate tall at `0xA288E248+1` | Indexes the table by Rotate tall and turn. Turn 2 gives 0 in both rows, so even a half-turn lookup would not rotate. |

So, as on the Z7II, upside-down photos play back unrotated even after the EXIF
fix above writes Orientation 3. The EXIF *reader* table noted earlier is a
separate path (it fills the capture structure at `+0x24FD`) and is not what
playback uses.

The lookup and the decision table are in ROM and are called directly (the
decision has 24 direct callers in the playback code), so there is no single RAM
pointer to swap. The playback handlers that reach them are dispatched through a
16-byte-entry table of `{handler, handler, flags, …}` that a read-only
assisted-QEMU RAM search found live at `0xA18E4680` (copied from ROM
`0x11F80894`; one hit in `0xA1800000-0xA1A00000`). A port would copy those
handlers into module memory and redirect their calls, the method the movie
rotation module already uses, so the copies use a lookup that reports turn 2
for Orientation-3 files and a table with a half-turn entry. Upstream also
replaced the graphics worker's half-turn draw to avoid stray edge pixels; the
original Z7 graphics path for a 180° photo is not yet traced.

### Request path and field observer (November 25)

Most of the 24 decision callers put the result in a display request and send
it with `0x103D3854`. That sender copies the rotation (request byte `+0x22`)
through `0x1036048E`, which accepts 0, 1, **2** and 3 and maps anything else to
`0xFFFF`, into the PlaybackProcess request block `0xA289A264` (`+0x28`, with the
image id at `+0`), and posts message `0x04160011` (component `0x0416` is named
"PlaybackProcess" in Nikon's component table) to its queue. So the display
pipeline takes a half-turn code; only the lookup and the decision table never
produce one, as on the Z7II, where upstream's table change alone gave upright
playback before its edge-pixel fix.

The emulator cannot test this: with no card, Play does not enter playback and
no PlaybackProcess message is posted (`tools/probe_z7_message_watch.py`, a
read-only breakpoint/watchpoint run over 90 s after pressing Play). The
[field test](SHUTTER_SOUND_FIELD_TEST.md) therefore carries a read-only
observer (`plugins/playback_observer.h`) that logs the request's image id and
rotation and the lookup cache each time they change. Viewing a tall photo
should show rotation 1 or 3 there; the upside-down photo should show 0. That
confirms the hook point before any module changes playback. No module code
changes playback yet, and nothing here has run on a camera.

Credit: design follows JKWTCN's MIT `photo_rotation.h`; original-Z7 bindings
are independent work.
