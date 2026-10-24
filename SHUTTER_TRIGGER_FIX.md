# Capture-trigger investigation — October 21, 2026

Follow-up: the owner reports Waiting for capture after a silent photo and Silent
mode required after a mechanical photo. This supports this diagnostic build
running, inferred without readback. The late hook is reached in mechanical mode,
while a separate normal callback was outside this diagnostic's coverage. The
new correction and candidate are in [CAPTURE_START_FIX.md](CAPTURE_START_FIX.md).
The remaining sections preserve the earlier late-hook design and its scope.

The owner reports audible WAV playback now works, but taking a photo does not
play the replacement sound. The owner confirmed Enabled ON, SHUTTER.WAV selected
and Nikon Silent photography ON during the failed capture test. Treat Preview
playback as passed by owner report and shutter-triggered playback as failed.

## Reproduced hook defect

The previous patch replaces eight bytes starting at `0x10072728`. A second native
path branches directly to `0x1007272E`, the original shared `BLX R2` instruction.
That target lies inside the patched jump's address literal. Executing this path
against the installed audio-fix image fails to call Nikon's callback, including
with the custom feature disabled or its state absent. The old tests called the
private trigger directly, so they did not cover this native branch.

The correction restores the original argument setup and hooks the shared
callback/epilogue pair at `0x1007272E`. A checked adjacent 16-byte veneer reaches
the appended routine. The original callback runs once with its native arguments;
its returned registers, flags and caller stack are preserved. Only the existing
`0x04190004` event attempts custom audio. The alternate `0x04190001` event retains
its native behavior and records that a callback was seen, without playing audio.
The correction does not expand audio to every callback or remove mode/busy gates.

This is a demonstrated control-flow defect. Its role in the owner's missing
shutter cue is still unknown: no real electronic-shutter event trace is available.

## Diagnostic title for the next camera test

With Enabled ON and no file/audio error, the sound page title now shows:

| Title | Meaning |
| --- | --- |
| Waiting for capture | No relevant callback recorded since enabling |
| Capture callback seen | Alternate native callback arrived, without a completion-trigger attempt |
| Photo mode required | Completion reached the trigger, but the photo/video property blocked it |
| Silent mode required | Completion reached the trigger, but the silent-mode property blocked it |
| Capture audio busy | Loading, another custom request or native audio blocked immediate admission |
| Capture sound queued | Completion passed the gates and attempted to queue custom playback |

Existing file/queue/audio error titles take precedence. Selecting Enabled ON
resets this status. Preview does not supply capture-event evidence. The titles
describe controlled code branches, not proof of physical scheduling or sound.

## Private candidate and checks

Build/review suffix: `20261021-shot-fix-01`. Independent modified full EG:
33,065,098 bytes, SHA-256
`51dd7feb01e991d0cbce93e952ac42be98981dca510187e2767141ec8974dd9b`.
Version remains `03.80.00`. Previously installed images and original firmware
are preserved privately. This build was staged as E:\EG161080.BIN on the verified
Sony QD-G240F card at 2026-10-22 03:39 UTC (October 21 locally). Complete SHA-256
readback matched the candidate above. The old card firmware was backed up;
SHUTTER.WAV and all other card files were preserved. Installation and a physical
capture-sound result remain pending. The private review bundle's card-staging.json
records the copy.

All four presets rebuild reproducibly with valid CRCs; 16 existing firmware
tests pass without skips. Both sound presets pass the 18 playback checks and
24 new capture-path/diagnostic checks, plus the existing config, route, data and
menu contracts. Against the prior audio-fix image, three alternate-path native
callback comparisons fail; additional failures concern the newly required
diagnostics, not separate demonstrated firmware bugs.

The candidate passes 13 admission/corruption checks and 12 private installation
review checks. An isolated assisted-QEMU retry passes all 17 sound-menu checks
with 30 native key events and return to live view. The first attempt stopped in
the native abort reporter during assisted menu entry, before any menu checks;
that failure is preserved alongside the successful retry. No camera was accessed.

`tools/verify_sound_shot.py` executes both native argument-setup paths, the
compiled hook and the native epilogue boundary. It compares callback arguments,
payload, return registers, flags and stack against stock; checks callback-before-
trigger ordering, disabled/absent/null-callback behavior, mode and native-busy
gates, and all six diagnostic title bindings. Properties, callbacks and queue
boundaries remain controlled. Sensor exposure, actual callback reachability,
timing, audible shutter cues and recovery are outside these checks.

See `evidence/20261021-shutter-trigger-investigation.json` for final validation
counts and [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md) for installation/recovery
limits. This correction is prepared for diagnosis, not a claimed hardware fix.
