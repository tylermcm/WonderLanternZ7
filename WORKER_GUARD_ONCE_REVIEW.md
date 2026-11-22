# Manual single-attempt guard probe - November 22, 2026

Owner requested a diagnostic test after matched A worked and B froze. This is
an SD module only; no new firmware image, update or host-code patch is involved.
Prepared candidate is private and not yet staged. Windows currently sees the
reader but no card media. Earlier B remains disabled; working A is preserved.

## Exact candidate and operation

Z7APP.BIN is 5,664 bytes, SHA-256
`83ab23cadd63e902fb252cbb563f8b262ceac9e2e9ec332c0e0344be4ce2e99c`.
Private build: `.private/builds/20261122-worker-guard-once-01`.
Includes the working battery/six-grid components with manual selection/label hooks.
It registers no worker and performs no file I/O or firmware/code writes.

At initialization it checks the API's register-worker address and 28 exact bytes
of the installed original host's guard code. A mismatch blocks the probe and
labels Center as `[EX host]`. It does not attempt exclusives during boot, paint,
menu entry or ordinary grid selection. Selecting Center explicitly runs it once.

The manual probe first checks that both worker registration words are zero.
It executes one LDREX on the exact host guard at 0xa97000cc. If that value is
nonzero it clears the exclusive monitor and skips the store. Otherwise it makes
one STREX storing the same zero value, clears the monitor and returns its status.
There is no retry or wait loop. Successful storage preserves the guard contents;
this does not acquire the lock or call a worker. Repeated Center selections in
the same boot do not repeat the attempt.

## Card preservation and staging

User's request authorizes preparing/testing this bounded diagnostic. When the
card is connected, positively identify it against the previous private identity,
verify no active root BIN, and verify all earlier payloads and seeds against the
quarantine backups. Stop on unexpected active BINs or changed prior payloads.
Back up all named files and configuration files if present privately, inventory
existing file metadata, and fingerprint the catalog. Exclusively create only
Z7APP.BIN from the exact candidate; flush and full-readback verify it, verify all
prior named contents and metadata/catalog unchanged, then safely eject.
Do not enable EG161080.BIN, rename working A, delete photos or overwrite anything.

## One manual camera test

1. Start normally with the camera initially off. Do not choose firmware Update.
   Battery percentage and controls should behave like the working version.
2. Open the existing grid-choice menu. Center should read `Center [EX run]`.
   If it shows `EX host`, stop and report that label; the probe is blocked.
3. Select `Center [EX run]` once. If controls remain responsive, leave/reopen
   that grid menu and report the exact Center label. Then check normal power-off.
   Do not reboot to repeat the attempt without reviewing this result.
4. If it freezes, report whether boot, opening the menu or selecting Center
   triggered it. Stop; do not repeat or run Update. The card can be connected
   again to preserve/disable this exact diagnostic.

| Result | What it establishes | Remaining limit |
| --- | --- | --- |
| EX OK | One exclusive store returned success on this word in menu context | Does not establish worker-task success or exclude intermittent failures |
| EX fail | One exclusive store returned failure without hanging | Could be spurious; not proof every worker attempt fails |
| EX busy | Worker words were populated or the guard was nonzero; no successful probe | Needs state review; do not force/reset the guard |
| EX host | Code/API check failed; no exclusive attempt | Wrong binding or code mismatch needs review |
| Freeze specifically on selection | Failure occurs on the manual guarded probe path without a retry loop | Could be access exception/stall; no physical PC or exception type captured |

This test differs from the failing host worker in execution context (menu rather
than task) and stored value (zero rather than acquisition value one). It examines
exclusive access to the same physical-binding address; it does not replace the
original A/B evidence or prove an exact exception/instruction on the camera.

## Recovery and checks

The owner confirmed normal camera response without the card after B. Previously
card removal restored inputs and battery removal was needed when power remained
unresponsive. That is observed prior recovery, not a guarantee for this new probe.
If frozen, stop; use card-removal isolation and normal power-off if it responds.
If power remains unresponsive, battery removal was the prior recovery method.
No independently verified stock restoration or physical debug recovery exists.
This candidate could still freeze on an exclusive-access exception despite having
no retry loop. It supplies no exception handler or recovery firmware.

Build reproduced twice. Five offline paths cover success, one injected failure,
nonzero guard, registered-worker refusal and host-signature mismatch. They check
manual-only/single-attempt behavior, labels, unchanged host words and no file I/O.
Existing battery policy audit also runs against the exact candidate. These checks
use supplied native services and do not establish camera acceptance or recovery.
Private evidence: `.private/evidence/20261122-worker-guard-once-01.json`.
