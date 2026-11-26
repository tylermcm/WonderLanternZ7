# Pixel shift step 2: one tiny sensor move and back

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`:
display features, shutter-sound page, upside-down EXIF fix and playback) plus a
test that moves the image sensor **once** by a tiny amount and then puts it back
at centre. It is step 2 of the [pixel-shift plan](PIXEL_SHIFT_RESEARCH.md).
Step 1 ([LCD_VR_PROBE_TEST.md](LCD_VR_PROBE_TEST.md)) found the telemetry
layout on this camera.

## What it does

- **Waits.** Once a second it reads the VR (IBIS) telemetry. It does nothing
  until a read shows stabilisation **active and steady**: state byte 1, and the
  measured position within 48 counts of the target on every axis. A second read
  100 ms later must confirm it. If that never happens within 10 minutes, it
  gives up without moving anything.
- **Moves once.** It sends one position command (`0xF1F1`) with upstream's
  10-byte payload and step x = 4, y = 0. On the Z7II scale that is about **a
  fifth of a pixel**. It then reads the telemetry every 100 ms for up to
  2 seconds, to see whether the target and measured positions follow.
- **Recentres.** Whenever the move may have reached the VR unit (even if it
  was not followed, or the reply was lost), it sends the centre command, retried
  up to 5 times. Then it watches the telemetry again.
- **Watches.** For 30 more seconds, one read per second, to see whether the
  camera returns stabilisation to normal by itself.
- **Once per power-on.** It never takes a photo and never changes Nikon's VR
  settings. Everything is logged to `A:\Z7VRMOV.DAT`.

After the move, stabilisation may stay **held at centre** (off) until the next
power cycle. Upstream restores it with Nikon's own VR parameter call. That call
is not yet found on the Z7, which is why this test does not take photos.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + one-move test, SHA-256 `5fe15dcc…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRMOV.DAT` | The test's log (rewritten on every power-on) |

## Steps (about 3 minutes)

1. Lens attached, **VR On** (Normal) in the photo shooting menu, photo mode.
2. Power on. Hand-hold the camera and aim at something detailed. Every few
   seconds, **half-press** the shutter button and hold it for about 3 seconds,
   then let go. Repeat for about a minute. **Do not take a photo.**
   - At some point the test runs by itself (2-4 seconds). You may see a tiny
     jump in live view, or nothing at all.
3. Keep the camera on for **one more minute**, then power off.
4. **Do not power on again** before the card comes back: each power-on runs the
   test again and rewrites the log. Bring the card back, and I restore your
   everyday module. Your next power-on then has normal stabilisation.

**If anything seems wrong** (a noise from the camera, an error message, a frozen
screen), power off at once. If it does not turn off, take the battery out.
Either way the sensor returns to its normal state at the next power-on.

## What I will look for

- whether the VR unit accepts the command (status 0);
- whether the target moves to the expected value (-16 on the first axis on the
  Z7II scale) and the measured position follows, then returns to 0;
- the state byte during the hold (upstream expects `0x40`);
- whether the camera returns stabilisation to normal by itself.

That gives the Z7 step scale for later calibration and shows whether the
restore call is needed.

## Verified before the camera

- `8dcee0e0` still rebuilds byte for byte; the test is behind its own switch.
- Offline against a simulated VR unit (25 checks):
  - it only moves after stabilisation is active and settled on two reads;
  - the payload is exactly upstream's shape with x = 4, y = 0;
  - one move and one centre per boot, every send made with the service idle;
  - it always recentres once a move may have reached the device, including
    when the move is ignored and when its reply is lost;
  - a refused move commands nothing more;
  - it never moves on a parked, unsettled or briefly active unit, a busy
    service or a firmware mismatch;
  - the worker is held for at most about 12 seconds;
  - the log has the documented layout and phases, and it goes quiet afterwards.
- The display suite (277), playback (22) and folder (22) checks pass unchanged.
- Emulator: the module boots and Nikon's menus work (26 checks). The emulator
  does not model the VR unit.

Credit: design follows JKWTCN's MIT z7ii-extensions pixel shift; original-Z7
bindings are independent work.
