# Upside-down photo EXIF orientation — original-Z7 bindings

Status: **built and verified offline, November 25, 2026.** Included in the
[shutter-sound field test](SHUTTER_SOUND_FIELD_TEST.md) so one camera session
measures it. Not yet in the LCD release module.

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

## In-camera playback (not started)

Upstream also rotates upside-down photos in playback. On the Z7, Nikon's EXIF
*reader* table for IFD0 is at `0x11531BB8` (7 entries of `{tag word, reader}`);
its Orientation reader `0x10283AF1` maps 1/8/6 to poses 0/1/2 and anything else,
including 3, to 4 ("unknown"). The table address comes from a switch at
`0x102836EC` that returns ROM addresses, and no literal or direct branch to that
switch was found, and a read-only RAM search in assisted QEMU found no pointer
to it either, so there is no RAM descriptor to swap as on the writer side. Whether Nikon's playback renderer can show a 180° rotation at all is also
unknown. Both need tracing before a playback change is designed.

Credit: design follows JKWTCN's MIT `photo_rotation.h`; original-Z7 bindings
are independent work.
