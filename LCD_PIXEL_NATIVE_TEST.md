# Original-Z7 pixel-shift native-menu continuation

November 27, 2026. **Offline candidate, not installed or camera-tested. Native
feature parity is unfinished.** Independent original-Z7 C 3.80 work. This
supersedes the behavior described in [the earlier Nikon-style
assessment](LCD_PIXEL_NIKON_MENU_TEST.md); that frozen assessment is retained.

| Candidate | Value |
| --- | --- |
| Build | `.private/builds/20261127-pixel-native-10` (byte-identical to tested build 09; preference-header comment corrected) |
| Module size | 42,116 bytes |
| SHA-256 | `59975c6a75cfcff0459218239acd6ee28d06588bfdf099e7ffd738aa17ceecd8` |
| Source | `z7-native-modules/plugins/lcd_pixel_nikon_checkpoint.c` |
| Host | Existing API44 host; no firmware update required |
| Installed everyday module | Unchanged; SHA-256 `8dcee0e026017de282288635ef92ea4bf544caa81863125c6c68f0ff995d611a` |

## Implemented behavior

The [official Z8](https://onlinemanual.nikonimglib.com/z8/en/psm_pixel_shift_shooting_156.html)
and [Z6III](https://onlinemanual.nikonimglib.com/z6III/en/psm_pixel_shift_shooting_167.html)
menus provide the reference labels and choices.

| Setting or action | Current implementation |
| --- | --- |
| Entry | Photo shooting menu → Pixel shift shooting. Preserves all 33 original rows and their event maps, plus the native eight-row viewport. The Extras entry also remains available. Back returns to the entry's parent. |
| Mode | Off, On (single photo), On (series). Single turns Off after one attempted group. Series requires a fresh full press for every group. Every boot starts Off. |
| Shots | 4, 8, 16, 32. Eight averages two four-position sets; 32 repeats 16 positions. Expanded geometry is software-tested only. |
| Delay | Off, 1, 2, 3, 5, 10 seconds, displayed in Nikon's descending order. Measured from full press, with the existing seven-second Z7 settling floor after release. |
| Interval | Numeric 00–30 seconds. Up/Down edits, J commits, Left cancels. Minimum start-to-start interval uses the native millisecond clock and includes processing time. Position verification can extend it. |
| Starting storage folder | New folder and Reset file numbering checkboxes. Reset requires New folder; turning New folder Off clears Reset. Calls Nikon's original unused-DCF-folder helper once per group, before sensor movement. Refusal stops the group. |
| Image quality | Worker selects NEF-only while pixel-shift mode is On. Off and Single completion restore the previous quality if the module still owns the change. Existing NEF-only requires no write. JPEG settings, RAW compression and depth are untouched. A later external quality change cancels pixel shift and is preserved. |
| Full press | Wraps the original CapStQue dispatcher at its event-task callback slot. Input queues a scalar request; the worker prepares RAW and captures. Half press alone does not arm. Off forwards native input; an owned full release remains consumed through cancellation. Physical routing is unverified. |
| Cancellation | Off or touching the shutter during the sequence stops the worker and attempts centering/restoration. The native J-between-shots shortcut has not been implemented. |

Count, delay, numeric interval and both folder flags persist in the separate
16-byte version-3 `A:\Z7PXL.DAT` record. Valid older versions migrate. Mode
and quality ownership never persist. An interrupted preference write may lose
the selection. On power loss, automatic quality restoration cannot run; the
user may need to reselect their previous quality after restart.

The result log remains `A:\Z7PIX.DAT` version 4: 32 file keys and 512 entries.
Use `tools/decode_z7_pixel_menu_log.py`. The computer merger supports all four
counts. No NX Studio group tags or in-camera merge are added.

## Remaining native differences

**AE bracketing is visibly unavailable.** Nikon brackets complete pixel-shift
groups, keeping one exposure throughout each group. Ordinary per-frame
bracketing would corrupt the merge. Original-Z7 exposure conversion research
now executes the native shutter and compensation paths, but metering lock,
Auto ISO, whole-group scheduling, longer logs and exposure restoration remain
unfinished. Compensation alone cannot bracket fixed-ISO manual exposure.

Single-frame release, self-timer Off and Silent photography On still need
manual setup. The worker checks them and refuses incompatible settings. Full
native mode handling, AF changes, the J cancellation shortcut and removal of
the measured settling floor remain unimplemented. Original-Z7 bindings must
be verified independently; Z7 II property IDs are not interchangeable.

[Upstream issue 7](https://github.com/JKWTCN/z7ii-extensions/issues/7) remains
open, checked November 27. It reports excessive displacement and missed phases
in preview.42. The maintainer suspects loose centering checks and native capture
interference with VR; these remain hypotheses. The Z7 implementation retains
tighter centering/rearm checks and verifies the commanded hold before and after
each exposure. This does not establish that the Z7 II defect was reproduced or
fixed here.

## Validation scope

The builder produces the candidate twice and verifies byte identity. Compiled
capture tests supply sensor telemetry, capture/file callbacks, property
publication, folder publication, clock and scheduling. Native-menu QEMU walks
use modeled services and synthetic camera readiness. These do not prove
physical shutter routing, exposure results, card durability or recovery.

The separate folder audit executes Nikon's actual unused-folder bitmap search
and helper, supplying card locking/storage boundaries: **12 checks pass**.
The exposure audit executes original PTP conversions and ROM tables with
supplied property boundaries: **23 checks pass**, establishing conversion units
only. It does not implement AE bracketing.

The repository suite passes **115 tests**, including 11 merge/log tests.
The exact module passes **88 compiled capture/settings checks** and **53
native-menu QEMU checks across 29 frames**. Screenshots were inspected privately.
Everyday and earlier simplified pixel-menu rebuilds retain their exact hashes.
All **277 saved-display regression checks** pass, including cold reloads of all
four presets, 10 saves and 16 native DISP skip checks. Exact-candidate results
are recorded in `evidence/20261127-pixel-native-settings.json`. The private
frozen packet is `.private/review/20261127-pixel-native-01`; it records offline
success and unfinished native parity separately. No stage/restore scripts were
prepared for this unfinished continuation.

## Installation and recovery assessment

No camera/card writes or firmware flash occurred. This is an SD module for
the existing host. The earlier frozen review packets remain historical and
must not be used to stage this different candidate.

Before a physical trial, confirm the exact installed host, card identity,
backups and readback hashes, and review this exact candidate. Replacement
requires a powered-off camera: a loaded dispatcher still points into the old
module until reboot. Recovery by power cycling or replacing the SD module
has not been established for this candidate. No emulator result establishes
camera update acceptance or emergency recovery.

The first trial must use four shots, a tripod, still subject, steady light,
manual exposure/focus, FX/L, native bracketing Off, Silent photography On,
single-frame release and self-timer Off. Begin with folder controls Off;
validate full-press behavior, four distinct NEFs, the log, centering, restored
quality and normal shooting before any folder or expanded-count trial.
Then test folder controls separately and 8/16/32 only after four-shot cleanup
and geometry are confirmed. Staging or flashing is not authorized by this
assessment itself.
