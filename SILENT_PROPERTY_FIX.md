# Z7 Silent photography property correction — October 21, 2026

**Subsequent camera failure:** the owner reports repeated sound in live view and
Capture audio busy. See [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md).
The corrected property does not establish a valid photo trigger. Leave Enabled
OFF; the audit/flash hold remains. No new candidate was built for this report.

**Port audit hold:** the owner raised the risk of copied cross-camera assumptions.
This correction is not clearance for another flash. Read [PORT_AUDIT.md](PORT_AUDIT.md)
for the initial evidence-gap review; installation recommendations are on hold.

The owner followed the capture-start installation/test instructions and reports
no shutter audio. After the silent photo the sound-page heading is **Silent mode
required**. Unlike the earlier Waiting for capture result, this establishes an
owner-reported trigger attempt that stops at the silent-property comparison.
The owner had already confirmed Nikon Silent photography ON. Installation of
the staged candidate is inferred from the test sequence, without firmware readback.

## Confirmed mismatch

The port retained Z30 property `0x57B`. The native Z7 C 3.80 **Silent photography**
page is `0xB2`; its constructor at `0x1049AC30` explicitly reads **`0x576`** and
selects ON control `0x15F2` only for value 1 (otherwise OFF control `0x1567`).
The call passes through `0x104065A4` and `0x101D53AE` to original property getter
`0x1016FEF2`. This is the same getter used by the custom trigger.

The stock descriptor tables resolve `0x576` to `0xA24E3430`, whereas `0x57B`
resolves to the different location `0xA24E3444`. The native page title and ON/OFF
labels were identified through the local English UTF-16 resource table; assets
and raw metadata remain private. Merely confirming that `0x57B` exists was not
enough to identify its meaning.

The correction changes the trigger's property to **`0x576`**, preserving its
required value 1 and every other mode, loaded-file and busy gate. Relative to
the capture-start candidate, the EG changes exactly **three bytes**: one appended
instruction byte and the two regenerated CRC bytes. Length and all original
MAIN-body/menu/other appended routine bytes are unchanged relative to that build.

## Regression that exposes the previous test gap

Earlier tests returned a supplied value when the code queried `0x57B`. That mock
matched the copied assumption and masked the bug. Playback and capture tests now
execute the original native property getter and stock descriptor tables, with
controlled property RAM values rather than a mocked getter.

The capture tests also execute the original Silent photography menu constructor.
Four cases deliberately make the real Z7 property and old Z30 property disagree:
Z7/legacy values `(1,0)`, `(0,1)`, `(1,2)`, `(2,1)`. Each checks native ON/OFF
selection, capture admission and the actual queried property IDs. The previous
candidate passes native menu selection but fails all eight admission/query checks
in these cases. The corrected candidate passes all 60 capture checks and all 18
playback checks for both sound presets; all 16 existing firmware tests pass without
skips, and all four presets rebuild reproducibly with valid CRCs.

Native property RAM values, UI state/selection helpers, controller helpers,
semaphore, callback and queue boundaries remain controlled. These tests do not
establish real sensor exposure timing, audio completion or physical sound.

## Private candidate and review

Private build/review suffix: `20261021-silent-property-01`. Full `EG161080.BIN`,
33,065,322 bytes, SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
The version remains `03.80.00`. This candidate was staged as E:\EG161080.BIN
on the verified Sony QD-G240F card at 2026-10-22 04:38 UTC (October 21 locally).
Complete SHA-256 readback matched the candidate above. The previous card firmware
was backed up privately; SHUTTER.WAV and all other card files were preserved.
The review bundle's card-staging.json records the copy. Installation is now inferred
from the owner's latest test sequence without readback; the live-view regression
above supersedes the earlier pending result.
Prior candidates, the working WAV and original firmware remain preserved.

Candidate admission/corruption checks and private header/filename/package checks
passed (13 admission checks, 12 native review checks and three private bundle
copies verified by full readback). Results are recorded in
`evidence/20261021-silent-property-fix.json`. Full assisted-QEMU
menu testing was not repeated for this one-byte trigger change; the previous
capture-start build's 17 passing menu checks remain evidence for that baseline,
not a new emulator run. Menu and Preview code bytes are unchanged.

Read [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md) before a new installation.
Hardware shutter audio remains failed for the previous candidate and untested
for this corrected candidate. The next camera result must establish whether the
correct property permits the request and whether audio actually plays.
