# Pixel shift step 1: read-only VR telemetry probe

Status: **prepared, not staged.** Your everyday module (`8dcee0e0`: display
features, shutter-sound page, upside-down EXIF fix and playback, all working on
the camera) plus a probe that only **reads** the in-body VR (IBIS) controller.
First step of the [pixel-shift plan](PIXEL_SHIFT_RESEARCH.md).

## What it does

- From the module's background task, while the VR service is idle and has no
  request outstanding, it sends position **reads** (opcode `0xF040`) through
  Nikon's own BodyVr command service and saves the answers to `A:\Z7VRLOG.DAT`.
- It reads four small windows: the Z7II telemetry block (`0x0FE0`, 42 bytes) and
  three addresses Nikon's own Z7 code reads (`0x1018`, `0x1FF8`, `0x1FF9`).
- It **never** sends the position command and never changes VR settings, so the
  sensor is not moved. At most one read per background tick, 48 rounds, then it
  stops until the next power-on.
- Everything else is unchanged; your current module is kept on the card.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + VR probe, SHA-256 `e5ac0844…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7VRLOG.DAT` | The probe's log |

## Steps (about 3 minutes)

1. Power on with a lens attached and **VR on** in the menu. Stay in photo-mode
   live view on a tripod or a steady surface for about **1 minute**.
2. Then hand-hold the camera for about **1 minute** in live view (so the VR is
   actively correcting).
3. Power off and bring the card back.

What I will look for: whether the reads succeed, and which bytes behave like
target and measured actuator positions (steady on the tripod, moving when
hand-held). That tells the next step where to confirm the sensor has settled.

## Verified before the camera

- `8dcee0e0` still rebuilds byte for byte; the probe is behind its own switch.
- Offline: the display suite (277), the upside-down/playback checks and the
  folder checks pass unchanged on this build, plus 16 probe checks: only reads
  are ever sent (never the position command), the four windows go out in
  order with the right addresses and lengths, one request per tick and only
  with the service idle and no callback outstanding, returned bytes and
  statuses are logged, a lost reply times out safely, a refused send is not
  waited on, it stops after 48 rounds, the log file has the documented layout,
  and a firmware mismatch sends nothing.
- Emulator: the module boots and Nikon's menus work (26 checks). The emulator
  does not model the VR controller.
