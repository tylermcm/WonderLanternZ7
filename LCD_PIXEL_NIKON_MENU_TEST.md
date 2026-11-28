# Nikon-style pixel-shift controls for the original Z7

November 27, 2026. **Offline candidate; not installed or camera-tested.**
Independent original-Z7 C 3.80 work following the public
[Z6III menu](https://onlinemanual.nikonimglib.com/z6III/en/psm_pixel_shift_shooting_167.html)
and [Z8 menu](https://onlinemanual.nikonimglib.com/z8/en/psm_pixel_shift_shooting_156.html).
This extends the earlier [test interface](LCD_PIXEL_MENU_TEST.md), while retaining
the everyday sound-folder, display and inverted-playback components.

| Candidate | Value |
| --- | --- |
| Source | `z7-native-modules/plugins/lcd_pixel_nikon_checkpoint.c` |
| Build flag | `tools/build_z7_lcd_volatile.py --pixel-nikon-menu --output NEW_PRIVATE_DIRECTORY` |
| Module | 38,824 bytes |
| SHA-256 | `723809cd9ecb8a9c3cf7dc1eb8b0584e2a35377d27b965966d3fc3f9becc4d76` |
| Host | Existing API44 host; no firmware update required |
| Preference file | `A:\Z7PXL.DAT`, 16-byte versioned/checksummed record |

## Menu and behavior

Open **Custom settings → h Display settings → Extras → Pixel shift**.
The page title is now **Pixel shift shooting**. It has Nikon's six settings,
with a Back row for this Z7 interface. Pickers highlight the current choice.

| Setting | Implemented behavior |
| --- | --- |
| Pixel shift shooting mode | Off; On (single photo); On (series). Single switches Off after one attempted group. Series stays enabled, but another group requires a fresh deliberate trigger. |
| Number of shots | 4, 8, 16 or 32. Eight repeats the four Bayer corners for averaging. Thirty-two repeats the sixteen half-step positions. |
| Delay | 0, 2, 5, 7, 10, 20 or 30 seconds. The larger of the selected delay and the measured seven-second Z7 settling minimum is used. |
| Interval until next shot | 00, 01, 02, 03, 05, 10 or 30 seconds. A conservative minimum: sensor settling, capture and file handling can make the actual interval longer. |
| Options | Off is supported. AE bracketing is visible but unavailable; selecting it explains that no setting was changed. |
| Starting storage folder | New folder and Reset file numbering are visible but unavailable. Their switches cannot be enabled. |

This is **core control matching, not complete Nikon feature parity**. The
entry remains in Extras rather than the Photo shooting menu. Timings are
bounded presets rather than Nikon's full numeric editor. The existing host
uses a **half-press and release**, not interception of Nikon's full-press
capture event. AE bracketing and automatic folder/numbering management still
need independently verified original-Z7 bindings and capture integration.
No Z7 II property writer or unverified file-management address is used.

Count, delay and interval are saved after two stable worker ticks. The shooting
mode is never saved: every power-on starts **Off**. Missing, corrupt or
out-of-range preferences fall back to 4 shots, a seven-second delay and zero
additional interval, with mode Off. The record is separate from every existing
display, sound and playback file. Interrupted preference writes may lose the
new selection; physical save/recovery behavior has not been tested.

## First camera trial

Start with a four-shot sequence. Use a tripod, a still subject, steady light,
M exposure, manual focus, FX/L NEF, Silent photography ON, single-frame release,
self-timer OFF and native bracketing OFF. Select **On (single photo)**, leave
the menus, half-press for several seconds, then release and step back. The
Z7 settling checks remain active even with Delay set below seven seconds.

After the four photos, the mode should be Off. Allow the existing restore and
observation period to finish. Check the log and raw alignment before testing
8 shots, then 16 and 32. The [computer merger](PIXEL_SHIFT_MERGE.md) accepts
all four counts; real 8/16/32 geometry and image quality remain unverified.

**On (series)** keeps pixel shift enabled until Off is selected. It does not
run groups continuously. Each group needs a new half-press/release after the
previous group restores normal stabilisation. Off cancels an active group;
the worker attempts centering and the existing Nikon D2 restore. Counts and
timings cannot change during a group or its restore/observation period.

The result log remains `A:\Z7PIX.DAT` version 4. Use
`tools/decode_z7_pixel_menu_log.py` to inspect it. It has room for 32 file keys
and 512 entries. No in-camera merge or NX Studio pixel-shift tagging is added.

## Evidence and limits

The ARM builder runs twice and checks byte identity. Compiled menu/capture
checks cover all four counts, single/series mode semantics, fresh triggers,
minimum delays/intervals, Off cancellation, failed capture/hold cleanup and
cold preference loading. Tests restore an initialized RAM/service snapshot
between independent cases; additional cold starts exercise saved/corrupt files.
The native menu emulator checks the rendered labels, current-choice focus,
all selector pages, unavailable options and the modeled preference write.
Existing saved-display checks and root tests are also run.

Exact final candidate passed **49 compiled capture/settings checks, 277 saved-display
checks and 46 native-menu emulator checks across 25 frames**. All **115 root
tests** passed, including 11 merge/log tests. Everyday and earlier pixel-menu
regression builds remain byte-identical. These counts describe software checks.

These fixtures supply sensor, capture, filesystem and scheduling boundaries.
They do not establish physical capture timing, native reset-menu integration,
full-press behavior, 8/16/32 image quality, interrupted writes or emergency
recovery. Real camera verification is still required.

## Installation and rollback assessment

This is an SD-module swap on the already installed host, not a host firmware
flash. The expected everyday module is
`8dcee0e026017de282288635ef92ea4bf544caa81863125c6c68f0ff995d611a`;
the installed-host payload baseline is
`24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.
Use only a frozen review packet whose module, assessment and source hashes match.

With the camera fully off and card activity finished, preserve and verify the
everyday module as `Z7APP.LCD-EVERYDAY-8DCE.disabled`, back up the root files,
copy the reviewed candidate as `Z7APP.BIN`, and verify its full readback.
Preserve all photos, sounds and existing settings. This preparation did not
perform the swap. Read [RISK_NOTICE.md](RISK_NOTICE.md).

Rollback is to power off, wait for card activity, remove the card, copy the
trial log and preferences privately, park the candidate and restore the exact
preserved everyday module. Retain `Z7PXL.DAT`; the everyday module ignores it.
Earlier lab recovery used power removal when normal shutdown failed, but that
does not verify emergency recovery during this candidate's sensor movement.
Do not remove a writing card. Physical interruption/recovery remains unverified.

Credit: JKWTCN's MIT Z7 II pixel-shift design and the existing original-Z7 lab
bindings. The Nikon-style controls, persistence and 8-shot integration are
independent modifications; component licenses and notices remain intact.
