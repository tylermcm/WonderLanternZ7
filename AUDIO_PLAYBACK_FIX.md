# Z7 playback admission correction — October 21, 2026

The owner reported that the installed full build shows `SHUTTER.WAV` as loaded
but produces no audible Preview. The stronger test file also stays silent.
`Sound busy` becomes visible when moving the menu selector after activation.

The exact WAV meets the vendored Z7 repository's requirements. Two independent
porting errors prevent the old request path from reaching normal playback.

## WAV requirements and actual file

The authoritative local requirements are in
[`docs/shutter-sound.md`](z7-firmware-extensions/docs/shutter-sound.md),
`tools/prepare_wav.py`, and the generated `sound_audio_z7.py` validator.

| Field | Required | Staged test file |
| --- | --- | --- |
| Encoding | RIFF/WAVE, uncompressed integer PCM (tag 1) | Matches |
| Sample rate | 8,000 Hz | 8,000 Hz |
| Channels | Mono | 1 |
| Samples | Signed 16-bit little-endian | Matches |
| Header | Canonical 44 bytes, 16-byte fmt chunk, no extra chunks | Matches |
| Byte rate / block alignment | 16,000 bytes/s / 2 bytes | Matches |
| Duration | Nonempty, at most 1.08 seconds | 0.9 seconds |
| Data/file length | At most 17,280 / 17,324 bytes | 14,400 / 14,444 bytes |
| Filename/path | Card root `SHUTTER.WAV` | Verified after copying |

File SHA-256:
`d9b38aae45fbe7cb6ccbe79e64bafc40c2d69d987beb6608f00d8c0fc1145ac0`.
Its RIFF size is 14,436, exactly file length minus 8. The installed build's
validator accepts its 14,400 data bytes; conversion produces nonzero, reference-
matching 48 kHz stereo PCM. The internal output format does not change the
required 8 kHz mono format of the WAV on the card.

## Incorrect busy address

The native busy getter at `0x1006B540` reads the state byte at `0xA188D190`.
The format table starts 16 bytes later, at `0xA188D1A0`; its first word is 2 in
the checked stock initialized-data image. The port used the table address for
the Preview and shot-trigger busy checks. Therefore an idle audio service could
be reported busy before any request was queued.

The correction gives state and format table distinct named constants and uses
the actual state address for both busy checks. Native busy still blocks playback.
The menu reads the recorded result again while rendering/selecting rows, which
fits the reported delayed appearance of the error.

## Invalid playback type

The port requested type 18. The stock consumer at `0x1006BC46` checks the type
through `0x100A2C04` with an exclusive upper bound of 18: valid types are 0–17.
This is verified by executing the actual native range checker and consumer;
18 is rejected, while 17 reaches configuration under the same ready-state fixture.

The correction uses the last valid descriptor, type 17, for the custom request.
Config and data replacement still require the exact private completion callback
and nonempty loaded state. Native audio using that same type with another
callback retains its stock config and stock resource data.

## Build and verification

Private build: `.private/builds/20261021-audio-fix-01`.
Private review bundle: `.private/flash-review/20261021-audio-fix-01`.

| Candidate | Bytes | SHA-256 |
| --- | --- | --- |
| Full EG, with CRC | 33,064,942 | `770408b99ff547dd972486656285307b17e4ff2674937dbb50f144200233b7be` |
| Full MAIN, for QEMU | 33,064,940 | `596ecfdf8ea829b18d15734411c2f12c0d8dbdd6310c8f9aa0ed3d77023723d4` |

Against the installed full EG, exactly five appended-code bytes change, plus
the two regenerated CRC bytes. No byte of the original MAIN body or other
firmware modules changes. This remains an independent modified research release.

`tools/verify_sound_playback.py` is now a required build check for both sound
presets. Five request-path checks fail against the installed build. All 18 pass
against each corrected sound preset. The tests execute compiled Preview,
trigger, start, config, data and completion routines, stock metadata, the native
range checker and consumer admission code. They also check stock handling for
a foreign callback using the same type.

Heap/property/ready-state/queue/UI boundaries are controlled. Callback packets
are synthetic unit-test inputs, not observed hardware completions. These results
do not establish physical audio scheduling, DMA, amplifier behavior, speaker
output or failure recovery.

The rebuild also passed 16 existing firmware tests without skips, reproducible
output/module CRC, 1,024 DISP gate cases per applicable preset, the existing
hook/route/data/menu contracts, 13 candidate checks and 12 private package/header/
filename checks. The corrected full image also passed all 17 isolated assisted-
QEMU sound-menu checks using 30 native key events, including return to live view.
The first sandboxed probe could not open its localhost diagnostic socket; the
successful isolated retry used the normal host socket permissions. Neither
attempt accessed a camera. These checks cannot prove physical sound.

Sanitized results are in
[`evidence/20261021-audio-playback-fix.json`](evidence/20261021-audio-playback-fix.json).

The corrected candidate was staged as E:\EG161080.BIN on the verified Sony
QD-G240F card at 2026-10-22 03:08 UTC, with complete SHA-256 readback matching
the table above. The old card firmware was backed up privately; SHUTTER.WAV
and all other card files were preserved. The owner subsequently reported
"the wav actually works now!" after the corrected staging and installation/
Preview instructions. Audible WAV playback is owner-reported; the exact playback
mode was subsequently clarified by the owner: audio works but shutter replacement
does not, despite Enabled ON, a selected WAV and Silent photography ON. Corrected
installation is inferred without firmware readback. Shutter-triggered playback
has failed by owner report; repeated-use stability and recovery remain unverified.
See [the capture investigation](SHUTTER_TRIGGER_FIX.md). The previously installed full image and
both original stock rollback inputs remain private and preserved. Read
[`FLASH_ASSESSMENT.md`](FLASH_ASSESSMENT.md) before another hardware attempt.
