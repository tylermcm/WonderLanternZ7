# Merging Z7 pixel-shift photos

The merge tool reads the original NEFs and writes its results to a separate
folder. Keep the originals. It does not change camera files or settings.
Install `rawpy`, `numpy` and `Pillow` in the Python environment used to run it.

```powershell
.venv\Scripts\python.exe tools/merge_z7_pixel_shift.py `
  PRIVATE/DSC_8550.NEF PRIVATE/DSC_8551.NEF PRIVATE/DSC_8552.NEF PRIVATE/DSC_8553.NEF `
  --output .private/merge-example
```

Pass one complete series in capture order: 4, 8, 16 or 32 photos. Paths above are
examples. Position measurement runs on the raw colour planes. If those
measurements are already saved, reuse them with `--shift-report report.json`;
the filenames and order must match. `--shifts` accepts explicit fractional
image shifts for every photo after the reference, separated by semicolons.

Four shots produce an 8256 x 5504 RGB image for the original Z7's normal FX
crop. Each pixel combines one red, two green and one blue sample. The first
frame is also converted by LibRaw as a reference. The output includes
`merged.tif`, `single.tif`, comparison crops and `merge.json`.

Eight shots repeat the four positions and average two sets, keeping the same
8256 x 5504 dimensions. A synthetic end-to-end export verifies that repeating
an identical four-shot set leaves the merged samples unchanged within one
16-bit output level. Real eight-shot capture still needs a camera trial.

## The striping fix

The first merge rounded measured shifts to whole pixels and interlaced the
frames without matching their brightness. On DSC_8550–8553, the brightness
differences also vary across the frame. This creates alternating bright and
dark colour phases. Residual position errors alone did not explain or remove
the visible stripes.

The revised tool:

- corrects fractional position errors within each same-colour plane;
- estimates illumination ratios from large same-colour patches, then smooths
  those ratios before applying a spatial correction;
- uses the camera's FX crop and a common colour/tone pipeline for comparison;
- rejects incomplete phase coverage and excessive position errors instead of
  silently rounding a bad capture into a supposed pixel-shift set.

The original four NEFs were reprocessed privately on November 27, 2026. The
visible stripes in the inspected smooth-background crop were removed. The
range of the four phase means in that fixed crop fell from 0.0330 to 0.0040
in red, 0.0119 to 0.0040 in green, and 0.0272 to 0.0082 in blue, on a 0–1
rendered scale. This is one crop in one scene, not a general image-quality
score. The lighting mechanism was not measured; flickering light during a
rolling-shutter exposure is a possible explanation for the spatial variation.

Local matching is the default. `--photometric match` uses only global colour
ratios; `--photometric none` disables illumination matching.
`--alignment integer` retains integer-only alignment for a four-shot control.
Fractional correction resamples a colour plane; it does not promise recovery
of aliased detail or eliminate scene motion, clipping, colour moire or
misregistration. Use a tripod, a static subject and steady light.

## Experimental 16 and 32 shots

The [Nikon-style menu candidate](LCD_PIXEL_NIKON_MENU_TEST.md) places four Bayer corners at each
of four half-pixel offsets. Sixteen shots can therefore fill a doubled RGB
lattice, **16512 x 11008** after the FX crop. Thirty-two shots repeat those
sixteen positions and average both samples; the dimensions stay the same.

The merger accepts these counts, checks all sixteen colour phases, accumulates
on disk, and streams a 16-bit TIFF. Allow several GB of temporary/output disk
space. It also writes a native-resolution single-frame reference and a preview.
The TIFF is an RGB export, not an NEFX or an NX Studio pixel-shift group.

Synthetic 16/32-shot tests recover the intended full-colour lattice, and a
synthetic end-to-end 16-shot export checks TIFF dimensions and Windows file
cleanup. **No real Z7 16/32-shot set has been captured or merged yet.** The
half-step calibration and resulting image quality still require camera tests.

Design follows JKWTCN's MIT Z7 II pixel-shift work. The original-Z7 bindings,
illumination matching, registration and computer merge are independent work.
