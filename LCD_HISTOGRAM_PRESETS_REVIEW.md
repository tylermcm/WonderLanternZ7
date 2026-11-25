# LCD histogram DISP preset trial — November 24, 2026

This independent original-Z7 checkpoint adds an optional **Histogram** control
to each of the four saved LCD DISP presets. Histogram, virtual horizon and
framing grid can be enabled together. Histogram defaults remain OFF. The brief
3x3 grid visible during cold startup is deferred at the owner's request.

## Exact candidate and scope

- Private `Z7APP.BIN`: 22,712 bytes, SHA256
  `f97ba8b4e927ba9b2f85b3d4fc0d073de61873eccdb1889da36b5a38902ad79c`.
- Build: `tools/build_z7_lcd_volatile.py --histogram-presets`.
- Expected current card module: `5e62ce53def1a8de4cf789bb4f3b03fb51791943501a11da6ca4be44b4e77349`.
- Camera-tested rollback: `f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`.
- Original Z7 C 3.80, without the paid RAW upgrade; photo mode, rear LCD,
  Custom pages ON. EVF, movie and external-output histogram are outside scope.
- Existing installed module host is sufficient. **No firmware update is needed.**
  The optional host read-retry experiment is excluded from this trial.

The preset submenu has Page enabled, Shooting information, Framing grid,
Histogram, Virtual horizon and Reset preset. The implementation exposes the
existing original-Z7 native histogram integration; it retains native readiness,
GUI/output/busy guards and a 100 ms refresh throttle. Menu and file operations
remain outside the native histogram painter. See the credited upstream
[histogram/horizon documentation](https://github.com/JKWTCN/z7ii-extensions/blob/main/docs/histogram-horizon.md)
for the related Z7II feature; that camera's results do not establish Z7 support.

## Preferences and rollback

The existing version-3 `Z7DSP0.DAT` / `Z7DSP1.DAT` journals already define the
histogram component bit. No storage migration or new filenames are needed.
Legacy `Z7CFG0.DAT` / `Z7CFG1.DAT` remain a read-only fallback. The older rollback
module strips unsupported histogram bits before GUI readiness, retaining other
settings. A subsequent save with that older module can discard histogram
choices; preserve the original journals privately before staging.

## Validation completed

- Reproducible candidate build; the preceding label profile still rebuilds
  byte-for-byte to the current card module with histogram presets disabled.
- 170 native histogram audit checks: native renderer calls and guarded failure,
  transition and cleanup paths. Statistics samples, submit/present and low-level
  drawing boundaries are supplied by the fixture.
- 96 saved-preset checks: four preset reloads, five alternating saves, separate
  histogram/horizon toggles, reset mapping, other settings and legacy files
  preserved, no GUI file I/O, and the exact older rollback's component filter.
- 12 QEMU native-key menu checks with four private frames: both Histogram ON
  and Virtual horizon ON remain selected together after reopening the preset.
- 103 root unit tests pass. Baseline and optional-host validation independently
  rebuild their respective candidates; neither host was installed this turn.

These checks establish menu, storage and bounded renderer behavior with supplied
service boundaries. They do **not** establish camera statistics, live histogram
pixels, responsiveness under camera load, update acceptance or recovery.
The histogram candidate has not been staged or camera-tested.

## Proposed SD-only hardware trial

Staging needs separate owner authorization. Identify the card, back up its
current module and all four preference files, and preserve existing root files,
photos and disabled modules. Keep the known working rollback. Stage only the
exact candidate above, verify readback, flush and safely eject. Do not select
Firmware update.

One combined feature test is sufficient for this checkpoint: with Custom pages
ON, enable histogram, grid and horizon in one LCD preset. In photo live view,
check that the histogram responds to scene brightness while horizon, controls,
MENU and playback remain responsive. Wait for Saved before normal power-off.
There is no per-setting reboot matrix or startup-grid investigation in this
trial. This limited test does not establish all camera modes or configurations.

If controls freeze or responsiveness degrades, stop the trial. Card removal and
battery removal restored earlier failures, but recovery from this exact
candidate has not been physically verified or guaranteed. Preserve the failed
candidate and journals, inspect the card, and restore the known working SD
module without another firmware update. Emergency firmware recovery remains
unverified.
