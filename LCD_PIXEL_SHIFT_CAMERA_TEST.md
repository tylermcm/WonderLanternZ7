# Pixel shift shooting: camera test candidate

Status: **prepared, not staged.** It passes every offline and emulator check,
and nothing has run on the camera yet. It is your everyday module (`8dcee0e0`:
display features, shutter sound, upside-down EXIF and playback) plus the full
pixel-shift menu. This continues
[LCD_PIXEL_NATIVE_TEST.md](LCD_PIXEL_NATIVE_TEST.md), which was frozen before
AE bracketing, the automatic setup and J-cancel were finished.

| Candidate | Value |
| --- | --- |
| Source | `z7-native-modules/plugins/lcd_pixel_nikon_checkpoint.c` (`--pixel-nikon-menu`) |
| Module | 48,100 bytes, SHA-256 `ede43437747aafe14939e70109568687ac19e274d329f132e86ee9f548206f08` |
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

**Trigger:** a full press of the shutter while the mode is On. A half-press
alone does nothing. **Cancel:** press J, touch the shutter, or set the mode to
Off. The sensor is then recentred and stabilisation restored.

**What it changes for you during a group, then puts back:**
- image quality → NEF (RAW) only;
- release mode → single frame, with in-camera bracketing off;
- Silent photography → On;
- AF-C → AF-S, and Dynamic-area → Single-point;
- exposure frozen: P/S/A are held at the metered exposure in temporary
  Manual, and Auto ISO is fixed at the metered ISO.

Each change is checked before the shutter fires. If anything doesn't stick,
or you change a setting yourself mid-group, it stops without firing and keeps
your change. If the battery dies mid-group, the automatic restore can't run,
and you may need to set image quality and the other settings back yourself
after restart.

## Camera test, in order

Use a sturdy tripod, a still subject with fine detail, steady light, manual
focus, and FX image area. Stop after any step that misbehaves and bring the
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

## Verified before the camera

All on this exact module, except the exposure, folder and repository checks,
which test the firmware bindings and tools it uses:

- **Capture and settings: 116 checks.**
  - 4/8/16/32 positions, with single and series modes;
  - delay and interval timing, and the folder helper;
  - RAW, release, Silent and AF setup and restore;
  - AE groups holding one exposure each, up to 9 groups × 32 shots (288
    distinct files);
  - P/S/A/Auto ISO frozen and restored;
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
