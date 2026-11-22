# Visible worker-progress checkpoint - November 22, 2026

Offline preparation only. User is AFK; no card staging, camera operation or new
firmware update was performed. Keep the owner-tested B module active until this
new SD checkpoint is reviewed and approved with the owner present.

Exact Z7APP.BIN: 5,452 bytes, SHA-256
`3b5aced1e58f56ebad9d5f945452254d82614549e6904acb5ff3d460909e51a9`.
Private build: `.private/builds/20261122-worker-progress-checkpoint-01`.
Requires the owner-tested revised host, EG SHA f479950e... . Do not install it on
the old exclusive-guard host. No firmware update belongs in this test.

## Added behavior

The working battery/six-grid base and one registered worker remain. The callback
now increments a single-writer counter using aligned atomic loads/stores, with
no atomic read/modify/write, file operation, allocation, native UI call or text
write. The count saturates at 9999. Menu entry samples it once and formats the
existing Off row as `Off [W 0003]`, for example. The GUI owns the text buffer.
The worker never paints or changes menu objects. Other grid labels, choices,
native On/Off storage, and EVF/movie fallback behavior are unchanged.

Two increasing values on separate menu openings would directly demonstrate
callback execution on camera. The counter is volatile, starts at zero each boot,
and is not a settings persistence feature. It may already be nonzero on the
first menu opening. Menu openings themselves do not increment it. Native delay
units and physical callback cadence remain unmeasured; no fixed update interval
is promised. An unchanged value or saturation needs observation, not repeated
probe selections or a firmware update.

## Proposed card/test sequence

After approval, identify the same card and require active Z7APP.BIN to match the
working B767ada05... module. Privately back up named payloads/seed/configuration
files if present and inventory size/mtime/catalog. Preserve B as an unused
Z7APP.POST-HOST-B.disabled; stop on a collision or unexpected active file.
Exclusively create the progress module, flush/full-readback verify it, verify all
other contents/metadata/catalog unchanged, then safely eject. Keep all updaters
disabled. No deletion, formatting or overwrite of existing files.

1. With the camera off, insert card and start normally; do not choose Update.
2. Check ordinary controls and battery percentage. Open the grid-choice menu
   and read the Off row's W number; no selection is required.
3. Leave the menu, use the camera briefly, reopen the same menu and report both
   numbers and responsiveness. Do not select a retired EX/LX diagnostic.
4. Check normal power-off. Stop on a stall and report its trigger/timing. If it
   recovers, record the label before a battery pull if possible; do not repeat.

Prior card removal and battery isolation recovered earlier SD-triggered stalls;
that is not a guarantee for this new module. Never interrupt firmware programming
with battery removal; this SD test performs no firmware programming. Return the
card for preservation/disable if it fails. Do not auto-activate the restore build.

## Offline evidence

Build reproduced twice. All 28 ELF-bounded module functions were scanned with
zero LDREX/STREX/CLREX instructions. Checks cover 270 grid/publication/geometry
assertions and 450 geometry calls, early worker ticks with no GUI calls, exact
digit/carry boundaries, saturation, fresh-load reset, unchanged count on GUI/menu
events, busy guard refusal, no text writes from worker and no extra file I/O.
The exact compiled code ran against the complete regenerated host.

Native UI/kernel/telemetry services remain supplied; this does not establish
physical scheduling, label appearance, callback cadence or recovery. The old B
responsiveness pass remains the current hardware checkpoint.
Private evidence: `.private/evidence/20261122-worker-progress-restore-01.json`.
