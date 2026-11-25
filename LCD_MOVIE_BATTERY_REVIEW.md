# Movie LCD battery percentage checkpoint — November 24, 2026

This optional independent original-Z7 profile extends the existing global
Battery percentage switch to movie LCD contexts with a matching native battery
icon. It includes the preceding histogram DISP preset work, while the earlier
histogram-only candidate remains available separately. The brief startup grid
transition remains deferred.

## Candidate

- Build with `tools/build_z7_lcd_volatile.py --movie-battery`.
- Private `Z7APP.BIN`: 22,712 bytes, SHA256
  `cc9d6b395e148b943af550cd31be8c9b1ca4de944ee260edc6fdeef0176dd830`.
- Target: original Z7 C 3.80 without the paid RAW upgrade, rear LCD.
- Uses the installed host; no firmware update or new host hooks required.
- Same global switch, default OFF; same preference format and filenames.
- No card files changed and no camera installation authorized by this review.

The implementation accepts the known photo/movie mode values rather than only
photo. All existing icon visibility, geometry, painter, palette, font, pool,
label ownership, adapter, bar-fallback, menu and output guards remain. It does
not force an icon visible or change its native callback. An unexpected movie
layout is excluded instead of receiving a guessed overlay position. Histogram,
custom DISP, focal and other information overlays retain their photo-only guards.

The feature follows the related upstream
[movie LCD battery behavior](https://github.com/JKWTCN/z7ii-extensions/blob/main/docs/battery-percent.md).
Existing JKWTCN drawing credit and MIT notices are retained. This change uses
independent original-Z7 bindings; it does not copy Z7II addresses or binaries.

## Checks and limits

The candidate builds reproducibly. Building with the preceding
`--histogram-presets` option still produces the exact `f97ba8b4...` packet.
The 47-check movie battery audit executes the compiled integrated module,
native getter and object helpers with supplied GUI, icon, mode, telemetry,
filesystem and selected drawing boundaries. It covers the global menu switch,
photo/movie transitions without extra object allocation, sample cadence,
disable/retirement and nine excluded contexts. The prior profile continues to
reject movie mode in the same fixture. GUI transitions perform no file writes.
The root suite passes 103 tests.

The exact new candidate also passes the 170-check native histogram renderer
audit, with statistics, presentation and low-level drawing boundaries supplied.
This checks that the added battery admission has not broken that existing path;
it does not establish a live movie histogram.

These are instruction-level contracts, **not a native movie HUD capture**.
The real movie icon geometry, percentage visibility in standby/recording,
recording scheduler load, output transitions, physical telemetry and pixels
remain unverified. No QEMU movie frame or camera recording is claimed.
The preceding histogram candidate's menu/storage results are documented in its
[separate assessment](LCD_HISTOGRAM_PRESETS_REVIEW.md); they do not establish
movie behavior.

## Installation and recovery assessment

This is an experimental SD-module candidate, not a firmware update. Before any
owner-authorized staging, re-identify the card, privately preserve the current
module and all four configuration journals, retain every existing disabled
module and photo, and verify exact candidate readback before safe ejection.
Expected current module is `5e62ce53...`; the known working rollback is
`f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`.
Neither value should be assumed without checking the connected card.

The first hardware observation should establish movie LCD layout and standby
responsiveness. Only after that passes should a short ordinary recording check
percentage visibility and normal stop/playback. One photo return checks the
original battery overlay; there is no exhaustive settings matrix or startup
grid retest. Wait for Saved before normal shutdown. Do not select Firmware update.

On freeze or abnormal recording behavior, stop instead of repeating the test.
Earlier card/battery removal recovered prior failures, but recovery from this
exact candidate is unverified. Preserve the candidate and settings, inspect the
card and restore the known working module without a firmware update. Physical
emergency firmware recovery remains unverified. Older modules can discard the
new histogram selections when saving, so retain the original journal backup.
