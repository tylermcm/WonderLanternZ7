# Exclusive-load-only control - November 22, 2026

WITHDRAWN after owner reported an immediate matching freeze and slight screen
dim on selection. Battery removed; no result marker or physical PC captured.
Preserved as Z7APP.GUARD-LOAD.disabled. Do not repeat this diagnostic. All prior
working files remain intact. The procedure below describes the completed trial.

Owner authorized continuing the one-step investigation. Ordinary read and CLREX controls both passed on
camera. This control adds one LDREX with the tested CLREX cleanup; no exclusive-store trial or
firmware update is included. Earlier combined exclusive probe is withdrawn.

Exact Z7APP.BIN: 5,664 bytes, SHA-256
`f8f4506fa30fe5379403f2a8f9ee6d919b2e4d60b31a94efeee8588ae7085a4a`.
Private build: `.private/builds/20261122-worker-guard-load-01`.

The module retains battery/six-grid components and the manual Center trigger,
host API/code-signature check, zero-worker checks and one-attempt state latch.
The probe function executes CLREX, one LDREX on 0xa97000cc, then CLREX cleanup.
No exclusive store is executed. Both cleanup instructions execute the same
CLREX operation that passed on camera in the previous control.
It writes no host words, registers no worker, and performs no file I/O. It uses
no STREX. The old exclusive instruction signature remains data
for identifying the installed host, and is never executed by this module.
Boot/menu entry/other grid choices do not trigger the guard read.

## Preservation and installation

Identify the same external Sony card, verify all previous named file hashes
against the previous verified backups. Require active Z7APP.BIN to match the
working CL control SHAe55eda50... and preserve it under the unused name
Z7APP.GUARD-CLEAR-WORKING.disabled before creating the new module. Stop on a name
collision or unexpected active file. Back up named
payloads/seed/configuration files if present privately. Inventory existing file
metadata and hash the catalog. Exclusively add this exact Z7APP.BIN; flush and
verify full readback, previous contents and metadata (except the intended rename),
unchanged catalog and identity,
then safely eject. Preserve every existing disabled file and photo. Never
enable EG161080.BIN or replace existing payloads. Stop on unexpected contents.

## One manual observation

1. With the camera off, insert the card and start normally. Do not run Update.
2. Open the grid-choice menu. If Center reads `[LX host]`, stop and report it.
3. Select `Center [LX run]` once. Leave/reopen the menu and report the exact
   Center label and whether selection stayed responsive. `[LX OK]` means the
   exclusive load returned zero; `[LX busy]` means a nonzero guard or registered
   worker blocked the control. `[LX begun]` means completion was not recorded.
4. Check normal power-off. Do not repeat/reboot for additional attempts yet.

If selection stalls, do not press it again. The previous combined probe
recovered after about 12 seconds by owner report, closing the menu and restoring
control with the card present; a battery pull was the alternative. Wait for
recovery if it occurs and report the label by reopening only, without selecting
again. Do not run firmware Update. If controls remain unresponsive, prior card
removal/battery isolation was effective, but recovery for this exact candidate
is not independently established. Preserve/disable it on the laptop afterward.

A pass establishes that exclusive load and CLREX cleanup returned in this context;
it does not establish STREX support. A freeze would keep address/native-menu/state
issues open and require investigating them before another exclusive operation.
No physical PC, exception type, MMU state or guaranteed recovery is captured.

## Offline scope

Build reproduced twice. Four supplied cases cover zero guard, nonzero guard,
registered-worker refusal and wrong-host signature. Checks require no guard
reads before selection, exactly one when allowed, no repeats, no host-word
writes, expected labels, no worker registration and no file I/O. Exact-candidate HUD smoke passes. The previous 38-check battery policy evidence
is reused only for unchanged battery/dependency source hashes; it is not claimed
as a fresh full policy run on this candidate. Native service boundaries remain supplied;
these checks do not establish camera acceptance or exclude a physical stall.
Private evidence: `.private/evidence/20261122-worker-guard-load-01.json`.
