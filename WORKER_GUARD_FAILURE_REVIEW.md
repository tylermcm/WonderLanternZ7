# Worker guard: localized suspected failure point

## Update: matched hardware trigger and resident-loop trace

November 22: owner-confirmed A working, B freezing, and camera normal again with
the card removed. A/B have identical code/layout and differ only in the worker
enable flag and CRC. B's callback begins `bx lr`; it contains no restore or file
I/O. B is preserved as Z7APP.WORKER-B.disabled, no active root BIN remains,
and safe ejection was verified. All earlier files and working A are intact.

`tools/trace_z7_worker_dispatch.py` now traces the successful registration and
the installed resident loop separately. On the supplied successful load path,
registration at 0x11fa66f6 returns success after writing exactly two host words:
callback at 0xa97000c4 and registered flag at 0xa97000c8. Its executed trace
contains no calls or exclusive instructions. This excludes a hidden registration
retry loop in that path, without proving its physical memory accesses succeeded.

The exact resident loop is at 0x11fa6032: native delay(1000), worker_tick, repeat.
The audit enters that loop after the real audited module load, supplies native
delay returns, and stops at the fourth delay boundary or 4096 instructions:

| Exact module and supplied condition | Delay calls | Callback entries | Failed stores |
| --- | ---: | ---: | ---: |
| A, healthy | 4 | 0 | 0 |
| B, healthy | 4 | 3 | 0 |
| A, failed-store injection | 4 | 0 | 0 |
| B, failed-store injection | 1 | 0 | 804 |
| B, failed-store injection, bounded branch in memory | 4 | 0 | 3 |

The last case changes only the host's two-byte BNE target from retry to its
existing return in emulator memory. No patched host artifact or firmware image
is emitted. It proves that the retry loop can prevent subsequent native delays;
it does not model scheduler priorities or establish that this stalls physical
input tasks. A bounded failure also does not demonstrate a functioning worker:
all three ticks skip it when the exclusive store is forced to fail.

The leading suspect is therefore the pre-callback guard acquisition, specifically
STREX 0x11fa5858 and its retry branch 0x11fa585e. The physical distinction between
repeated STREX failure, an exclusive-access exception, or another worker-path
fault remains open. No physical PC, MMU attributes, exception record or callback
entry was captured. Do not call this exact hardware cause confirmed.

Next hardware evidence must distinguish bounded failure from successful guard
acquisition/callback execution. Another empty-worker SD test would repeat B.
Any installed-host change needs its own exact installation/recovery assessment
and explicit authorization; the existing offline weak-CAS build is not installed.
Private trace: `.private/evidence/20261122-worker-dispatch-trace-01.json`;
source-safe copy: `evidence/20261122-worker-dispatch-trace.json`.

The earlier investigation below is historical; its pre-A/B card state and
pending-owner-check statements are superseded by this update.

November 22, 2026. Camera's working battery/six-grid module restored; no new
firmware flash or camera experiment. The read-only restore module and seed,
earlier baselines and all trial files remain intact. Card safely ejected.
Owner has not yet tested the restored card. Installed host remains unchanged.

## Exact installed-code behavior

The current pre-change source reproduced the installed host blob byte-for-byte:
4,593 bytes, SHA-256
`6ef05fb5730fef910dfaa7245446f3c515bb16d9111803748b808cbda2566fd3`.

`z7_module_worker_tick` starts at 0x11fa57d4. After validating worker state, its
strong compare/exchange operates on `worker_running` at 0xa97000cc:

| Instruction | Address | Effect |
| --- | --- | --- |
| LDREX | 0x11fa5852 | Read guard exclusively |
| STREX | 0x11fa5858 | Attempt to set guard |
| BNE back to LDREX | 0x11fa585e | Retry on failed exclusive store |
| BLX callback | 0x11fa5868 | Enter worker only after acquisition |

There is no retry bound or native delay inside this acquisition loop. If the
store keeps returning failure with the guard still zero, execution never reaches
the module callback. A worker whose entire body is return-zero cannot prevent
this pre-callback stall. With no registered worker the host returns before it.

## What the offline experiment establishes

`tools/audit_z7_worker_exclusive_progress.py` loads a 384-byte instruction-only
worker probe through the exact installed host. Its fault hook supplies a failed
STREX result and skips that store; it does not simulate a real memory monitor.
Under a 4,096-instruction cap, the installed code attempts 805 failed stores,
remains at 0x11fa585e and invokes no callback. This is an intentionally injected
instruction-level stall, not a reproduction of the entire camera input freeze.

An in-memory two-byte branch experiment returns after one failed attempt.
The actual source hardening changes strong CAS to weak CAS, making failure skip
this tick and allowing the resident task to delay before the next attempt.
Its compiled blob is reproducible, has the same length and function addresses,
and differs only inside the worker-tick function. Healthy, busy, absent-worker,
recursive-callback and transient-failure cases also pass. All 99 root tests pass.
This preserves atomic mutual exclusion; it does not replace it with a racy
load/store guard. No installable firmware or EG image was generated.

## Why non-cacheable memory is a credible concern

A short stock-firmware assisted-QEMU boot supplies another observation. The
firmware's cache-range table at 0xa29dbf18 places 0xa97000cc in the range
0xa9700000..0xac400000 with flag1. The native cache helper at 0x101e3e2a treats
that flag as not cached. This is the firmware software classifier observed in
an assisted emulator, NOT a physical MMU/SoC capture.

[Arm's Cortex-A MMU guidance](https://arm-software.github.io/CMSIS_6/main/Core_A/mmu_c_pg.html)
explains that uncached exclusive accesses rely on global monitors, which are
absent on some implementations; unsuitable memory attributes can cause STREX
failure. That is a plausible mechanism here. We have not established the
camera's actual translation attributes, monitor support, or failing PC.
No guessed cached alias or replacement RAM address has been put into code.

## Hardware correlation and remaining boundary

The full LCD, settings-I/O-disabled return-zero-worker, and read-only restore
profiles all register workers and all froze. Battery-only, fixed-thirds and
six-grid profiles omit workers and work by owner report. In the latest failure
the percentage appeared while controls were already frozen. No SD marker,
responsive interval before freeze, worker entry or physical file read was proved.

The combined evidence localizes a credible common failure path BEFORE callback
entry, but does not prove it was the camera's actual failure. Other native I/O,
scheduling, memory-attribute or exception faults remain possible. Weak CAS avoids
the demonstrated retry loop; if stores never succeed, callbacks never run. It
also cannot make an unsupported memory access safe or fix a data abort.

The source change is offline hardening only and is NOT installed. Before any
future flash, resolve the worker guard's physical memory binding and obtain
better target execution evidence, then rebuild/review the complete host and
installation/recovery path with fresh owner authorization. No further SD I/O
trial, host flash, rollback or speculative address patch is authorized here.

Evidence: `evidence/20261122-worker-exclusive-progress.json` and
`evidence/20261122-working-grid-menu-restored.json`. Raw range-table data,
compiled blobs, firmware and emulator logs remain private.
