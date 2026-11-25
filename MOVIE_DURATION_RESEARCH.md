# Original-Z7 native movie ceiling experiment

The Z7II feature extends ordinary movie recording beyond 29:59 using its native
task callbacks. The original-Z7 C 3.80 capacity and configuration layouts differ;
no Z7II callback or RAM address is installed here. The pinned upstream target is
recorded in [the parity inventory](UPSTREAM_PARITY.json).

## Native binding and experiment

Original capacity entry `0x10270C22` uses the ordinary duration table at
`0x115419E8`. The first four entries are zero; the next 24 are 1,799,000 ms.
The native alternative policy already uses a 359,999,000 ms ceiling. A stock
instruction audit covers the 28 format/quality indices, preserving the four
unsupported combinations, card quota, free-space, reservation, allocation-unit
and selected-volume rejection behavior.

Builder option `--extend-movie-duration` changes only those 24 ordinary ceiling
entries to the existing native alternative ceiling. It does not replace task
callbacks, bypass native error/stop branches or change the card-space calculator.
The native capacity calculation can return a duration longer than 29:59 under
the supplied inputs. This is **not proof of longer physical recording** or of
every native recording stop condition. The ceiling is not unlimited recording.

This table-based experiment is independent original-Z7 work, distinct from the
upstream RAM callback implementation. Whether it covers all original-Z7 writer,
encoder, countdown, segmentation and stop paths remains to establish. Special
recording paths, temperature handling, actual capacity and camera load still
need their native behavior verified; no duration or thermal guarantee is made.

## Exact private candidates

- Duration experiment MAIN SHA256:
  `b8db040d43418303f4fb2ea5622e5689403349c08267b956664bc2bd149b5667`.
- Control MAIN SHA256:
  `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.
- Both MAIN files are 33,058,840 bytes; the SD host code is identical.
- The control matches the installed-host baseline. The experiment remains
  emulator-only, with no installation clearance, update container or card copy.
- This pair uses the API44 display host. The API72 highlight integration remains
  a separate host/profile; it is not made compatible by the duration option.

Both candidates build reproducibly and pass independent full reconstruction.
The candidate differs from the control only in the reviewed 96-byte table span.
The raw emulator EG member has a valid CRC; this is not a reviewed camera update.

```powershell
.venv\Scripts\python.exe tools/build_z7_module_host.py --source .private/stock/Z_7_0380.bin --display-hooks --extend-movie-duration --output .private/builds/movie-duration-new
```

## Evidence and remaining work

`tools/audit_z7_movie_capacity.py` passes 197 stock-native contract checks and
370 checks with the exact candidate/control pair. The differential run compares
the candidate's ordinary capacity results and flags against the stock native
alternative calculation for the admitted formats, and retains the unsupported
format and tested capacity rejection paths. Original format lookups, integer
arithmetic and bytes-to-time functions execute; incoming configuration and card
state are supplied. Source-only evidence is in
[the capacity record](evidence/20261124-movie-duration.json).

Read-only stock QEMU inspection separately distinguished the native event
dispatcher from a cyclic wake callback. That avoids treating a timer notification
as a recording handler. No such callback is changed by this experiment.

Next work is tracing the UI-to-recorder duration propagation and native elapsed-
time stop condition, then assessing file splits and ordinary mode exclusions.
Orientation metadata is a separate port. Hardware long recording, exported file
duration/playback, temperature behavior and recovery remain unverified.

There is no flash approval or recovery clearance. Before any proposed camera
installation, prepare an exact update-container and host/module assessment,
preserve existing files and working candidates, and obtain explicit owner
authorization. Earlier recovery by card/battery removal does not establish
recovery from this firmware change.
