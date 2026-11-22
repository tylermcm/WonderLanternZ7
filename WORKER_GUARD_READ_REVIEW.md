# Ordinary-read control - November 22, 2026

Owner authorized continuing the one-step investigation. Only this plain-read
control is prepared for the next camera test; no exclusive-load/store trial or
firmware update is included. Earlier combined exclusive probe is withdrawn.

Exact Z7APP.BIN: 5,664 bytes, SHA-256
`10864694f04424d479adc4b61cc99dd7e3b512e70129621595f547428f888438`.
Private build: `.private/builds/20261122-worker-guard-read-01`.

The module retains battery/six-grid components and the manual Center trigger,
host API/code-signature check, zero-worker checks and one-attempt state latch.
The probe function now performs only one ordinary volatile LDR on 0xa97000cc.
It writes no host words, registers no worker, and performs no file I/O. It uses
no LDREX, STREX or CLREX. The old exclusive instruction signature remains data
for identifying the installed host, and is never executed by this module.
Boot/menu entry/other grid choices do not trigger the guard read.

## Preservation and installation

Identify the same external Sony card, verify all previous named file hashes
against the last quarantine, and require no active root BIN. Back up named
payloads/seed/configuration files if present privately. Inventory existing file
metadata and hash the catalog. Exclusively add this exact Z7APP.BIN; flush and
verify full readback, unchanged previous contents/metadata/catalog and identity,
then safely eject. Preserve every existing disabled file and photo. Never
enable EG161080.BIN or replace existing payloads. Stop on unexpected contents.

## One manual observation

1. With the camera off, insert the card and start normally. Do not run Update.
2. Open the grid-choice menu. If Center reads `[RD host]`, stop and report it.
3. Select `Center [RD run]` once. Leave/reopen the menu and report the exact
   Center label and whether selection stayed responsive. `[RD OK]` means the
   ordinary read returned zero; `[RD busy]` means a nonzero guard or registered
   worker blocked the control. `[RD begun]` means completion was not recorded.
4. Check normal power-off. Do not repeat/reboot for additional attempts yet.

If selection stalls, do not press it again. The previous combined probe
recovered after about 12 seconds by owner report, closing the menu and restoring
control with the card present; a battery pull was the alternative. Wait for
recovery if it occurs and report the label by reopening only, without selecting
again. Do not run firmware Update. If controls remain unresponsive, prior card
removal/battery isolation was effective, but recovery for this exact candidate
is not independently established. Preserve/disable it on the laptop afterward.

A pass establishes ordinary access and this menu path in this context; it does
not establish exclusive support. A freeze would keep address/native-menu/state
issues open and require investigating them before another exclusive operation.
No physical PC, exception type, MMU state or guaranteed recovery is captured.

## Offline scope

Build reproduced twice. Four supplied cases cover zero guard, nonzero guard,
registered-worker refusal and wrong-host signature. Checks require no guard
reads before selection, exactly one when allowed, no repeats, no host-word
writes, expected labels, no worker registration and no file I/O. Existing battery
policy audit runs on the exact file. Native service boundaries remain supplied;
these checks do not establish camera acceptance or exclude a physical stall.
Private evidence: `.private/evidence/20261122-worker-guard-read-01.json`.
