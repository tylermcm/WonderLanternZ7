# Persistent grid candidate review — October 25, 2026

**October 26 owner result:** the latest staged candidate was installed, and the
owner confirmed 3x3 stays selected after more than ten seconds switched off.
This is limited to one reported camera, without independent observation or
firmware readback. Other functions, extended durability and emergency recovery
remain unverified. Earlier preparation/staging statements below are historical.
For public distribution, the owner chose a source/patcher-only preview; see
`RELEASE_GRID_PREVIEW.md` and the prominent `RISK_NOTICE.md`.

**Staging update:** on the owner's explicit request to copy it for flashing,
the exact candidate below was copied to the freshly verified Sony XQD at
`E:\EG161080.BIN`. Full final-file SHA-256 matches; it is the only root `.BIN`.
The working RAM-only EG was verified/backed up on the laptop first. Other files
were preserved, with root settings/audio hashes checked unchanged. No formatting,
automatic ejection or agent-operated camera flash occurred. Owner installation
and physical persistence results are pending. Offline preparation descriptions
below refer to the preceding phase.

This assessment covers the independent original Nikon Z7 C 3.80 **existing-setting
grid** candidate. It is different from the owner-tested RAM-only build and from
the held 90-record journal prototype. The owner requested this firmware build;
the work here prepares local files, without card staging or camera programming.

## Intended behavior

After selecting 3x3, it should remain selected across shutdowns of any duration,
using Nikon's existing internal settings storage. There is **no expiry timer or
timed reversion to 4x4**. A test with at least ten seconds switched off is simply
longer than the old image's approximately three-second retention window; it is
not a duration limit in the new design.

Select 3x3 once after installing this image. The earlier RAM-only image did not
save the type, so the update cannot recover that old choice from native storage.
Choosing 4x4 or Off intentionally changes the saved setting. Off stores 0 and
forgets the prior type. Native settings resets/imports may also change the field
as they do other Nikon settings; user-mode/import interactions are not cleared
by this preparation.

Only 4x4 / 3x3 / Off grid functionality is included. This stock-based image
replaces the earlier sound/splash/M900/dual-display experiments rather than
combining them. The original sound-port hold still applies to sound builds.

## Exact private files

Fresh build: `.private/builds/20261025-grid-native-flash-01/`.
Review bundle: `.private/flash-review/20261025-grid-native-01/`.
Convenient binary: `.private/flash-ready/20261025-grid-saved/EG161080.BIN`.

| File | Bytes | SHA-256 |
| --- | --- | --- |
| Independent full EG candidate | 33,054,026 | `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7` |
| Candidate MAIN for emulation | 33,054,024 | `7f29bfda937c90261eff989d5f27dbf71ca2b142308b70879b1a7ef3d46c4075` |
| Untouched original EG | 33,052,090 | `7f59d8993080203a12692cf6927a0a8218786d3f72230c04174f1563c506a6f6` |
| Untouched official container | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |

The full EG, MAIN and report exactly match tested native-value candidate 02.
Four guarded windows total 28 bytes, with 1,936 appended bytes. Version remains
03.80.00. Only the full EG, including its two CRC bytes, is the component-file
installation input. Do not use MAIN, truncate the tail, or rename an EG as the
official `Z_7_0380.bin` container. No modified outer container was repacked.

The original EG descriptor allows 43,253,760 bytes; this EG also fits the
patcher's stricter 32 MiB bound. Original firmware, previous working image and
the new candidate remain separately named and private.

## Storage change and rollback implications

The existing native scalar 0x102D stores 0=Off, 1=4x4, 2=3x3. A guarded shared
scalar-reader wrapper normalizes only successful grid/value-2 reads to boolean
On while preserving the original return flags. Owned geometry/menu routines
read the raw stored type. This alters the field's value encoding, while keeping
the original 89-record journal layout. No added journal record, heap reservation,
custom flash writer, or journal descriptor/load/save/reset hook is included.

Original native worker saves and startup loads execute in the instruction
fixture. A fresh unmodified stock loader accepts the resulting journal and
preserves all 89 native payloads; its tested grid menu/visibility consumers
treat stored value 2 as Off. No incompatible-schema conversion is needed in
those tested paths. This is not exhaustive stock behavior or physical rollback
validation.

If the camera remains bootable with updater access, the separate stock module
or official container are potential rollback inputs. The previously working
RAM-only EG is another preserved experimental comparison input. Same-version
rollback on this body is unverified; none of those files is a full flash or
calibration backup. **There is no verified local emergency recovery for an
unbootable Z7.** A failure could require professional servicing/reprogramming.
The normal Nikon guide's service fallback and power precautions are linked in
`GRID_FLASH_ASSESSMENT.md`; they do not establish recovery for this image.

## Completed verification

- Fresh repeated builds and complete independent admission match the tested
  candidate's EG, MAIN and report. The complete EG CRC and output hashes pass.
- The same exact candidate passed **107 instruction checks**, including 21,130
  scalar calls covering all 2,111 indexed native properties plus invalid keys,
  NZCVQ/ABI preservation, native request/worker/completion, fresh-RAM restoration
  of all three choices, preservation of native records, selected stock fallback,
  failed programming and two whole-program-boundary interruption cases.
- **10 native-key menu and 6 assisted live-view QEMU checks** passed on that
  exact MAIN. Native UI service stores 2 for 3x3; both grid sizes and Off render.
- The exact full EG and stock module pass **12 original updater header/filename
  probes**. These mock file I/O and runtime-property boundaries; they do not
  execute complete card enumeration, programming or real update acceptance.
  All four original module CRCs, official-container CRC/bounds/trailer, and
  private bundle copies are checked independently.
- **Six review tests** cover private output containment, overwrite prevention,
  corrupt/mixed files, unsupported presets, and rejecting RAM-only artifacts
  when selecting the native-value candidate, and vice versa.

The instruction fixture supplies OS/events, flash-controller operations,
secondary datasets, selected UI/viewport boundaries and zeroed native BSS. QEMU
does not retain the flash banks across its processes in these runs. Emulator
success does not establish complete physical shutdown, durability or recovery.

Evidence: `evidence/20261025-grid-native-value.json`,
`evidence/20261025-grid-native-value-qemu.json`, and
`evidence/20261025-grid-native-flash-review.json`. Read `NATIVE_GRID_SETTINGS.md`
for implementation contracts and detailed test scope.

## Remaining risk and physical test

The shared getter is native infrastructure. Indexed property/flag comparisons
do not prove every indirect consumer. User presets U1/U2/U3, native toggles,
settings-file import/export, standby/wake, full shutdown ordering, long sessions,
physical programming and durability remain unverified for this image. This is
an experimental hardware-test candidate, not a production-safety certification.
The new binary has not been physically installed or staged by this preparation.

Before staging, identify the actual card/reader again and preserve existing
firmware and user files. Do not assume that the earlier E: mapping is current.
Only the exact reviewed candidate EG should be at the card root; read back its
full hash after copying. Keep all stock/comparison firmware off that card.

Confirm the original Z7 C 3.80/no paid RAW upgrade and fully charged supported
power, inspect the actual current/new versions in Setup → Firmware version,
and obtain explicit authorization before programming this exact candidate.
During an update, follow its completion instructions without interrupting
power, operating controls or removing the card.

After a completed installation, select 3x3 once and confirm the menu and display.
Test normal shutdowns longer than the old retention window: at least ten
seconds, then a longer off period. Those are checks of persistence, not expiry
thresholds. Confirm 3x3 is retained, then test intentionally selecting 4x4 and
Off, LCD/EVF, standby/wake, ordinary capture/playback and recorded-image contents.
Report any unexpected reversion rather than calling it successful persistence.

## Reproduce review

```powershell
.venv/Scripts/python.exe tools/prepare_flash_review.py `
  --preset grid-native --build .private/builds/20261025-grid-native-flash-01 `
  --output .private/flash-review/NEW-UNUSED-NAME
.venv/Scripts/python.exe -m unittest discover -s tests -p test_flash_review_paths.py -v
```

The helper prepares private local files only. It has no camera/card write step.
