# Z7 pixel-shift menu candidate

November 27, 2026. **Prepared privately; not installed or camera-tested.**
This is an independent original-Z7 C 3.80 SD-module candidate, retaining the
everyday module's display, shutter-sound folder, EXIF and inverted playback.
It does not require a firmware/host update. Read [RISK_NOTICE.md](RISK_NOTICE.md).

| Item | Exact candidate |
| --- | --- |
| Source profile | `z7-native-modules/plugins/lcd_pixel_menu_checkpoint.c` |
| Builder | `tools/build_z7_lcd_volatile.py --pixel-menu --output NEW_PRIVATE_DIRECTORY` |
| Module size | 35,452 bytes |
| SHA-256 | `201235a678c3485ff3301af85d3592958849d9b3cc8069fd54c5cfcc44246e8e` |
| Installed everyday baseline | `8dcee0e026017de282288635ef92ea4bf544caa81863125c6c68f0ff995d611a` |
| Installed host payload baseline | `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce` |
| Settings | Volatile; starts disarmed at 4 frames each boot |
| New log | `A:\Z7PIX.DAT`, version 4, 32 photo keys and 512 telemetry entries |

## Controls

Open **Custom settings → h Display settings → Extras → Pixel shift**.

- **Frames:** OK cycles 4, 16, 32. It cannot change during an armed/running group.
- **Arm series:** OK arms the next group. Press it again to cancel.
- **Status:** Ready, Armed, Running, Wait, Done, Stopped or Restart.
- **Back:** returns to Extras. The Back key does the same.

After arming, leave the menu, half-press until the stabiliser is active, then
release the button and step back. The module waits for the button to be free,
then allows seven seconds for the body to settle. It approaches each y target
from above, confirms it twice, waits another 500 ms and checks it again before
the release. Each confirmed photo has an audible click. It recentres, applies
Nikon's current VR settings, and observes the return to normal afterwards.
After a successful group and that observation period, another group can be
armed without restarting. A failed centre/restore or timed-out request blocks
rearming. The status does not turn an unverified physical recovery into a guarantee.
An atomic ownership guard excludes menu resets while the worker is active;
cancellation remains a separate nonblocking flag.

Use a tripod, a static subject, M exposure, manual focus, FX/L NEF, steady light,
Silent photography ON, **single-frame release and self-timer OFF**. The new
worker reads the latter three settings before starting and before each shot;
it refuses other configurations rather than changing camera settings. It also
requires photo view with menus/playback closed. Keep the shutter button free
during the group. A touch, cancellation, lost hold, busy release callback or
capture failure stops the series and attempts the normal cleanup.

## More frames

Four shots use the previously measured 20/18 sensor-step scale. Sixteen shots
add four half-step offsets of 10/9 steps. Thirty-two shots repeat the same
sixteen positions for averaging. Every frame retains the approach-from-above
procedure. The largest approach is 63 y steps, or 252 telemetry counts.

The half-step scale is a starting value derived from the four-shot calibration,
**not a measured 16/32-shot result**. Test four shots first, inspect its log and
raw alignment, then test 16 and finally 32. The
[computer merger](PIXEL_SHIFT_MERGE.md) supports doubled-resolution 16/32-shot
sets; there is no in-camera merge or NX Studio tagging in this candidate.

## Upstream bug review

[Z7 II issue #7](https://github.com/JKWTCN/z7ii-extensions/issues/7) reports
excessive displacement and inconsistent steps in preview.42. The author's
[reply](https://github.com/JKWTCN/z7ii-extensions/issues/7#issuecomment-7207179806)
suspects a loose centering check and native capture interfering with VR.
The later [single-release fix](https://github.com/JKWTCN/z7ii-extensions/commit/34d9cd09b1a4d50ae608056e649fcd827859119d)
temporarily selects single release on the Z7 II.

This Z7 candidate keeps exact commanded targets, tightens measured error to
8 telemetry counts, checks the hold both before and after each exposure, and
requires confirmed centering and restore before rearming. It requires single
release and no self-timer rather than copying the Z7 II's native setters.
The upstream report is still open at inspection. These are defensive changes,
not a claim that its reported failure has been reproduced or solved on a Z7.

## Validation and installation boundary

The module builds twice identically. The everyday baseline and earlier
four-shot v2 module still rebuild to their exact camera-tested hashes.
Compiled menu/worker simulations cover 4/16/32 counts, every target, cleanup,
explicit rearming and refusal/cancellation cases. Emulator checks cover menu
navigation, count choices and arming/cancelling without sensor work. The saved
display-preset suite is also rerun. Current exact-candidate results are recorded
in the private review packet and sanitized source evidence.

The exact candidate above passes **60 compiled capture/menu checks, 277 saved
display-preset checks and 31 emulator menu checks**. The workspace has **113
passing unit tests**, including 10 merge/log tests. No new physical-camera
result is included in these counts.

Those checks supply stabiliser, capture, filesystem and scheduler boundaries.
They do not establish real sensor timing, long exposures, shutdown during a
group, card-full/error handling, thermal limits or the 16/32-shot geometry.
The menu and repeat-session workflow need a new camera test even for four shots.

Installation is an SD-module swap only after the exact packet is reviewed and
the camera is fully off with card activity finished. Preserve and verify the
existing `Z7APP.BIN` as `Z7APP.LCD-EVERYDAY-8DCE.disabled`, back up the card root,
then copy and read back the frozen candidate. Keep every existing setting,
sound and photo. Never substitute the Z7 II module or a different host.

If the trial is stopped, power off, wait for activity to finish, remove the
card and restore the preserved everyday module; retain the candidate and copy
`Z7PIX.DAT` privately for inspection. Do not remove a writing card. If normal
power-off is unresponsive, the owner's earlier lab recovery was power removal
and restoring the card module. **Emergency recovery and interruption during
sensor movement are not physically verified for this exact candidate.**
No camera flash, card staging, camera capture or physical recovery test was
performed while preparing this candidate.

Credit: JKWTCN's MIT Z7 II pixel-shift design. Original-Z7 integration,
bindings, menu, capture guards and offline checks are independent work.
