# Capture callback correction — October 21, 2026

Follow-up: the owner followed this candidate's installation/test instructions,
reported no audio and read Silent mode required after the silent photo. The
trigger is now reached but still checks the old Z30 mode key. See
[SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md) for the verified Z7 property
and minimal correction. This document preserves the prior callback investigation.

The owner reports the diagnostic heading stays **Waiting for capture** after a
silent photo. With custom sound still enabled, one mechanical photo changes the
heading to **Silent mode required**. This supports a working late hook and mode
gate during mechanical capture, while neither late-hook diagnostic is observed
during silent capture. The unique headings support the diagnostic build running;
there is no firmware readback or independently observed updater completion.

The distinction locates the remaining investigation in capture-event coverage.
It does not identify a WAV parsing/volume problem. A counter reset or an unobserved
callback cannot be excluded beyond the owner's stated test sequence.

## Native path missed by the previous diagnostic

The original controller has a normal callback at `0x100726AC`, separate from both
paths converging at `0x1007272E`. The former passes event `0x04190001`; the latter
handles the late `0x04190004` event and an alternate `0x04190001` path. The prior
diagnostic only hooked the latter site. Therefore the normal callback can run
with no sound and leave the diagnostic at Waiting for capture.

Static callback registration was followed through `0x100752DE`, its caller at
`0x10147BBE` and the native consumer at `0x1014708C`. Native dispatcher execution
now covers `0x100725A0` and both normal controller states, not just calls to the
private trigger. Physical silent-mode reachability and precise exposure timing
remain to be verified on the camera.

## Independent correction

Hook the normal callback's argument setup at `0x100726A8` with a checked nearby
veneer. Reconstruct the original arguments, call Nikon's callback exactly once,
then attempt custom audio for the normal `0x04190001` notification. Restore the
callback's returned registers/flags and resume at the original `CMP R6,#0`.
Keeping that instruction intact preserves the native null-callback branch target.

The late hook remains as a diagnostic only; it no longer requests audio. This
avoids playing twice if both normal and completion notifications arrive. The
alternate late path also remains diagnostic-only. The photo/silent, enabled,
loaded-file and busy checks remain. No audio is queued for a missing native
callback, absent private state or a disabled custom feature.

The six existing diagnostic headings remain. A seventh, **Completion callback
seen**, distinguishes a late completion without a prior normal-trigger status.
Errors and a prior trigger status take precedence over that passive diagnostic.

## Candidate and validation

Private build/review suffix: `20261021-capture-start-02`. Full `EG161080.BIN`:
33,065,322 bytes, SHA-256
`efcfbda40439354e8707a2c1e8c0b16b5e47a27c0fe8999110ca98eb9f15dc1c`.
Version remains `03.80.00`. The candidate was staged as E:\EG161080.BIN on the
re-verified Sony QD-G240F card at 2026-10-22 04:10 UTC (October 21 locally).
Complete SHA-256 readback matched the candidate above. The previous card EG was
backed up privately; SHUTTER.WAV and all other card files were preserved. The
review bundle's card-staging.json records staging. Installation remains pending.
The audio-working and previous diagnostic candidates remain preserved privately.

All four presets rebuild reproducibly with valid CRCs. Sixteen existing firmware
tests pass without skips. Both sound presets pass 18 playback checks and 48
capture/diagnostic checks, alongside the existing config/route/data/menu contracts.
The capture checks compare all three original callback paths against stock and
run the original dispatcher in states 0, 2 and 4; they verify native callback
arguments, caller state, absent/disabled/null behavior, mode/busy gates, all seven
title bindings and no duplicate sound from a following late completion.

The previous installed diagnostic fails the new normal-capture queue checks while
still preserving that native callback. Changes to which notification queues audio
and the new seventh heading are new requirements, not additional independent
control-flow defects. An initial offline relocation attempt failed the null-
callback branch comparisons; the argument-setup site above fixes that before any
card or camera write.

The candidate also passes 13 admission/corruption checks, 12 private review
checks and full readback of the three private bundle files. Its first isolated
assisted-QEMU run passes all 17 sound-menu checks, with 30 native key events,
return to progressing live view and no observed abort. This validates menu
regression scope, not physical electronic exposure or speaker scheduling.

Properties, controller helpers, semaphore, callbacks and queue boundaries in the
instruction tests are controlled. These tests do not prove sensor exposure,
hardware callback reachability, cue timing, audible shutter sound or recovery.
Final package and assisted-QEMU results are recorded in
`evidence/20261021-capture-start-fix.json`. Use
[FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md) before any new installation.
