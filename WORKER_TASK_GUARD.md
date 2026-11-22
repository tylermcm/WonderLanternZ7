# Private task-owned worker guard - November 22, 2026

Follow-up: the complete base host and native bridges have now been regenerated,
independently rebuilt and checked with both exact worker controls. See
WORKER_GUARD_HOST_ASSESSMENT.md and evidence/20261122-worker-task-full-host.json.
No camera update or card staging is authorized/performed. The overlay limitation
below describes the earlier blob-only checkpoint, not the subsequent full build.

Implemented and validated offline. Not installed on the camera. No new complete
MAIN/EG/update image, card staging or installation/recovery clearance is produced.
Owner authorized offline engineering work after the load-only probe froze.
Camera subsequently boots/responds normally without the card; failed LX remains
disabled and all card files remain intact.

## Ownership and behavior

`z7_module_worker_tick` is now a static, out-of-line function in z7_380.c, removed
from the host header. The production C/H scan finds exactly its definition and
one call in the resident loader-task loop. There is no dispatcher pointer in the
module API: modules can register one callback during initialization. The compiler
confirms local ELF binding for the dispatcher. The SDK documents that it is
private to the one task and that adding another caller requires a new ownership/
synchronization contract.

The dispatcher validates the same state/callback bounds as before. Its ordinary
volatile recursion flag returns if already set, writes one before callback entry
and zero after return, with compiler barriers around the call. It performs no
exclusive operation on the guard word. This is deliberately a task-owned recursion
flag, not a mutex for concurrent threads. Arbitrary raw-address calls by module
code are outside the SDK contract. Callback publication and any cross-task module
data retain their separate synchronization requirements.

The host-state layout, guard address and 44-byte base SDK ABI are unchanged.
No cached alias, unverified replacement RAM, guessed native mutex or new native
task is introduced. The installed old host remains unchanged. The earlier weak-CAS
source-only proposal is superseded for this worker path because it still used
LDREX on the region implicated by the hardware controls.

## Exact offline build and checks

Private build: `.private/builds/20261122-worker-task-guard-01`.
The host code blob reproduced byte-for-byte twice: 4,573 bytes, SHA-256
`5b389010817fe30ae681c9526c45832f71dcc40547bc2d637215c0ae74051ccd`.
Dispatcher is 146 bytes and has local ELF binding. Its complete disassembly has
zero LDREX/STREX/CLREX instructions. Code shrank from the installed 4,593-byte
blob; function addresses moved, so old external bridges cannot be reused for an
installation. Source layout/API stability does not imply address stability.

`tools/audit_z7_worker_task_guard.py` overlays the new blob into an in-memory
fixture and updates its C-symbol metadata. It saves only the code blob, symbol
metadata and evidence, not a full firmware image. The out-of-blob native display
bridges still contain old addresses and are explicitly not exercised or cleared
by this fixture. A future complete host build must regenerate them.

Validation passed:

- 55 existing worker checks: initializer/callback admission, bounds, failed-load
  cleanup, late-registration refusal, guard/state rejection, recursion, legacy
  API rejection, and actual resident loop with success/failure/missing module.
- Four additional exact guard traces: normal and recursive dispatch call the
  callback once and write only ordinary 1/0; busy and unregistered paths skip
  the callback and leave the guard unchanged.
- Production caller scan, ELF local linkage/size, complete guard disassembly,
  repeated build, Python compilation and repository diff checks.
- Root repository suite: 99 tests passed. Code graph refreshed; existing
  conditional-C extraction limitations remain.

Native kernel, heap, filesystem, telemetry and delay returns remain supplied
fixture boundaries. This does not prove physical scheduling, memory attributes,
camera update acceptance, recovery, or that all future module synchronization is
safe. Optional advanced host profiles and complete native display integration
were not rebuilt/tested here. No hardware fix is claimed.

The next firmware engineering checkpoint is a complete base-host rebuild with
regenerated native bridges and an exact no-I/O worker candidate, followed by full
integration checks and installation/recovery assessment. No flash authorization
is inferred from permission for this offline change.

Source-safe evidence: `evidence/20261122-worker-task-guard.json`.
