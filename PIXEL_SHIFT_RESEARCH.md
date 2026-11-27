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
`0xF040` reads of four windows and logs them; 16 offline checks.

## Step 1 result: telemetry on the camera (Nov 26)

The probe (`e5ac0844`) was staged, run and restored. The log covered 12 rounds:
48 reads, 0 refused, 0 timeouts, every status 0. It never moved the sensor.
Layout of the 42-byte window `0x0FE0` (signed little-endian int16, three axes):

| Bytes | Meaning (Z7) | Evidence |
| --- | --- | --- |
| 0x00-0x05 | target position | constant `(-770, -8591, -8598)` while VR was idle (rounds 0-8, 10-11); `(1950, -1158, -4308)` in the hand-held round 9 |
| 0x06-0x0B | servo error, target - measured | round 9: `(-26, -104, 128)`, exactly target - measured |
| 0x22 | state byte | 0 idle, 1 in the active round |
| 0x24-0x29 | measured position | drifts while idle (unpowered sensor), tracks the target within ~130 counts when active |

The layout is the same as JKWTCN's Z7II telemetry block. Other windows:
`0x1018/6` reads three int16 values of about 91 that stay steady.
`0x1FF8` always reads 1. `0x1FF9` alternates 0/1.

For step 2, "settled" can be read as state byte 1 and |error| small on every
axis. The step size for one pixel is still unknown.

## Step 2 built: one tiny move and back

[LCD_VR_MOVE_TEST.md](LCD_VR_MOVE_TEST.md), build `5fe15dcc`. Once per boot it
waits until telemetry shows stabilisation active and settled (state 1, |error|
<= 48, confirmed 100 ms later). It then sends one `0xF1F1` with upstream's
payload `{0,4,0,0,0,16,16,0,0,2}` (about 0.2 pixel on the Z7II scale) and
polls telemetry every 100 ms. Whenever the move may have applied, it always
sends the centre payload, then watches for 30 s. It uses Nikon's delay
`0x1017081E` between polls. The D2 restore is not used, so a power cycle
returns normal stabilisation. 25 offline checks against a simulated VR unit.

## Step 2 result: the sensor moved and came back (Nov 26)

The one-move test (`5fe15dcc`) was staged, run hand-held and restored. Log:
56 requests, 0 refused, 0 timeouts, every status 0. Flags: armed, move sent,
acknowledged and followed, centre sent, acknowledged and followed.
Stabilisation did not return to normal on its own.

- **Arming:** state 1 was first seen at tick 10. Settling was confirmed at
  tick 15 with errors of at most 41 counts.
- **Move** (`x = 4`): state `0x88` while ramping. The target on axes 1/2
  went 469/-470, then 32/-33, then 0. After that the state was `0x40` (hold)
  with target **exactly `(-16, 0, 0)`**, the Z7II scale (-4 x step). Measured
  was -20 and -30 on the first axis, against about ±15 counts of noise in hold.
- **Centre:** target `(0, 0, 0)`, state `0x40`. Measured stayed within about
  20 counts for the whole 30-second watch.
- **No automatic return:** the state stayed `0x40` for 30 s. Normal
  stabilisation needs Nikon's D2 parameter restore (upstream `restore_d2`),
  or a power cycle. Finding that call on the Z7 is the next research item.

So the Z7 uses the same `0xF1F1` payload and the same -4-per-step target
scale as the Z7II. One pixel is probably about 21/18 steps as upstream
calibrated, but that is not yet measured on this sensor.

## Step 2b found and built: the D2 restore

Upstream's Z7II restore (`restore_d2`) re-sends Nikon's last VR parameters
with `0x103939A1(selection, flags, 0)`. The Z7 counterpart is
**`0x101C63F8(selection, flags, callback)`**:

- it checks BodyVr state 1 (`0x100F3298`);
- it copies selection bytes 0 and 1 and the flags into the command-4 buffer
  at `0xA235B900+0x144` = `0xA235BA44` (bytes 0, 1 and 8, upstream's D2
  layout);
- it sends device command 4 through the protocol send `0x100B5E32`, and
  command 5 when needed.

Nikon's own VR-mode apply (`0x101C69D8`, BodyVr task event bit 4 at
`0x101DF34C`) calls it. The position command uses a separate buffer
(`0xA235B900+0x9C`), so the D2 buffer still holds Nikon's last parameters
during a hold. Upstream's "duplicate filter" clear has no Z7 counterpart:
the Z7 hook at `0x100F16D6` is an empty function. Commands are admitted by
service state instead.

Build `2ff19bde` (`--vr-restore`) adds this to the one-move test. It
snapshots the D2 buffer before moving (no snapshot, no move), re-sends it
after recentring, and polls until the state leaves `0x40`. 19 offline checks;
31 static binding checks.

## Step 3a built: series dry run

[LCD_PIXEL_SERIES_TEST.md](LCD_PIXEL_SERIES_TEST.md), build `b68284dc`
(`--pixel-series`). Upstream fires the shutter itself (`0x103BA6EB` with
settings `{0x100,0,0,1,1}`). On the Z7 the candidates are `0x101ECFB0`, which
checks property `0x11B` as upstream's capture-ready test does, and
CaptureStateControlService `0x10203D40`, used by remote release in
`CCaptureCameraControl` around `0x10520ED4`. Their request layouts are not
pinned down yet. The dry run therefore leaves the shutter to the
photographer. After each new photo (still-file hook `0x041E0002`), it steps
the sensor through the four Bayer corners at upstream's 21/18 scale. It
re-sends a lost hold, and recentres and restores D2 at the end. 20 offline
checks. The run also shows whether a half-press or a native release ends the
hold.

`tools/measure_z7_pixel_shift.py` checks the result on the computer. It
phase-correlates the full-size preview JPEG inside each NEF against the first
photo, with sub-pixel peak fitting. Synthetic 1-pixel shifts read back as
1.000 px, or 1.014 px after a JPEG round trip. So the four photos show
directly whether 21/18 steps move the image one pixel on the Z7.

Still open after 3a: the release call (for an unattended series), capture-idle
and settings guards, NX Studio group tags, and the Z7 step calibration.

## Step 3a result: Nikon takes the sensor back on every half-press (Nov 27)

The series dry run (`b68284dc`) ran on a tripod and was restored. Log: 228
requests, all status 0, no timeouts. Four photos were counted, the series
finished and the sensor was recentred. Stabilisation was back to normal
within 2 s; Nikon had already re-sent its D2 parameters, so the module's own
D2 sender was never called and is still untested.

- **Every position command was followed** (state `0x40`, target exactly
  `(0,0,0)`, `(-84,-72,-72)`, `(0,-72,-72)` at the 21/18 scale, measured
  within about 20 counts).
- **The hold did not survive the photographer.** It was lost 6 times (the
  maximum number of re-sends):
  - after about 20 s idle, the unit parked (state 0, park target
    `(-770,-8591,-8598)`);
  - on each half-press, normal stabilisation came back (state 1) and the
    D2 buffer changed (`D2_CHANGED`);
  - state 2 appeared once, around a release.
  So the photos were exposed with normal stabilisation, not at the
  commanded positions. Photos 1 and 2 were also counted in the same tick,
  so the corner (21,0) was skipped.
- **Photos.** `tools/measure_z7_pixel_shift.py` on the four JPEGs gives
  shifts of (1.03, -1.13), (1.06, -2.65) and (1.24, -2.02) px. Correlation
  peaks are low (0.19-0.27). That is camera movement from pressing the
  shutter, not the Bayer pattern. There is no calibration from this run.

**Conclusion.** On the Z7, as upstream's design implies, the shutter must be
fired by the module, right after the position is confirmed and without a
half-press. A photographer-driven series cannot hold the sensor. Next:
pin down the Z7 release call (`0x101ECFB0` / `0x10203D40`, request layouts),
then a module-fired series. The D2 snapshot from this run was `0x030301`
(selection 1, 3; flags 3).

## Step 3b built: module-fired release

The release is **`0x101ECFB0(request, callback)`**, Nikon's capture API.
Nikon's PTP InitiateCapture handlers (`0x10308DE6`, `0x10319F40`) and remote
capture control (`0x10520FBC`) all call it. It returns 0 when it accepts, or
one of Nikon's refusal codes (`0xA`-`0x1C`). It checks property `0x11B`, as
upstream's capture-ready test does.

The request is 0x14 bytes, as the PTP builder `0x10308C80` fills it:

| Field | Meaning |
| --- | --- |
| byte 0 | mode |
| byte 1 | destination override (property `0x131B`) |
| byte 2 | AF mode |
| word +4 | AF before release (only with property `0x1326`) |
| word +8 | stored at `0xA18B83B8+0x30` |
| +0xC, +0x10 | as upstream (frame count at +0x10) |

The module sends `{0,1,0,0, 0,0,1,1}`, the same values as upstream's
`{0x100,0,0,1,1}` and PTP's format-`0x3800` request. That means no AF.

On acceptance the callback goes into slot `0x38` of the table `0xA238BA48`
(`0x1005ED7C` fills only an empty slot). It is called with event
`0x04100034` ("done": word 0 = 0 on success; Nikon's event table at
`0x10649A80`).

The shutter switch bits are in Nikon's switch-name table (name, then mask,
in 40-byte entries): SW0 `0xA1F90AA4`, half `0x80000000`, full
`0x40000000`, vertical-grip half/full `0x20000000`/`0x10000000`.

Build `c813c457` (`--pixel-release`,
[LCD_PIXEL_RELEASE_TEST.md](LCD_PIXEL_RELEASE_TEST.md)):
1. arm;
2. wait until the button has been free for 0.5 s;
3. for each corner: hold, confirm, release, then wait for `0x04100034` and
   the new still record;
4. stop on any refusal, failure, timeout, busy slot or button touch;
5. recentre, restore D2, watch.

Checks: 20 offline, 48 static.

## Step 3b first camera run: the release works; three fixes (Nov 27)

`c813c457` armed at power-on, not on the photographer's half-press, because
stabilisation is already active and settled right after start-up.

- **The release worked.** It held position 0 (state `0x40`, target 0) and
  fired: `0x101ECFB0` returned 0. Nikon called back once, with event
  **`0x04100038`** and no argument. The still-file hook then counted a new
  record (key `0x3642780`).
- **The module stopped after one frame.** It waited only for `0x04100034`,
  so after 15 s it gave up on the frame.
- **The hold stayed on.** It recentred, but the release had replaced
  Nikon's D2 parameters, and the module took that as "Nikon already
  restored" and sent nothing. The hold (state `0x40`) stayed on for the
  full 30-second watch, until power-off.

Fixes in `a431a849`:
1. Arming also requires the shutter button half-pressed (SW0 bits
   `0xA0000000`).
2. `0x04100038` counts as done; the still record must still confirm the
   file.
3. If the D2 buffer changed, the module re-sends Nikon's latest parameters,
   as upstream re-snapshots before `restore_d2`.

`8dcee0e0`, `5fe15dcc`, `2ff19bde` and `b68284dc` still rebuild byte for
byte. 24 offline checks.

## Step 3b result: a module-fired four-frame series on the Z7 (Nov 27)

Build `3b2bb075` ran on a tripod and was restored. The series is complete:
102 requests, 0 refused, 0 timeouts.

- **Every frame went the same way.**
  - Position held and confirmed: state `0x40`, with the targets exactly
    `(0,0,0)`, `(-84,0,0)`, `(-84,-72,-72)` and `(0,-72,-72)`, measured
    within about 13 counts.
  - `0x101ECFB0` accepted the release.
  - Nikon reported `0x04100038`.
  - The still record followed: `DSC_8509`-`DSC_8512`, keys `0x36427A0` to
    `0x3642800`.
  - It armed on the half-press, about 42 s after power-on.
- **Image shift** (`tools/measure_z7_pixel_shift.py`, full-size NEF
  previews, 2048 and 1024 px windows):

| Frame | Command (x, y) | Image shift (px) |
| --- | --- | --- |
| 2 | (21, 0) | (-1.11, +0.02) |
| 3 | (21, 18) | (-1.67 to -1.73, -0.02) |
| 4 | (0, 18) | (-0.30 to -0.35, -0.03) |

  **X works:** 21 steps move the image about 1.1 px, so about 19 steps per
  pixel on the Z7 (the Z7II uses 21). **Y does not:** moving both
  "vertical" actuators equally (target `(0,-72,-72)`) gave no vertical shift,
  only a small horizontal one. The Z7's actuator geometry differs from the
  Z7II's. The vertical direction probably needs the two actuators moved
  differently, which upstream's payload `{0,x,0,y,0,16,16,0,0,2}` cannot
  express without further payload bytes.
- **The D2 re-send did not end the hold.** The module re-sent Nikon's last
  parameters (selection 1, 3, flags 3) with `0x101C63F8`. It was accepted
  and Nikon called back, but the state stayed `0x40` for the 30-second
  watch. Nikon's own VR-mode apply (`0x101C69D8`) sends flags `sel[1]|0x80`
  (or `|0xC0`) instead. Flags 3 appear to come from Nikon's variant
  `0x101C6A38`. The next restore attempt should use the apply form, or
  Nikon's own BodyVr event (bit 4, handler `0x101DF34C`).

**Next:** a geometry probe (one telemetry-checked frame per payload variant)
to find the Z7's vertical axis, and the restore variants above.

## Step 3c built: geometry probe and restore variants

[LCD_PIXEL_PROBE_TEST.md](LCD_PIXEL_PROBE_TEST.md), build `d6e6db28`
(`--pixel-probe`). It takes one module-fired frame per position-command
variant:
- reference;
- x = 19;
- y = 18;
- byte 4 = 18;
- y with bytes 5/6 = 24/8;
- bytes 2/3 = `FF EE`;
- bytes 0/1 = `FF ED`.

Each frame fires only if every target is within +-400 counts; otherwise the
module recentres at once and skips it.

Then it tries three ways to end the hold, stopping at the first that works:
1. D2 with flags `sel[1]|0x80`, as Nikon's apply `0x101C69D8` computes them
   (`0x101C69FE`);
2. BodyVr event bit 4, posted to task `0xA23826D0` with `0x1017088C`
   (dispatcher `0x101E09F2` -> handler `0x101DF34C`; the task's wait mask is
   `0x364FFFFF`);
3. `0x101C69D8` itself.

Checks: 17 offline, 54 static.

## Step 3c result: payload layout, restore found, y still uncertain (Nov 27)

Build `d6e6db28` ran and was restored. 252 requests, 0 refused, 0 timeouts.
4 of 7 variants were photographed (`DSC_8513`-`DSC_8516`); 3 were skipped by
the +-400 guard.

**Payload layout** (from the targets the stabiliser accepted):

| Bytes | Meaning |
| --- | --- |
| 1-2 | **x, little-endian int16** (`ED FF` = 237 -> target -948; `00 FF` = -256 -> +1024) |
| 3-4 | **y, little-endian int16** (`EE 00` = 238 -> -952 on both vertical actuators) |
| 4 = 18 | y = 4608, clamped at the end of travel (**about +-8180 counts**). This was the big movement the owner saw; it lasted under 100 ms before the guard recentred. |
| 0 | did not affect the targets |
| 5/6 (24/8 instead of 16/16) | did not change the targets; the two vertical actuators always get the same y |

So negative steps are `x = FF..` / `y = FF..` in little-endian. Upstream's
`{0,x,0,y,...}` only works for 0-255.

**Restore found.** Method 1 worked at once: Nikon's D2 sender `0x101C63F8`
with the apply flags `sel[1]|0x80` (selection 1, 3, flags `0x83`). The state
went `0x40` -> 1 (normal) within 100 ms and stayed normal. The earlier
re-send with flags 3 does not end the hold.

**Image shift**, measured with the refined tool (upsampled
cross-correlation, 1/50 px, verified on synthetic shifts to about 0.01 px):

| Run | Command | dx, dy (px) |
| --- | --- | --- |
| probe | x = 19 | -0.86, -0.02 |
| probe | y = 18 | 0.00, +0.48 |
| probe | y = 18, bytes 5/6 split | +0.02, +0.60 |
| series | x = 21 | -1.16, +0.02 |
| series | x = 21, y = 18 | -1.56, -0.04 |
| series | y = 18 | -0.28, -0.04 |

X is consistent at about 0.045-0.055 px per step (roughly 18-22 steps per
pixel). Y moved the image vertically in the probe but not in the series. With
correlation peaks of only 0.18-0.30 on the preview JPEGs, sub-pixel values
are not yet trustworthy.

**Next:** a calibration run with larger steps (2-4 px) for a better signal,
repeated reference frames to measure noise, a textured target, and the
working restore.

## Step 3d built: calibration run

[LCD_PIXEL_CALIB_TEST.md](LCD_PIXEL_CALIB_TEST.md), build `73567658`
(`--pixel-calib`). Nine module-fired frames in the measured little-endian
layout:

| Frame | Steps (x, y) |
| --- | --- |
| 1 | (0, 0) |
| 2 | (+80, 0) |
| 3 | (0, 0) |
| 4 | (-80, 0) |
| 5 | (0, +72) |
| 6 | (0, 0) |
| 7 | (0, -72) |
| 8 | (+40, +36) |
| 9 | (0, 0) |

All targets are within 320 counts. Then centre and the D2 apply restore.
The simulated stabiliser now decodes the camera-measured layout (clamped at
+-8180), and the probe audit reproduces the camera outcome (V3, V5 and V6
skipped). Checks: 7 calibration, 15 probe.

## Step 3d result: the Z7 step scale (Nov 27)

Build `73567658` ran and was restored. All 9 frames were module-fired
(`DSC_8517`-`DSC_8525`): 60 requests, 0 refused, 0 timeouts. Each was
held at its exact target before the release (x +-320, y +-288,
`(-160,-144,-144)`). The D2 apply restore (flags `sel[1]|0x80`) ended the
hold at once, the second time on the camera.

**Image shift** (refined tool, 2048 and 3072 px windows agree to 0.04 px).
Each frame is measured against its neighbouring references. The references
(frames 3, 6, 9) agree within about 0.4 px but sit about 2.3 px below
frame 1: the first frame, 0.5 s after the button was released, caught the
camera still settling. That likely explains why y looked horizontal in the
`3b2bb075` series.

| Steps (x, y) | Shift (px) | Steps per pixel |
| --- | --- | --- |
| (+80, 0) | (-3.72, -0.02) | x 21.5 |
| (-80, 0) | (+4.75, ~0) | x 16.8 |
| (0, +72) | (-0.04, +3.88) | y 18.6 |
| (0, -72) | (+0.01, -4.04) | y 17.8 |
| (+40, +36) | (-1.89, +1.98) | x 21, y 18 |

- **X:** about **20 steps per pixel** (mean of the three x measurements:
  4.08 px per 80). +x moves the image to the left.
- **Y:** about **18 steps per pixel** (3.96 px per 72). +y moves the image
  down. **Y works vertically.**
- **x and y are independent** (the diagonal adds up).

The Z7 matches upstream's Z7II scale (21/18) within the measurement spread.

**For the real series:**
1. Wait about 2 s after the button is released, then let each frame settle
   before releasing.
2. Corner steps: x = 20, y = 18.
3. Restore with the apply flags.
4. Merge on the computer, since in-camera merging and NX Studio tags are
   not ported.

## First real series built

[LCD_PIXEL_SHIFT_TEST.md](LCD_PIXEL_SHIFT_TEST.md), build `f4e46989`
(`--pixel-shift`, `Z7_PIXEL_SHIFT_V1`). It takes four module-fired frames
at the calibrated corners `(0,0)`, `(20,0)`, `(20,18)`, `(0,18)`:
1. A 2 s settle after the button is free (touching it cancels).
2. For each frame: confirm the position, wait 0.5 s, re-check it, release
   (a lost hold stops without a release).
3. One click per frame.
4. Recentre and the D2 apply restore (flags `sel[1]|0x80`).

10 offline checks. In-camera merge and NX Studio tags are not ported; the
set is merged on the computer.

## First real series result (Nov 27)

Build `f4e46989` ran on a tripod and was restored.

- **Mechanics: perfect.** 95 requests, 0 refused, 0 timeouts.
  - All four frames (`DSC_8526`-`DSC_8529`) were re-confirmed at the exact
    calibrated targets after the 0.5 s settle (`(0,0,0)`, `(-80,0,0)`,
    `(-80,-72,-72)`, `(0,-72,-72)`, measured within 8 counts) and released.
  - The D2 apply restore ended the hold at once, for the third time on the
    camera.
- **Image shift**, preview JPEGs, median of the 11 most-textured 768-px
  tiles:

| Frame | Expected (px) | Measured (px) |
| --- | --- | --- |
| 2 | (-1, 0) | (-0.78, +0.16) |
| 3 | (-1, +1) | (-1.64, +0.26) |
| 4 | (0, +1) | (-0.08, +0.20) |

  On the calibration run the same tile method gives a clean x-80 -> +4.64,
  y+72 -> +4.14, y-72 -> -3.74. So large steps are linear, but **18-step y
  moves have measured 0 to 0.6 px across three runs** instead of about 1,
  while 36 and 72 steps were proportional. Either the vertical actuators
  have a small dead zone, or one-pixel structure cannot be measured on the
  NEF's demosaiced preview. Correlation peaks are low (0.13-0.19), and the
  preview is demosaiced, which blurs exactly the colour-filter-scale detail
  pixel shift relies on.

**Next:** decode the raw Bayer data, and check each frame's shift on the
raw colour channels. That also gives the merge tool. If y really has a dead
zone, a larger step that lands on the next same-phase site (e.g. 3 px), or
an approach from a fixed direction, would be the fix.

## Raw analysis of the series (Nov 27)

With rawpy 0.28 (LibRaw 0.22) installed in the project environment,
`tools/measure_z7_raw_shift.py` measures each frame against the first on
the four raw colour planes separately. Each plane is uniformly sampled, so
there is no colour-filter mixing.

**Calibration run**, all planes agree within about 0.1 px:

| Steps | Shift (px) |
| --- | --- |
| x -80 | (+4.5, +0.2) |
| y +72 | (+0.05, +4.2) |
| y -72 | (+0.05, -3.9) |
| (+40, +36) | (-2.0, +2.2) |

**Series** (`f4e46989`, R/G/G2/B agree within about 0.1 px):

| Frame | Command vs frame 1 | Shift (px) |
| --- | --- | --- |
| 2 | x +20 | (-0.8, +0.6) |
| 3 | x +20, y +18 | (-1.4, +0.7) |
| 4 | y +18 | (-0.2, +0.65) |

Frame 1 is offset about 0.6 px vertically from frames 2-4. The
calibration's first frame was offset too (about 2.3 px), so the first
exposure still catches the body moving, despite the 2 s settle. Between
frames 2 and 3 (y +18 only), the vertical shift is **+0.06 px**, against 1
commanded. Between 3 and 4 (x -20) it is **+1.2 px** (expected 1).

**Small y steps barely move the image**, while 36- and 72-step y moves and
all x moves are proportional. The stabiliser's own telemetry reports every y
target reached (within 8 counts), so the loss looks mechanical: the vertical
actuators lifting the sensor against gravity, friction, or a dead zone.

Methods that did not work:
- 2x2-binned raw locks onto even shifts: an odd shift changes the colour mix
  inside each window.
- Lucas-Kanade on demosaiced images was too noisy on this scene (about
  1 px spread).

One-pixel values on single planes are half a plane sample, where planes are
aliased, so they are indicative only. The agreement across planes and
neighbouring frames is what supports the reading.

**Next experiment:** y-only steps of 18, 36 and 54 (both signs), each with a
reference before and after, plus an x 20 control, and a discarded first
frame. That measures the dead zone directly, and shows whether
approaching from one direction (or overshooting and coming back) restores
one-pixel y steps.

## Step 3e built: vertical dead-zone run

[LCD_PIXEL_DEADZONE_TEST.md](LCD_PIXEL_DEADZONE_TEST.md), build `615cf144`
(`--pixel-deadzone`). 20 module-fired frames, with a 2 s start settle and a
0.5 s settle per frame:
- a discarded first frame;
- y +18/+36/+54 and -18/-36, each between references;
- an x 20 control;
- y +18 reached from +54, and y -18 reached from -54.

All targets are within 216 counts. Then the D2 apply restore. 10 offline
checks.

## Step 3e result: y works; early frames drift, upward approach falls short (Nov 27)

Build `615cf144` ran and was restored. 20 module-fired frames
(`DSC_8530`-`DSC_8549`): 112 requests, 0 refused, 0 timeouts. Each frame
was held at its target. The apply restore worked (fourth time).

**Raw colour-plane positions** (`tools/measure_z7_raw_shift.py`; the four
planes agree within about 0.2-0.4 px):
- The references from frame 4 on (`DSC_8533` onwards) sit at y = -1.05
  +-0.15 px.
- Frames 1-2 (`DSC_8530`/`8531`), 2-3.5 s after the button was released,
  sit about **1 px** away. The body or tripod is still settling for about
  5 s after release. That explains the earlier "y does not move" readings:
  the drift masked or mimicked the one-pixel y step in `3b2bb075` and
  `f4e46989`.

**Each move against its stable neighbouring references:**

| Move | Measured (px) | Expected (px) |
| --- | --- | --- |
| y -18 | -1.03 | -1 |
| y -36 | -2.04 | -2 |
| y -54 | -3.01 | -3 |
| y +18, reached from +54 | +0.95 | +1 |
| y -18, reached from -54 | -1.01 | -1 |
| x +20 | -1.11 | -1 |
| y +36, from 0 | +1.65 | +2 |
| y +54, from 0 (twice) | +2.69, +2.72 | +3 |

- **Y is linear at 18 steps per pixel.**
- Upward moves (+y) from 0 fall short by about 0.3 px; the same target
  approached from above is exact.
- The zero position differs by about 0.15 px between arriving from above
  (-0.95) and from below (-1.12).

**For the series:**
1. Settle about 6-8 s after the button is released, or discard the first
   frames.
2. Approach every y target from the same side (from above: overshoot to
   +36 first). This removes the 0.3 px upward shortfall.
3. Keep x 20 / y 18.

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
