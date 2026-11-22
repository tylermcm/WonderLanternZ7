# Exact last-working versus frozen module comparison

November 22, 2026. Comparison only: no card changes, new camera test, firmware
image or deployable diagnostic generated. Working six-grid module remains restored.

The most useful delta is registration of a background worker callback. The
native loader task and its host code already exist in both cases. Registration
allows the failing build to reach the host's exclusive-store guard before any
module worker code, GUI-ready check, record decoder or settings-file read.
This is a narrowed failure hypothesis, not a physical root-cause confirmation.

## Exact artifacts and changes

Working: owner-confirmed battery/six-grid module, SHA-256
`53334536d00ed18ea9d80d36dd736d6341fd1943da674f6e0fd513112f226195`.
Frozen: read-only restore module, SHA-256
`0714fe8491b4e802406ed0867f0c5ecacc3ceb4c573feecceb742364b2c4bf95`.
Both frozen review manifests identify the same installed host MAIN:
`7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057`.
The recent offline weak-CAS source change was NOT installed and is not used
in this comparison.

| Area | Working | Frozen |
| --- | --- | --- |
| Module file | 5,260 bytes | 6,628 bytes; +1,368 |
| Image / BSS | 5,120 / 2,216 | 6,464 / 2,260 |
| Relocations / minimum API | 19 / 20 bytes | 25 / 44 bytes |
| Native task, host, stack descriptor | Existing loader task / API44 host / 8KB | Same |
| Battery component and sample policy | Original source | Identical source hashes |
| Six grids and native On/Off | Working volatile choices | Same mechanism, with restore hooks |
| Actual display hooks | Grid source/geometry; battery before/after | Same, but after calls `restore_after` |
| After-paint wrapper | No restore flag | Calls original battery `after`, then publishes GUI-seen flag |
| Worker registration | Absent | Added `restore_worker` |
| Worker body | None | GUI-ready check, file open/read/close and decode |
| Grid selection adapter | Volatile assignment and normal On setter | Adds atomic revision increment first |
| Grid-menu entry/text | Original choices | Conditional restore and SD status labels |
| Seed file | Not required/read | New 80-byte `Z7GRID.DAT` |
| Custom settings page, dispatcher/key replacement, mask edits | Absent | Absent |
| Module filesystem writes | Absent | Writer excluded at compile time |

The 44 extra BSS bytes are accounted for by four restore-state words (16), the
file context (20), and two staging flags (8). Existing battery source is unchanged;
its binary addresses move because code/layout changes. Comparing file offsets
alone would conflate relocated code/data with behavioral changes.

## Same-size controls executed only in memory

`tools/compare_z7_working_restore.py` loads the exact failed module and performs
two minimal modifications, resealing only its CRC. File length, entry offset,
image/BSS sizes, relocation table, strings, seed input and all other bytes stay
unchanged. The modified packets are never saved or staged.

1. Skip worker registration: replace its two-byte indirect call at image offset
   2262 with a success return value. Keep every restore function/hook in place.
2. Empty worker: keep registration but replace the four bytes at worker entry
   offset 2304 with return-zero instructions. No file operation can execute.

The native load and GUI percentage succeed for all variants with supplied
kernel/filesystem/telemetry services. Then inject persistent exclusive-store
failure at the exact installed host guard:

| Variant | Worker registered | Worker entered | Settings operations | Tick returns |
| --- | --- | --- | --- | --- |
| Exact working file | No | No | None | Yes |
| Exact frozen file | Yes | No | None | No; guard retries |
| Frozen, registration skipped | No | No | None | Yes |
| Frozen, empty worker | Yes | No | None | No; same guard retries |

With normal exclusive-store behavior, the original frozen worker enters and
performs open/read/close; the empty worker enters and returns without file I/O.
This verifies the controls have the intended distinction. The same-size controls
remove payload-size/layout as an explanation of these simulated differences.

The execution order matters: registration -> host guard -> callback -> GUI-ready
check -> file read. The post-GUI condition is inside the callback, so it cannot
protect against an earlier host-guard stall. Increasing a delay or changing the
file parser would not resolve that particular stall.

## A second new exclusive loop

The frozen profile's `restore_selected` uses atomic fetch-add as a user-choice
flag. It is inlined into its grid-choice handlers. The working profile has no
exclusive operations there. For example, the frozen Center-cross handler has
LDREX at image offset 5200 and STREX at 5206, before the normal On/Off setter.

The comparison injects failure at that store too: the frozen handler retries
and never calls the setter; the working handler returns normally. This is a
separate latent exclusive-progress problem. It does not explain a startup freeze
unless that selection handler actually ran. The owner reported controls already
frozen when the percentage appeared, so the pre-callback host guard remains the
better first point to isolate for that observation.

## What is narrowed and what is not

The newly enabled host worker guard is the earliest demonstrated stall before
the restore I/O. Earlier full/settings-disabled failures also registered workers,
including the return-only-worker case. This strengthens the guard hypothesis
without proving physical exclusive-store failure. No target PC, MMU/monitor
capture or worker-entry marker was obtained on camera. The record/parser/native
file service can still have independent faults once execution gets past it.

The next discriminating experiment should separate worker registration from
worker-body execution while holding the failed packet's layout constant. It
would require a separate exact review and explicit camera-test approval. No such
test is prepared for deployment or authorized by this comparison.

Validation: exact file/header checks, runtime API-registration traces, normal
versus failed-exclusive-store runs for four variants, and old/new grid-selection
handler runs (ten controlled execution cases), with stack/callee-save checks on
normal returns. UI/kernel/filesystem/telemetry and exclusive failure are supplied
boundaries. Whole-camera freezing and physical recovery are not reproduced.
Raw firmware and generated binaries remain private.

Machine-readable evidence: `evidence/20261122-working-versus-frozen.json`.
