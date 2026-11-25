# Native Information DISP page trial — November 24, 2026

This independent original-Z7 checkpoint adds **Information display** to the
Display settings root menu as an optional fifth page in the photo LCD DISP cycle.
It uses Nikon's native information application and rendering. The four custom
presets, histogram switches and optional movie battery work remain included.
Information display defaults OFF. The startup grid transition remains deferred.

## Exact candidate

- Private `Z7APP.BIN`: 26,040 bytes, SHA256
  `cec4c39bdda98fb5269bb87cb6cd15961bc78e6eca464b6a39f78477cf3f62c5`.
- Build: `tools/build_z7_lcd_volatile.py --information-page`.
- Original Z7 C 3.80 without the paid RAW upgrade, photo mode, rear LCD.
- Existing installed host supplies the native information-cycle API. No host
  change or firmware update is required.
- The preceding movie-battery profile still builds to its exact `cc9d6b39...`
  packet when this optional feature is disabled.
- No card files changed. This candidate has not been camera-tested or staged.

The root menu now has seven rows: Custom pages, Standard, Minimal, Composition,
Exposure, Information display and Battery percentage. The last two switches are
independent. Information display may be the only enabled page; the last enabled
page cannot be disabled. Switching the master OFF restores the native cycle.

Existing native routing releases custom masks, base-page ownership and pending
overlay painters before requesting the native information application. It waits
for the native application transition rather than assigning an application or
framebuffer directly. Exit uses the existing native admitted DISP path. Busy,
menu and conflicting-ownership conditions retain their existing guards.

## Settings and rollback

The version-3 display journals already define the fifth-page bit. This profile
preserves it rather than filtering it out. There is no storage migration or new
filename. `Z7DSP0.DAT` / `Z7DSP1.DAT` retain alternating writes; legacy `Z7CFG`
files remain read-only fallback. An older module filters the unsupported fifth
page, falling back to Standard when Information was the sole enabled page.
Subsequent older-module saves may discard the fifth-page and histogram choices;
retain the original journal backup.

## Validation limits

The candidate builds reproducibly. The audit tooling executes native DISP
admission and exit instructions, compiled routing/menu/codec/worker logic and
native file wrappers. Native app initialization, incoming GUI state, property
services, file contents, telemetry and selected drawing/presentation boundaries
remain supplied. Completed checks:

- 54 native routing checks, including admitted entry/exit, mask restoration,
  overlay retirement, native busy gates, sole-page mode and old-API rejection.
- 57 menu/storage checks with three alternating saves and four cold loads;
  independent battery row, last-page protection, retained legacy files and
  rollback to the preceding `cc9d6b39...` module's Standard fallback.
- 12 QEMU native-key menu checks and four private frames. The combined ON
  frame was visually inspected; all seven rows and both switches are visible.
- 103 root unit tests pass.

See [the source-only checkpoint record](evidence/20261124-lcd-information.json).

QEMU menu evidence is separate from live Information display appearance. A
previous native-control experiment already reproduced mirrored information text
in the emulator; this checkpoint does not repair or hide that rendering issue.
Routing checks do not establish physical image orientation, camera startup,
sleep/wake, all output modes, recording behavior or recovery. The included
[histogram](LCD_HISTOGRAM_PRESETS_REVIEW.md) and
[movie battery](LCD_MOVIE_BATTERY_REVIEW.md) features retain their hardware limits.

The page/component concept follows the credited MIT
[JKWTCN custom DISP feature](https://github.com/JKWTCN/z7ii-extensions/blob/main/docs/custom-disp.md).
Original-Z7 bindings, integration and validation are independent work. Upstream
hardware reports are not original-Z7 verification.

## Proposed installation and recovery assessment

Any staging needs owner authorization and a connected, re-identified card.
Preserve its current module, all four configuration journals, existing disabled
modules and photos. Stage only the exact reviewed packet, verify readback, flush
and safely eject. Expected current card module is `5e62ce53...`, subject to actual
inspection. Retain camera-tested rollback
`f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`.
Do not select Firmware update.

A combined observation can enable Information display with Custom pages ON,
cycle into and out of it, check native text orientation and normal controls,
then check MENU return and ordinary power-off after Saved. There is no need to
test every enabled-page combination or revisit startup grid cosmetics. Movie
battery and live histogram verification are additional observations only if
the owner elects to test this cumulative candidate.

On freeze or abnormal behavior, stop instead of repeating the test. Prior card
or battery removal recovered earlier failures; recovery from this exact packet
has not been physically verified or guaranteed. Preserve the failed packet and
journals, inspect the card and restore the working SD module without another
firmware update. Emergency firmware recovery remains unverified.
