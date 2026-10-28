# Original Z7 clean shooting display research

## Scope and result, October 27, 2026

The owner wants only the live image and composition grid, including removal of
the bottom shutter/aperture/ISO/metering/card information. This is separate from
the spiral color/display correction. No clean-display firmware patch or camera
trial has been prepared.

In assisted QEMU, diagnostic changes to the original Z7's shooting-widget
visibility masks remove the top and bottom readouts in simplified DISP mode,
while the live scene and native 3x3 grid remain. Two empty card-count brackets
still appear at bottom right. They survive a native MENU clear and return, so
the result does not yet meet the requested completely clean display.

## Native structures and reversible experiment

The native binding table at `0x1064D610` contains 61 descriptor pointers. The
original walker compares against `0x3D`; these are not inferred from another
model. Each descriptor has nine 32-bit visibility masks at `+4`. Clearing
`0x22222` in each of those masks, then cycling DISP back to mode 1, hides the
ordinary shooting widgets in the assisted LCD fixture. The 2,196 original mask
bytes were saved and restored exactly. A final resumed capture shows normal
readouts again.

These are emulator RAM fixtures, not edits to firmware code, settings storage,
pixel buffers or camera memory. The host supplies diagnostic native calls and
DISP/MENU key inputs. QEMU's camera/controller inputs are assisted, as in the
grid experiments. Generated screenshots, raw structures and logs remain private
under `.private/research/display/20261027-clean-mask-03/`.

Additional negative experiments:

- Zeroing all nine masks does not remove the remaining brackets.
- Original component permission function `0x103FB5BE(1, 0, 0)` returns success,
  but does not maintain the desired hidden UI after normal tasks resume.
- Original bitmap fill `0x103FAE10(buffer, 720, 480, 0)` on native component 0
  (`0xB0B09600`) and component 2 (`0xB0FB9600`) does not remove those brackets
  from the resumed screenshot. These calls do not establish ownership of them.

The next step is to trace the card-count bracket painter and its own visibility
conditions, then design an explicit setting with restoration on DISP/MENU,
playback, warnings, capture and wake. The main UI bitmap also hosts the spiral;
hiding that entire bitmap would hide the curve too. Combining a clean display
with the spiral is not yet tested.

## Display routing relevant to the spiral

Original descriptor getter `0x10433B80(kind, display_id, dataset)` accepts LCD
1, external 2 and EVF 4. Component **1**, dataset 0 is the relevant UI surface:
LCD is 720x480; EVF is 1280x960. The bitmap address is at `+0x24`, packed shape
at `+8`, format selector at `+0x34`. Component 0 is a different 720x480 plane
and cannot be used to infer the main EVF drawing size.

The current LCD registry has a 720x480 entry at `0xB045F200`; the inactive EVF
descriptor uses the same address with a different shape. A display-aware helper
must require an exact existing active registry entry for the selected native
descriptor and size. The new spiral helper refuses a mismatch instead of
assuming the LCD registry is suitable for EVF. Native descriptor inspection and
supplied routing are not evidence of a physical eye-sensor transition or EVF
scanout.
