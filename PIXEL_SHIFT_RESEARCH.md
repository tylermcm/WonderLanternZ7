# Pixel shift on the original Z7: research

Status: **research only, November 26, 2026.** Nothing has been built or run on
the camera. Target: JKWTCN's MIT Z7II pixel shift (`8aad350`, released
November 25, 2026). The Z7 and Z7II use the same 45.7 MP sensor size
(8256 × 5504), so the shift geometry should carry over; the firmware bindings
must be found independently.

## How upstream does it (Z7II C 1.70)

- The camera's in-body VR (IBIS) is driven through Nikon's **BodyVr command
  service**: a 40-byte request (opcode, device address, length, payload,
  output) sent with a completion callback.
  - Opcode `0xF040` reads 42 bytes of VR telemetry (target and measured actuator
    positions, a state byte) from device address `0x0FE0`.
  - Opcode `0xF1F1` sets the sensor position with a 10-byte payload
    `{0, x, 0, y, 0, 16, 16, 0, 0, 2}`; x/y are half-pixel-scale steps (21 and
    18 per pixel on the Z7II, calibrated).
- A worker task, per frame: wait until capture is idle and VR telemetry is
  settled at the previous position; send `0xF1F1`; wait until telemetry shows the
  new position twice; fire Nikon's own release call; wait for the NEF file to
  be written. 4/8/16/32 frames cover the Bayer phases (and half-pixel phases
  for 16/32). Afterwards it recentres the sensor and restores Nikon's own VR
  parameters ("D2" settings).
- It forces silent photography and uncompressed 14-bit NEF during the series,
  tags the NEFs as a group for NX Studio, and can merge in camera.

## Found on the original Z7 (C 3.80)

Checked by `tools/audit_z7_pixel_shift_bindings.py` (20 static checks):

| Piece | Original Z7 |
| --- | --- |
| Service | Component `0x042F` **BodyVrCommandService** (also `0x0306` BodyVrService, `0x0205` BodyVrProtocolService) |
| Send | `0x100F1F9E`, the same 40-byte request: opcode at `+0x00`, payload at `+0x1C`, output at `+0x24`; three native callers |
| Read | Opcode `0xF040` handled; Nikon itself reads 6 bytes at device address `0x1018` (the Z7II telemetry block is at `0x0FE0`) |
| Move | Opcode `0xF1F1` handled at `0x100F2048`: copies a **10-byte payload** and sends it as a 10-byte device command, the same shape as upstream's |

So the original Z7 has the same mechanism. Still to find before anything moves:

1. The VR telemetry block on the Z7 (address and layout of target/measured
   positions and the state byte), so "settled" can be checked.
2. Nikon's still-release call, the capture-idle state and the file-written
   event for single frames (the shutter-sound work already measured the
   capture events and still-file notification on this camera).
3. The VR "D2" parameter cache and how Nikon restores it, so the sensor is
   always returned to normal stabilisation.
4. The step scale for one pixel on the Z7 (calibration, as upstream did).

## Step 1 built: read-only probe

Completion of a BodyVr request calls the stored callback (slot `0xA18B5D88`,
cleared afterwards) with event `0x042F0021` and a result whose first byte is the
status; the send refuses while `0xA18B6030+0x34` is 1. The probe
([LCD_VR_PROBE_TEST.md](LCD_VR_PROBE_TEST.md), build `e5ac0844`) uses only
`0xF040` reads of four windows and logs them; 16 offline checks. Not staged.

## Safety plan

Moving the sensor is the riskiest experiment so far, so it goes in small,
reversible steps, each needing your approval:

1. **Read-only telemetry probe**: a module that only sends `0xF040` reads while
   the camera is idle and logs them to the card. No movement.
2. **One tiny move and back**: one `0xF1F1` with a minimal offset while idle,
   confirm the telemetry follows, recentre, confirm normal VR. No capture.
3. **Four-frame series** on a tripod, files merged on the computer (NX Studio
   or upstream's Parsek NEFX) before any in-camera merge.

Credit: design follows JKWTCN's MIT z7ii-extensions; original-Z7 bindings are
independent work.
