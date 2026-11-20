# Original-Z7 module host probe

## Optional native parameter extension - November 20, 2026

The explicit API52 `--parameter-hooks` build extends the opt-in API48 highlight
host with narrowly filtered native parameter payload callbacks and read-only
update notices. Its [scoped validation](z7-native-modules/PHOTO_HIGHLIGHTS.md#native-parameter-payload-path-api52)
covers native caller/completion lifetime and registration. Default API44/API48
host bytes remain unchanged. API52 state is272 bytes, with the original256-byte
prefix preserved, and reserves320 workspace bytes. Original allocator101E3DAC
rounds allocation sizes to64 without aligning the cursor; reservation must
therefore remain a64-byte multiple. This is independently modified emulator
work, with no camera installation or recovery clearance.

November 19, 2026. Independent, emulator-only original Nikon Z7 C 3.80 work,
following the owner's choice of SD modules before display features. This extends
the [first module-format stage](SD_MODULE_PORT.md). No physical camera or card
was accessed, and the installed grid trial and prior build files are preserved.

## Implemented host

`z7-native-modules/host/z7_380.c` supplies the original-Z7 side of loading a
trusted native module. It reads `A:\Z7APP.BIN`, checks the exact model-specific
package, prepares aligned executable memory, clears BSS, rebases pointers and
calls `z7_main`. Successful image/BSS storage remains resident. Repeated calls
cannot reload or unload an active module. The SDK still exports no camera
functions, so this first module is a no-feature C initialization probe.

The stock-based firmware experiment changes two guarded locations: a 12-byte
workspace-initialization window and one four-byte AUTOOP callback binding. It
reserves 256 bytes before the first native monotonic-workspace allocation. The
callback calls the original initializer first, preserves its return value and
starts a separate low-priority task using the original native task wrapper.
Boot scheduling is latched per initialized state. Concurrency and physical
power/wake behavior still need separate validation.

The task makes at most 100 open attempts, separated by native delay argument
100. It stops retrying after reading a file or encountering another terminal
loader result, then parks with native delay argument 1000. The state keeps
status, native result, attempt count, module result and retained allocation.
`NO_FILE` is the prototype's generic open-unavailable result, not a diagnosis
that a physical card contains no file. The underlying native status is retained.
No physical timing is inferred from those delay arguments.

Read-only open, metadata size bounds, exact chunk counts and a final extra-byte
EOF check precede execution. A short read, read error, file growth, close error,
allocation failure, invalid package or nonzero initializer result prevents
publication of an active module. A failed close retains the handle value as a
diagnostic and blocks retries; it does not claim that the underlying OS resource
was released. No stale-handle raw-close fallback is attempted.

## Resident worker callback

November20,2026: additive API44 `sdk/worker.h` retains the existing40-byte
information prefix and every older prefix. One module-owned Thumb callback can
be registered during initialization. The existing low-priority loader task calls
it after each native delay argument1000, following successful module publication.
It is independent of display registration and does not run inside painting or
menu callbacks. Delay units and physical scheduling intervals are not inferred.

Registration rejects null, foreign, even, BSS and duplicate callbacks. Failed
initialization clears the staged pointer before releasing storage. Dispatch
requires valid host guards, loaded status, resident image/allocation and executable
image bounds; an atomic running guard suppresses recursive/concurrent dispatch.
The resident image length occupies a formerly reserved state word; all earlier
state offsets,256-byte reservation and guard offsets remain unchanged. The module
must bound its callback and coordinate shared settings state. This API supplies
no card-readiness guarantee, filesystem mutex or shutdown flush.

Private host09 is reproducible, MAIN33058860 bytes, resident4593 bytes, SHA
`7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
Worker probe01 is384 bytes, image320/BSS24, SHA
`428a947e16a756a659a0a88df6dbed67f8ca06d3378ea41baae3efd4aa5db83e`.
Fifty-five instruction checks include the actual loader loop with success,
failed initialization and exhausted unavailable-file retries. The earlier API40
host rejects this API44 module before registration. Loader99, display316,
GUI122 and information116 checks pass on host09; unchanged full module05 also
passes54 five-choice routing checks. Root55/no-skips pass. File,
allocator and kernel/delay boundaries remain supplied in these instruction runs.

Assisted QEMU worker-live01 passes11 checks. The native task loads the module,
then its counter advances2 to5 during free running with the modeled file fixture
already retired. The worker returns with its running guard clear and native MENU
input remains operational. No host counter stores or paint callback drives it.
The existing emulator binary remainsf76609ae...9b45c98; all5source fingerprints
and binary hash verified. Host11source and probe9source hashes verified. The
private MENU PNG hash is verified; this is a startup/task compatibility check,
not full display-feature or camera timing validation. Frozen helper sources are
retained beside the private run. No physical card or camera was accessed.

This is the execution path needed for future settings loading/saving, not an
implemented configuration writer. Keep card persistence and shutdown/recovery
assessment open; no write is registered by existing display profiles.

## Original-Z7 interface derivation

All instruction inspection uses the pinned stock MAIN SHA-256
`e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff`.
Instruction addresses below omit the Thumb low bit.

| Interface | Original-Z7 evidence | Tested scope |
| --- | --- | --- |
| File path/open | `0x102D8562`, `0x102D8566`, constructor `0x102D853C`, opener `0x102D84CE` | Original wrappers execute; modeled filesystem dispatcher receives read-only flags and the A: path |
| Descriptor and size | Constructor initializes 40 bytes; successful open calls `0x102D84A2`, using stat size at `+0x218` to populate descriptor `+24/+28` | Both low and high size words checked; oversized or nonzero-high sizes rejected |
| Native read | `0x102D86D8` → `0x1027C018` → filesystem request dispatcher `0x1027BEAE` | Original request opcode 8 carries FD, direct buffer, capacity and actual-count pointer |
| Native close and status | `0x102D85F2`, translation `0x102D83A4`; success `0x04390080` | Original close/reset/stat wrappers and error mapping execute; underlying dispatch modeled |
| Heap | `0x1016FE38` and `0x1016FE4A` | Allocator/free boundaries supplied in instruction checks; successful storage/allocator use still needs card-backed hardware checks |
| Read cache invalidation | `0x101E9F76` and cache-region selector `0x101E3E2A` | Original 64-byte-line loop executes against an explicit cache-region table fixture |
| Executable publication | New clean-to-PoU loop plus DSB, I-cache invalidation, DSB, ISB | Actual Thumb instructions execute and their order/count is checked; physical cache coherence is unverified |
| Native task creation/start | `0x1017074A`, trampoline `0x10170740`, start `0x101707F4` | Original task descriptor/wrapper executes with modeled kernel calls; native creation/start additionally observed in assisted QEMU |
| Task descriptor | Original APPIDLE descriptor at `0x11F9A92C`: priority 28, stack 8192, 28-byte record | Clone name becomes Z7MOD; copied fields and kernel start arguments checked |
| Startup and workspace | AUTOOP binding at RAM `0xA1822DB0`, native initializer `0x102697F4`; cursor `0xA18FD738`, initializer window `0x101E3DA0` | Guarded stock patch, original stack unwind/continuation registers and NZCVQ preservation tested |

The initial sound-port lead used 48 bytes of stack. Inspection establishes that
the native object itself occupies **40 bytes**, with the other space used for
the read-count result and alignment. This corrects the earlier inference that
the Z7 file object differs in size from the Z7II loader's object. The native read
calling convention and success code do differ and were not copied from Z7II.

The original invalidation helper intentionally iterates beyond the requested
byte count. A 513-byte request can invalidate ten aligned 64-byte lines. The host
therefore owns a **640-byte, 64-byte-aligned staging array**; tests check that all
those lines stay inside it. Using an unpadded 512-byte array could invalidate
unrelated dirty stack data. The cache-region table and hardware cache effects
are separate from this instruction-level address-bound check.

## Private builds and verification

The example C module now builds with private Zig 0.15.2's Clang/LLVM and embedded
LLD. Its image is 128 bytes, BSS four bytes, with two absolute pointer
relocations. The full Z7M1 file is 200 bytes. Native code verifies the API and
zeroed BSS before writing marker `0x5A703801`. It installs no display or capture
callbacks.

Final host candidate: `.private/builds/20261119-module-host-02/`.
Its MAIN is 33,053,812 bytes, SHA-256
`b2cde95401214c3115c55e3bd378dab836ae2f7e635612202dbd3e6e0a0fea1e`.
The host C image is 1,561 bytes; the total appended tail is 1,724 bytes, including
alignment and the guarded workspace helper. Two independent builds match and the
complete EG CRC is valid. This is a separate stock-based no-feature candidate,
not an update of the installed grid/spiral image or a cleared installation file.

The final instruction audit passes **99 checks**. It executes the compiled
Thumb host and C module through original Z7 file/task wrappers, with modeled
kernel, filesystem-dispatch and allocator boundaries. Cases include successful
initialization, wrong model/CRC, short/error/growing reads, both allocation
failures, close failure, initializer failure, full-width task IDs, task creation
and start failure, repeated boot scheduling, 100 exhausted retries and delayed
open availability. Workspace flags and register preservation, cache publication
order and the 640-byte staging bounds are checked.

An assisted QEMU boot of candidate 01 reached the native Playback menu, created
and ran the native task, exhausted all 100 unavailable-file attempts and retained
its state across MENU input. Its seven checks passed; the menu frame was visually
inspected. Candidate 02 additionally preserves NZCVQ at the workspace hook and
passes the same seven checks in a fresh QEMU guest. The exact final result is
under `.private/evidence/20261119-module-host-qemu-03/` and summarized in the
public source-only evidence record.

The first QEMU probe incorrectly required a task ID below 65536. The actual
kernel returned `0x01000102`, with the task already running. That assertion was
corrected to accept signed-positive 32-bit IDs and added to the instruction
fixture. A cleanup-path attribute error in that failed probe was also fixed;
the exact orphaned guest was identified and stopped before repeating. Failed
evidence is preserved. No firmware bug was inferred from these harness errors.

QEMU has no physical card for this run. It establishes native boot/task and
unavailable-file behavior, **not successful real-card loading**. The successful
module-read/initialization result comes from the instruction fixture's modeled
filesystem dispatcher. No sensor, capture, new display feature, sleep/wake,
extended operation, physical update acceptance or emergency recovery is claimed.

### Successful load with an explicit file-service fixture

Continuation run `.private/evidence/20261119-module-host-qemu-load-04/` passes
nine checks. A debugger fixture intercepts only the original filesystem dispatch
for `A:\Z7APP.BIN` and its owned synthetic file handle. It supplies read-only
open/stat/read/close results; unrelated dispatches execute their original code.
The guest's native task scheduler, allocator, cache-maintenance instructions,
host validation/relocation and compiled C initializer execute normally. The
probe's BSS marker is observed in its native allocated image, with loader state
retained across MENU input. This narrows the earlier allocator/execution gap;
it still does not establish real-card I/O or physical cache coherence.

The diagnostic observation point must be installed/refreshed after initial RSP
target negotiation. Installing it in the remote-client constructor left it
inactive after negotiation and produced two preserved unavailable-file runs.
One intermediate refresh asserted removal of a point that was not installed;
that harness assertion is also preserved. Successful installation is now checked
after negotiation and before bounded guest calls. The fixture retires after the
original close wrapper's final stat, before the guest runs freely.

## Reproduce on the root Windows laptop setup

First complete the existing root [Windows setup](WINDOWS_BUILD.md). Then add the
optional private compiler:

```powershell
.\tools\Setup-Z7ModuleToolchain.ps1
```

The [official Zig download](https://ziglang.org/download/0.15.2/zig-x86_64-windows-0.15.2.zip)
is pinned to archive SHA-256
`3a0ed1e8799a2f8ce2a6e6290a9ff22e6906f8227865911fb7ddedc3cc14cb0c`.
The helper preserves existing files and installs only under `.private`.
Clang/LLD are bundled in Zig; system MSYS2 and WSL are not changed.

Use **new** private output names for each run:

```powershell
.venv\Scripts\python.exe tools/build_z7_module.py z7-native-modules/examples/probe.c --zig .private/toolchain/zig-x86_64-windows-0.15.2/zig.exe --output .private/tmp/Z7APP-new.BIN
.venv\Scripts\python.exe tools/build_z7_module_host.py --output .private/builds/module-host-NEW
.venv\Scripts\python.exe tools/audit_z7_module_host.py --build .private/builds/module-host-NEW --module .private/tmp/Z7APP-new.BIN --output .private/evidence/module-host-NEW.json
.venv\Scripts\python.exe tools/probe_z7_module_host.py --build .private/builds/module-host-NEW --output .private/evidence/module-host-qemu-NEW
```

The compiler requires an ordinary permitted Windows process context; the Codex
restricted runner returned an uninformative `Unexpected` error, while its approved
local execution context built successfully. The module builder now keeps its
temporary files and compiler caches under the project's ignored `.private`.

## Next boundary

Validate real-card readiness/removal, read/error/EOF behavior and executable heap
cache coherence on the actual Z7 platform before calling this hardware-ready.
There is no verified emergency recovery. The installation-review helper rejects
this emulator-only identity. Any future staging or flashing requires its own
concrete exact-candidate installation/recovery assessment and explicit owner
authorization. Once the host boundary is established, expose the existing Z7
grid and histogram/horizon implementations as the first display-module controls.
The original sound-trigger hold and spiral EVF lag remain unresolved.
