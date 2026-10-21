# Tests and acceptance boundaries

## Firmware-free public checks

Run `sh tests/run.sh` on the prepared Linux host. This export passed:

| Check | Result | Scope |
| --- | --- | --- |
| Python unit tests | 11 passed | RAW input validation, CFA channel selection, levels, little-endian storage and padding |
| C renderer contracts | 270 passed | Synthetic path formats, fills, YUV storage, chroma, transparent source-over, strokes, caps, joins and bounds |
| C ISP contracts | 398 passed | Synthetic black/white RAW, padding, invalid dimensions, cache invalidation and recomputation |
| ASan / UBSan | No diagnostics in the above C runs | Host pixel modules in those cases |
| Cold QEMU 10.2.4 build | Passed locally | Integration, compiler and linkage |
| Firmware-free QMP smoke | Passed locally | Display machine realization, status query and clean quit |
| Public launcher with local BYO firmware | 21 checks passed | Synthetic scene, RAW/ISP/LCD, pause/resume and three MENU roundtrips in one session |

The copied native icon fixtures and private RAW/output oracle were removed.
These synthetic checks do not establish pixel equivalence for every camera icon
or Nikon ISP behavior. ASan/UBSan here do not instrument the entire QEMU guest.

Public CI checks the reviewed inventory and reachable history, runs these
contracts, builds QEMU, confirms machine registration and generates synthetic
CMOS files. It uses no Nikon firmware and uploads no runtime artifacts. A green
CI result therefore does not certify original-camera boot or shooting UI.

## Local firmware-dependent verification

After starting a local `--photo-liveview` session with your own compatible MAIN:

```sh
python3 tools/verify_ui.py --url http://127.0.0.1:8787 --menu
```

Use a new `--output DIRECTORY` for a repeated run; earlier evidence is preserved.
Output defaults to `.local/ui-verification/`. The verifier checks input geometry,
actual RAW transfers, ISP completion, native processed-buffer scanout, scene
detail, red no-card pixels, pause/resume stability and continued processing.
It sends three native MENU roundtrips, checks scene-region recovery and confirms
the same session remains running. These screenshots and raw states stay local.

The scene comparison excludes parts of the UI that can change. A scene match
does not prove all overlays or arbitrary menu paths. Numeric ISO/shutter and
outlined text/icons need visual inspection of the actual guest screenshot;
the host does not synthesize them. In the local export verification, the final
native screenshot showed `1/30`, `ISO AUTO 3200`, black text/icon outlines and
the red no-card indicator over the generated color bars/ramp. The screenshot
and firmware-dependent result remain local and are not shipped. This document
does not pretend that visual inspection runs in public CI.

## What to record

Record source/build and firmware fingerprints, assistance profile, input layout,
initial/final session identity, actual transfer/processing/scanout observations,
menu cycles, failure/unknown-access information and untested behavior. Include
the specific negative or invalid cases relevant to a device change.

Do not equate accepted key actions with successful shooting. No physical CMOS
protocol, AF/PDAF, MVD, recording, hardware add-on loading or flash acceptance
is certified by this test. The board has no complete VMState snapshot support.
