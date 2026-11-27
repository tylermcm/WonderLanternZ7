# Pixel shift on the original Nikon Z7 — it works*

**November 27, 2026. Source update; no firmware or module binary is
distributed.** Read the [risk notice](RISK_NOTICE.md) before trying anything.

Nikon brought pixel shift to newer bodies such as the Z8, Z9 and Zf, but never
to the original Z7. (The Z7 II only has it through JKWTCN's community
extensions.) Nikon Z7 Extensions now takes a real
**four-shot pixel-shift series on an original Z7 (firmware C 3.80)**, and a
computer-side merge turns the four raw files into a full-colour image with
no demosaicing.

\* *Experimental. It works on the project owner's camera under controlled
conditions. See [What "works" means](#what-works-means) below.*

## What works

- **Sensor control.** An SD-card module drives the Z7's in-body
  stabilisation (VR/IBIS) through Nikon's own BodyVr command service. It
  moves the image sensor in precise one-pixel steps, holds it there, and
  reads back telemetry to confirm each position.
- **Module-fired exposures.** For each position the module fires the
  shutter itself through Nikon's own capture call, the one remote and USB
  shooting use, and waits for Nikon's "capture done" signal and the new
  file. There is no half-press between shots. A half-press makes the camera
  re-enable normal stabilisation and spoils the shift.
- **Measured accuracy.** All four shots of the latest series landed within
  **0.15 px** of their targets: (0,0), (1,0), (1,1) and (0,1) pixels,
  measured on the raw colour planes of the NEFs.
- **Calibrated on the Z7.** About **20 sensor steps per pixel horizontally
  and 18 vertically**, with independent axes, close to upstream's Z7 II values (21/18).
  The camera needs about 5 s to settle after the button is released, and
  vertical targets are exact when approached from above. The module handles
  both.
- **Stabilisation is restored afterwards** with Nikon's own VR parameters,
  confirmed on five camera runs.
- **Computer merge.** [`tools/merge_z7_pixel_shift.py`](tools/merge_z7_pixel_shift.py)
  combines the four raw frames, so each pixel gets one red, two green and one
  blue sample. Compared with a single shot of the same scene, fine printed
  halftone is resolved with far less false-colour speckle, and smooth areas
  have visibly less colour noise.

## How it was built

A series of small, reversible steps, each tested offline, then on the camera
only with the owner's approval:

1. read-only VR telemetry probe;
2. one tiny sensor move and back;
3. finding Nikon's stabilisation restore;
4. a module-fired release;
5. a probe of the position-command layout (x and y are little-endian 16-bit
   values);
6. a nine-shot calibration;
7. a 20-shot vertical dead-zone run;
8. the corrected four-shot series.

Each module was checked against a simulated stabiliser and shutter (5 to 27
checks per build), the 277-check display suite, and a boot of Nikon's menus
in an emulator. Every camera-run build still rebuilds byte for byte.

The full measurement history, including what didn't work, is in
[PIXEL_SHIFT_RESEARCH.md](PIXEL_SHIFT_RESEARCH.md). Per-run evidence is in
[`evidence/`](evidence) (files named `20261126-*` and `20261127-*`).

## What "works" means

- **One clean run so far** with every fix in place. More runs on different
  subjects and light are needed before calling it reliable.
- **Not a menu feature yet.** It exists as a test build that runs once per
  power-on after a half-press. There is no pixel-shift menu option yet.
- **Merge on the computer only.** There is no in-camera merge, and NX Studio
  does not recognise the files as a pixel-shift set.
- **Small merge artefact.** A faint vertical striping shows in bright flat
  areas, from about 0.1 px residual misalignment. Sub-pixel registration is
  the next refinement.
- **Strict conditions.** Tripod, Silent photography, single frame, M mode,
  manual focus, a still subject, steady light. Anything that moves between
  the four shots ruins the merge, as on every pixel-shift camera.
- **One camera.** Tested on the owner's original Z7 (C 3.80, without the
  paid RAW-video upgrade). Other bodies, firmware versions and the Z7 II are
  not supported by these modules.

## Also new since the last update

These are working on the owner's camera inside the everyday LCD module:

- **Shutter sound in Silent photography**, with volume OFF/1–9 and a
  `SHUTTER` folder of up to ten selectable sounds.
- **Upside-down photos.** They are saved with the correct EXIF orientation
  and shown the right way up in in-camera playback.

**AF-area buttons** are built and pass offline and emulator checks, but are
not yet camera-tested. They give Fn1, Fn2, AF-ON, the sub-selector centre and
the movie button a one-press AF-area mode.

## Credit

The design follows [JKWTCN's MIT Z7 II extensions](https://github.com/JKWTCN/z7ii-extensions),
including its pixel-shift approach. All original-Z7 bindings, the
calibration and the merge tool are independent work. See
[CREDITS.md](CREDITS.md).
