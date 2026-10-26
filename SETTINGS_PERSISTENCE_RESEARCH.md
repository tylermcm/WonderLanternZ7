# Internal settings persistence — original Z7 C 3.80

## Preferred next experiment: existing saved grid scalar

Read `NATIVE_GRID_SETTINGS.md`. A new prototype preserves the native 89-record
format, stores 3x3 as value 2 in the existing grid field, and normalizes that
one value to On for native scalar reads. Original worker saves and fresh-RAM
startup reloads now pass, along with stock-loader fallback, all indexed-property
read comparisons and QEMU menu/live tests. It is emulator-only and not staged.
This avoids the added-record compatibility/conversion problem of the older
implementation below. Shared-reader consumer and physical-lifecycle review
remain required; raw setter acceptance alone is not compatibility proof.

## Hardware finding: temporary retention under approximately three seconds

The owner counted the off duration: selected 3x3 spacing survives rapid off/on
under approximately three seconds; longer off periods return to 4x4. That
clarifies the initially ambiguous delayed-reset report. Reliable persistence is
not established. The associated grid-only full EG SHA-256 is
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
This image has no custom journal hooks. Its initializer defaults to 4x4 when
executed, but the actual quick-restart/longer-shutdown paths remain untraced.
Temporary state retention is a hypothesis consistent with the observation,
not a proven memory/power mechanism. Battery removal and the exact threshold
remain untested. No spontaneous reset while continuously on was reported.

Use rapid off/on and at least ten seconds switched off as distinct lifecycle
regression cases. The optional 90-record implementation below was not installed
and remains held; these observations do not validate its storage design.

## Hardware-test selection and hardening — October 25, 2026

The owner chose the RAM-only grid build for the first hardware test. Internal
persistence remains a separate held prototype. Read `GRID_FLASH_ASSESSMENT.md`
for the selected installation input; none of the persistent candidates should
be staged for that test.

Latest private persistent candidate: `.private/builds/20261025-grid-persistent-05/`,
MAIN 33,058,292 bytes, SHA-256
`e230338d7d513a54b44cea6e0f2073e3b8f22aee15f0aa848f552d293ce1d8e7`.
It is independently rebuildable with valid EG CRC; 6,204 bytes are appended.
The 74 checks in `evidence/20261025-grid-persistence-hardening.json` pass,
including the previous CRC, migration, fresh-RAM, failure and sampled program
interruption cases, plus:

- Missing magic, invalid mode, corrupt native/owned destination pointers and
  lengths reject main load/save without changing live payloads, touching the
  damaged workspace or writing flash. Saves require a ready workspace and
  correct descriptor count/table/version/header fields.
- The load wrapper builds its own checked descriptor rather than trusting the
  caller's mutable destination table. Immutable destination/length pairs are
  checked against the pinned ROM copy.
- After conversion, restarting modified firmware and performing another normal
  save keeps the original 89-record format. An unmodified stock loader still
  accepts it. Selecting either grid type explicitly reenables the extension,
  even when selecting the already active 4x4 choice. A stock-format startup alone
  performs no migration write and leaves extension dirty state clear.
- A failed conversion restores the previous mode, preserves dirty state and
  releases its save lock/allocation.

Native contract correction: each schema triple's third word is a **mutable
flash-source cache**, populated by the native loader. It is not an immutable
flag or a dirty bit. Candidate 04 compared whole triples and rejected normal
native cache updates; its audit failed and it is superseded. Candidate 05
checks immutable pointer/length pairs and allows native cache population.
No failed/intermediate candidate is selected for physical installation.

The conversion entry is still diagnostic, without a camera menu or updater
action. Complete lifecycle, wake, cross-task concurrency, compaction/endurance,
partial physical writes and emergency recovery remain open. The new checks do
not establish those properties. Candidate 02 also passed 10 native-key QEMU
menu checks (`evidence/20261025-grid-persistent-menu.json`); that separate result
is not a later-candidate or persistent-QEMU-reboot test.

## Compiled prototype update

The initial investigation below is now followed by an optional compiled
emulator-only implementation in `features/settings_z7.py` and
`grid_z7.build(..., persistent=True)`. Candidate
`.private/builds/20261025-grid-persistent-02/` is reproducible, 33,057,940 bytes
of MAIN with SHA-256
`a0cda3a3c4acac326cfbc56ac9aca48b075f09c3a5742f8470a5f7da79bd508c`.
Eight guarded windows replace 80 bytes and append 5,852 bytes. Ordinary grid
builds and installation presets do not enable persistence.

The hooks reserve 0x500 owned workspace bytes, keeping the existing atomic live
choice at offset 4 and a separate 16-byte record at offset 16. Record contents
are WLS1 magic, version 1, choice 0/1 and IEEE CRC32 over the first 12 bytes.
An owned copy of the original record table adds record 89 without changing any
native payload layout or the native 0x102D On/Off property.

The descriptor and startup load hooks implement original-format fallback before
Nikon's reset handling. Valid custom data restores the choice; bad CRC, version
or choice defaults only the extension. Native reset also resets the extension.
The normal main-journal save routine is wrapped: a checked 176,744-byte allocation
holds an immutable payload snapshot and independent read-back buffers. Original
save/load code operates on those descriptors. Every payload is compared, scratch
storage freed and native logical-view/global-descriptor pointers restored.
Failure leaves dirty state set; a generation change during verification also
retains dirty state. Grid selection/rendering never directly programs flash.

The compiled diagnostic rollback entry selects the original schema and uses the
same verified save path. A fresh instance of the unmodified stock loader accepts
its output and restores every native record exactly. This entry is not yet in a
camera menu or updater lifecycle; its RAM-only mode will not survive a restart
back into this modified firmware. No physical rollback/recovery claim follows.

Validation on this exact candidate:

- `audit_grid_persistence.py`: 53 checks, including fresh-instance 3x3/4x4
  persistence, actual native startup caller, migration/reset, corrupt CRC,
  allocation/write/read-back failures, concurrent-generation detection, busy
  exclusion, conversion back to stock and six interrupted program boundaries
  during initial migration. All 89 native payloads survive the sampled cuts.
- `audit_grid_firmware.py`: 190 checks and 270 geometry calls. The earlier
  RAM-only candidate also still passes all 190 checks after tool changes.
- Assisted QEMU live view: six checks pass; private frames/logs are under
  `.private/research/grid/20261025-persistent-live-01/`. This uses diagnostic
  invocations of compiled handlers and native display updates, not a full
  natural menu-to-live-view sequence or a QEMU persistent-flash reboot.
- Patch/container/Thumb tests: 14 pass; two optional integrations skipped.

All persistence/restart tests use fresh Unicorn instances with supplied OS,
allocation and flash-controller boundaries. Power interruption samples occur
after whole program calls, not midway through physical flash programming.
No firmware was staged and no camera/card was accessed. Wake, full shutdown
policy, U1/U2/U3 interaction, repeated compaction, endurance, physical write
timing, updater integration and recovery remain open. Before installation,
audit invalid-workspace fail-closed behavior and add user-visible failures.
Native-key menu navigation has not been rerun on this persistent candidate.

```powershell
.\.venv\Scripts\python.exe tools/build_grid_firmware.py --persistent `
  --output .private/builds/NEW-PRIVATE-DIRECTORY
.\.venv\Scripts\python.exe tools/audit_grid_persistence.py `
  --build .private/builds/20261025-grid-persistent-02 `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --container .private/stock/Z_7_0380.bin `
  --output evidence/20261025-grid-persistence.json
```

Earlier prototype candidate 01 passed 25 initial checks; candidate 02 adds an
explicit match between save schema count and rollback mode. An early expanded
audit was invoked before its build report existed and failed on that missing
file; the completed build was then independently validated before testing.

## Original storage investigation

Independent investigation, October 25, 2026. The owner explicitly prefers
settings that stay inside the camera when cards are swapped. No card-file
fallback is being implemented.

The existing grid candidate remains RAM-only. This investigation has **not**
installed persistence hooks, built another firmware, staged a card or accessed
a camera. The additional record and compatibility descriptors below are
controlled inputs to original instructions running in isolated Unicorn memory.

## Result

The original firmware contains a native journal for the main camera settings.
Its default schema has 89 records. A supplied 90th record survives a native
journal save followed by loading in a fresh Unicorn instance, preserving all
89 native payloads byte-for-byte. An explicit original-schema retry loads old
settings before extending them. An explicit conversion back to the original
schema produces a journal a fresh stock-schema instance can load.

This identifies an internal-storage prototype path; it is not an approved
persistent firmware implementation or a physical durability result. A bare
schema replacement is incompatible in both directions. The production grid
feature is unchanged while migration, rollback, lifecycle and write verification
are designed.

## Independently traced native path

| Boundary | Original Z7 address / contract |
| --- | --- |
| Menu scalar setter wrapper | `0x104065B0` -> `0x101D61EE` |
| Low-level property writer | `0x100704FA`; `0x102D` has four-byte live storage at `0xA24F182C` |
| Packed RAM snapshot update | `0x100B9E6C`; table `0xA18C25D0`, 452 entries |
| Snapshot grid entry | Entry 324, one byte at offset `0x29C`; no flash program by this update alone |
| Native storage initialization | `0x10091CAC`; logical records at `0xA1880B00` |
| Main settings descriptor getter | `0x10070A16`; 89 triples at `0xA18C2190`, schema version 7 |
| Native settings buffer getter | `0x100709EA`; header `0xA24E2C4C`, payload length `0x154CC` |
| Stock startup load caller | `0x10117594` -> `0x101AEBAE` for logical ID `0x0F`, then `0x1007099A` |
| Main save caller | `0x1011764A` -> `0x101AEC44` for logical ID `0x0F`; argument 1 selects this store without other large datasets |
| Journal regions | `0x12E00000` and `0x131E0000`, each `0x40000` bytes |
| Native grid in main schema | Record 49, length `0x240`, scalar offset `0xB4`; six separate banks for this setting group exist in the table |
| Record validator | `0x100912BA` checks record IDs and exact lengths |
| Journal writer | `0x10091974` -> `0x10091848`; dirty-record comparison, append/compaction and commit markers |
| Flash program wrapper | `0x10091266` -> `0x101AE3F0`; byte count converted to halfwords, up to three retries |
| Flash erase wrapper | `0x10091242` -> `0x101AE430`; `0x20000`-byte sector units, up to three retries |

These are firmware memory/driver contracts. They do not identify a physical
flash part number or prove a separate EEPROM chip exists. The traced path
reaches the firmware's flash erase/program service.

The raw property writer accepts 2 and `0xFFFFFFFF` for `0x102D`; it is not a
boolean range validator. An early assumption that it rejected 2 was disproved
by executing it. Stock menu handlers supply 0/1 and multiple display consumers
compare specifically with 1. Simply writing 2 does not implement a compatible
third grid choice. The packed snapshot's one-byte storage is also distinct
from the four-byte live property.

The generic logical-record path is separate from the main settings journal.
For example, member `0x13` is a `0x100`-byte view at offset `0xA100` of parent
`0x11`. Saving it through `0x101AEA60` erases a full `0x20000`-byte bank at
`0x132C0000`, writes `0x1FFFC` bytes and programs its four-byte completion
marker. This is a synthetic demonstration of write scope, **not an identified
slot for extension settings**.

## Compatibility experiments

The additional record uses a supplied 90-entry schema and a 16-byte synthetic
payload. It does not reuse an existing Nikon setting or overwrite a native
record. The payload is a fixture, not a final format; it has no production
version/integrity/migration policy.

1. Stock schema save/load restores all 89 native payloads exactly.
2. Extended schema save/load restores all 89 native records and the supplied
   custom record exactly in fresh RAM.
3. Old journal with a bare extended loader is rejected: required record missing.
4. Extended journal with the stock loader is rejected: record ID out of range.
5. Explicit migration tries extended load, retries the original schema before
   startup reset handling, initializes custom state, then saves extended format.
   Fresh extended loading preserves all native payloads and custom data.
6. Explicit rollback conversion loads extended data, saves original format,
   then loads in a fresh stock-schema instance. All 89 native records match.
   Simply installing stock firmware is not covered by this successful case.

Neither conversion is installed in firmware. The normal startup caller passes
load failure into `0x1007099A`, which can reset settings to defaults. Missing
extension handling must occur **before** that failure reaches the caller.

## Write status is insufficient

Injected erase/program failures in the generic logical-block writer return
failure with bounded retries. The main journal behaves differently:
`0x10091974` discards the result from `0x10091848` and returns 1. In the fixture,
failing the first program gives an apparent successful `0x101AEC44` result,
but a fresh loader rejects the store.

An implementation needs independent read-back/selection validation of the saved
generation and payload. A successful return is insufficient. This audit does
not establish power-interruption recovery, later append/compaction durability
or flash-controller timing.

## Required implementation boundary

- Preserve Nikon's `0x102D` behavior and all 89 record layouts.
- Use a bounded, versioned extension record with integrity checks and defaults.
  The supplied record proves basic feasibility, not ID ownership across releases.
- Implement migration before reset handling; distinguish missing extension data
  from corrupt native settings.
- Provide verified original-format conversion **before** returning to stock.
  Updater ordering and a user-accessible conversion route need tracing. No
  automatic stock downgrade/recovery claim is justified.
- Connect changes to Nikon's normal save/shutdown worker. Never erase flash
  in a renderer or write on every frame.
- Read back the selected committed journal and retain dirty state on failure.
  Test interrupted data/marker writes and full-bank rotation.
- Prove load-before-first-grid-render, U1/U2/U3 behavior, reset/default handling,
  wake behavior, both processor readers and extension composition.

No persistent candidate should be staged based on this audit. Installation and
recovery remain governed by the existing flash assessment.

## Reproduce and scope

```powershell
.\.venv\Scripts\python.exe tools/trace_settings_storage.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --output evidence/20261025-settings-storage.json
```

Input: pinned original Z7 C 3.80 MAIN, SHA-256
`e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff`.
All 45 checks pass. Original property/mapping/default initialization, storage
initialization, journal parsing/writing and memory-copy instructions execute.
Supplied boundaries: workspace allocation, a model token, OS locks/context/events
and flash erase/program into isolated Unicorn memory. Fresh instances receive
only synthetic stored bytes, with fresh working RAM. Every native call checks
return PC, stack and callee-saved registers.

Firmware bytes, synthetic flash images and exploratory disassemblies remain
private. Public JSON contains addresses, sizes and pass/fail observations only.
No patched firmware or QEMU machine was built. No full camera cold boot,
updater, physical storage, battery removal or recovery was validated.

Early private runs are retained: global instruction instrumentation made native
default-copy loops exceed the fixture time limit; selective boundary hooks
resolved that overhead. The initial single-bank expectation also omitted the
native completion marker and was corrected from observed writes.
