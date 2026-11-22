# CLREX-only addition control - November 22, 2026

Owner authorized continuing the one-step investigation. Ordinary read passed on
camera with Center [RD OK]. This control adds only
CLREX to the probe function; no exclusive-load/store trial or
firmware update is included. Earlier combined exclusive probe is withdrawn.

Exact Z7APP.BIN: 5,664 bytes, SHA-256
`e55eda505bca7bca749acb52931ae614afd57e2170dd6273528cec29e7e1882f`.
Private build: `.private/builds/20261122-worker-guard-clear-01`.

The module retains battery/six-grid components and the manual Center trigger,
host API/code-signature check, zero-worker checks and one-attempt state latch.
The probe function executes one CLREX followed by the proven ordinary volatile
LDR on 0xa97000cc. No exclusive load or store is executed.
It writes no host words, registers no worker, and performs no file I/O. It uses
no LDREX or STREX. The old exclusive instruction signature remains data
for identifying the installed host, and is never executed by this module.
Boot/menu entry/other grid choices do not trigger the guard read.

## Preservation and installation

Identify the same external Sony card, verify all previous named file hashes
against the previous verified backups. Require active Z7APP.BIN to match the
working read control SHA10864694... and preserve it under the unused name
Z7APP.GUARD-READ-WORKING.disabled before creating the new module. Stop on a name
collision or unexpected active file. Back up named
payloads/seed/configuration files if present privately. Inventory existing file
metadata and hash the catalog. Exclusively add this exact Z7APP.BIN; flush and
verify full readback, previous contents and metadata (except the intended rename),
unchanged catalog and identity,
then safely eject. Preserve every existing disabled file and photo. Never
enable EG161080.BIN or replace existing payloads. Stop on unexpected contents.

## One manual observation

1. With the camera off, insert the card and start normally. Do not run Update.
2. Open the grid-choice menu. If Center reads `[CL host]`, stop and report it.
3. Select `Center [CL run]` once. Leave/reopen the menu and report the exact
   Center label and whether selection stayed responsive. `[CL OK]` means the
   ordinary read returned zero; `[CL busy]` means a nonzero guard or registered
   worker blocked the control. `[CL begun]` means completion was not recorded.
4. Check normal power-off. Do not repeat/reboot for additional attempts yet.

If selection stalls, do not press it again. The previous combined probe
recovered after about 12 seconds by owner report, closing the menu and restoring
control with the card present; a battery pull was the alternative. Wait for
recovery if it occurs and report the label by reopening only, without selecting
again. Do not run firmware Update. If controls remain unresponsive, prior card
removal/battery isolation was effective, but recovery for this exact candidate
is not independently established. Preserve/disable it on the laptop afterward.

A pass establishes that CLREX plus the ordinary read returned in this context;
it does not establish LDREX/STREX support. A freeze would keep address/native-menu/state
issues open and require investigating them before another exclusive operation.
No physical PC, exception type, MMU state or guaranteed recovery is captured.

## Offline scope

Build reproduced twice. Four supplied cases cover zero guard, nonzero guard,
registered-worker refusal and wrong-host signature. Checks require no guard
reads before selection, exactly one when allowed, no repeats, no host-word
writes, expected labels, no worker registration and no file I/O. Existing battery
policy audit runs on the exact file. Native service boundaries remain supplied;
these checks do not establish camera acceptance or exclude a physical stall.
Private evidence: `.private/evidence/20261122-worker-guard-clear-01.json`.
