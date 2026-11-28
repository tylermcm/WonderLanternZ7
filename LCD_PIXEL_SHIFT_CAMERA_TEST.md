# Pixel shift shooting: camera test candidate

Status: **fifth build `cb8cb929`, prepared, not staged.** Earlier builds:
`ede43437` stopped before moving or firing, `8e1da6c8` froze the camera after
the shutter press, `13e0ce7d` took one frame and showed Reboot, and `7a536ea7`
took one frame and stopped cleanly. All four are explained below. It passes every offline and emulator
check. It is your everyday module (`8dcee0e0`:
display features, shutter sound, upside-down EXIF and playback) plus the full
pixel-shift menu. This continues
[LCD_PIXEL_NATIVE_TEST.md](LCD_PIXEL_NATIVE_TEST.md), which was frozen before
AE bracketing, the automatic setup and J-cancel were finished.

| Candidate | Value |
| --- | --- |
| Source | `z7-native-modules/plugins/lcd_pixel_nikon_checkpoint.c` (`--pixel-nikon-menu`) |
| Module | 48,164 bytes, SHA-256 `cb8cb9295475984781ef15da88f9bbb57d83e80967d88027dc0cca295c926754` |
| Host | Existing installed host; no firmware update |
| Settings file | `A:\Z7PXL.DAT` (count, delay, interval, folder options, AE choices) |
| Log | `A:\Z7PIX.DAT` (decode with `tools/decode_z7_pixel_menu_log.py`) |

## Where it is and what it does

**MENU → Photo shooting → Pixel shift shooting.** It is also still under
Custom settings → h → Extras.

| Setting | What it does |
| --- | --- |
| Pixel shift shooting mode | Off, On (single photo) or On (series). Every power-on starts Off. Single turns itself Off after one group. |
| Number of shots | 4, 8, 16 or 32. |
| Delay | Off, 1, 2, 3, 5 or 10 s after the full press. The camera always waits at least the measured 7 s settle after release. |
| Interval until next shot | 0–30 s, edited with up/down and J. |
| Options → AE bracketing | 2F, 3F, 5F, 7F or 9F groups, from 0.3 to 3.0 EV. Each group of 4/8/16/32 shots keeps **one** exposure; the exposure only changes between groups. |
| Starting storage folder | New folder (and Reset file numbering) before each group. |

**Mode dial on M.** The Z7's exposure mode comes from the dial, which the
module cannot change. In P, S or A it refuses before touching anything, and
the mode row shows **Use M**. Other status values: **Failed** means a setting
was refused and the run stopped safely. **Reboot** means something could not
be put back, so power-cycle the camera.

**Trigger:** a full press of the shutter while the mode is On. A half-press
alone does nothing. **Cancel:** press J, touch the shutter, or set the mode to
Off. The sensor is then recentred and stabilisation restored.

**What it changes for you during a group, then puts back:**
- image quality → NEF (RAW) only;
- release mode → single frame, with in-camera bracketing off;
- Silent photography → On;
- AF-C → AF-S, and Dynamic-area → Single-point;
- exposure: your M shutter speed and aperture are kept. If Auto ISO is on,
  it is fixed at the metered ISO for the group.

Each change is checked before the shutter fires. If anything doesn't stick,
or you change a setting yourself mid-group, it stops without firing and keeps
your change. If the battery dies mid-group, the automatic restore can't run,
and you may need to set image quality and the other settings back yourself
after restart.

## Camera test, in order

Use a sturdy tripod, a still subject with fine detail, steady light, manual
focus, FX image area, and the **mode dial on M**. Stop after any step that misbehaves and bring the
card back.

1. **4 shots, single, no bracketing, no new folder.** Mode On (single photo),
   4 shots, Delay Off, interval 0. Leave the menu and **fully press** the
   shutter once, then step back. Expect a 7-second wait, then 4 clicks. After
   it's done, the mode should read Off. Image quality, release mode, Silent,
   AF and exposure should all be back to what you had.
2. **Cancel.** Start another 4-shot group and press **J** after the first
   click. Expect it to stop, with no more clicks, and settings restored.
3. **AE bracketing.** Options → AE bracketing 3F, 1.0 EV, 4 shots. Expect 12
   clicks: three groups of four, darker/normal/brighter.
4. **New folder.** Turn on Starting storage folder → New folder, 4 shots.
   Expect the four photos in a new DCIM folder.
5. **8, then 16 shots.** Only if 1–4 went well.

Keep every photo and bring the card back after each session. I'll check the
log, the raw alignment and the merge.

**If anything seems wrong** (a noise, an error, a frozen screen, shots that
don't stop), power off. Take the battery out if needed. Then check your image
quality, release mode, Silent photography, AF and exposure settings.

## First camera run (`ede43437`, Nov 27)

Both attempts showed **Stopped** on the mode row, which was also clipped. The
log (`Z7PIX.DAT`, job error 1) shows the module tried to switch the exposure
mode from A (the dial) to Manual. The camera refused, because the mode
follows the physical dial. The module then did what it should on a refusal:
it stopped before moving the sensor or firing, and restored the settings.
The simulator had modelled the mode as writable. It now models the dial, and
the build requires M instead. The labels are now at most six characters
(**Use M**, **Failed**, **Reboot**).

## Second camera run (`8e1da6c8`, Nov 27): the full-press trigger froze the camera

The owner's report: after the full press, no photo was taken, Play and Menu
stopped responding, and a second press blanked the display. A power cycle
cleared it. The log (`Z7PIX.DAT`) shows what happened:
1. The module took the full press and armed: dial on M, exposure untouched,
   no setup error.
2. It saw the button released and began the 7 s settle.
3. It saw the button pressed again during the settle, the second press, and
   cancelled before any sensor move or release (0 moves, 0 frames).
4. Stabilisation stayed normal throughout.

**Cause, found in the firmware.** Nikon's shutter-switch handler
(`10060A38`) registers four callbacks: half down, full down, full up and half
up. The module had two of their addresses swapped. It took Nikon's **half-up**
for the full press and swallowed it, so Nikon believed the shutter was still
half-pressed. That is why Menu and Play stopped working. The module then armed
on the release, and it ate the next real full press. The simulator used the
same wrong table, so it could not see the problem.

**Fix (`13e0ce7d`).** The module now owns only the real full-down and
full-up. Half down and half up always reach Nikon. Before it hooks anything,
it checks Nikon's own registration code for the addresses. The simulator now
reads the table from the firmware instead of a hand-written list. It sends the
real press order (half down, full down, full up, half up) and fails if Nikon
is left half-pressed. Run against `8e1da6c8`, it fails with exactly that.

## Third camera run (`13e0ce7d`, Nov 27): one frame, then Reboot

The full press worked: no freeze, the group armed, and it waited the 7 s
settle. The first frame was taken with the sensor held at its position. The
log (`Z7PIX.DAT`, job error 2) then shows two problems:
1. **After the shot, Nikon gave stabilisation back to its normal mode.** It
   does this after every capture. This build checked the hold again *after*
   each photo and stopped when it found Nikon's normal mode. The proven v2
   series, which took 4 good frames, never made that check; it just sent the
   next position. The hold is still checked immediately before every release.
2. **The centring check never passed.** Tripod noise put each reading up to
   19 units off, and this build allowed only 8. Stabilisation was confirmed
   back in Nikon's normal mode, but the cleanup still waited for a centring
   check that never passed. So it left image quality and the other temporary
   settings unrestored and showed **Reboot**.

**Fix (`7a536ea7`).** After a photo, the module only logs the stabilisation
state. Cleanup, the next AE group and a new group now wait only for Nikon's
normal stabilisation to be confirmed, so settings are restored even when
centring is noisy. The simulator now does what the camera does: it hands VR
back after every capture, and centring reads up to 19 units off. Run against
`13e0ce7d`, it stops after the first frame, as the camera did. The older
builds still rebuild byte for byte.

## Fourth camera run (`7a536ea7`, Nov 27): one frame, then a clean stop

No freeze, and the mode row read **Off**: settings and stabilisation were
restored correctly. Frame 1 was taken. The sensor then moved to frame 2's
position and the follow check passed. But the single check right before the
release read 13 to 16 units off the target, and this build allowed only 8, so
it stopped before firing (log flag `hold_lost`, no error). On the tripod the
held sensor reads up to about 19 units off. The v2 series, which took four
good frames, allowed 24, and its frames landed within 0.15 px.

**Fix (`cb8cb929`).** The hold tolerance is now 24, as in v2. The check before
each release takes up to five readings 100 ms apart, so one noisy reading
can't end the group. A real loss (Nikon's normal mode, or another target)
still never passes. The simulator now adds ±19 to every held reading. With
that noise, 4 and 8 shots complete; ±40 never fires and still restores. Run
against `7a536ea7`, it stops as the camera did.

## Verified before the camera

All on this exact module, except the exposure, folder and repository checks,
which test the firmware bindings and tools it uses:

- **Capture and settings: 127 checks.**
  - camera-level hold noise (±19) completing 4 and 8 shots, and noise past the
    tolerance never firing;
  - Nikon's normal-VR handback after each capture, and noisy centring, with
    settings still restored and no Reboot;
  - shutter callbacks taken from Nikon's own registration code, half down and
    up always passed to Nikon, and Nikon never left half-pressed;
  - 4/8/16/32 positions, with single and series modes;
  - delay and interval timing, and the folder helper;
  - RAW, release, Silent and AF setup and restore;
  - AE groups holding one exposure each, up to 9 groups × 32 shots (288
    distinct files);
  - P, S and A refused before any write (the dial is read-only), and Auto ISO
    in M fixed and restored;
  - an external change aborting and being preserved;
  - refusals stopping before the shutter;
  - J cancelling;
  - saved, old and corrupt settings files.
- **Emulator: 59 menu checks across 32 screens,** from the Photo shooting
  entry through every picker, including AE bracketing and folder options.
- **Display suite: 277 checks**, unchanged.
- **Original-Z7 exposure conversions: 34 checks. Nikon folder helper: 12
  checks. Repository tests: 119.**
- The everyday module and every earlier camera-run pixel build still rebuild
  byte for byte.

**Not proven until the camera test:**
- that a full press reaches the module;
- real exposure results;
- 8/16/32 geometry on the camera;
- card durability;
- recovery after an interruption.

The emulator cannot take photos or move the sensor.

Credit: menu labels follow Nikon's public Z8/Z6III pixel shift manuals. The
design follows JKWTCN's MIT z7ii-extensions. Original-Z7 bindings are
independent work.
