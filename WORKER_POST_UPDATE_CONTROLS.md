# Controls after the host update - November 22, 2026

Hardware follow-up: owner confirmed the host update, then A and B both working
without issues. B is the exact empty-worker packet that froze on the old host.
The targeted responsiveness checkpoint passes on camera; no direct callback-entry
marker, installed-image readback, physical fault PC or persistence clearance is
claimed. See evidence/20261122-post-host-B-result.json. Older pending-test and
not-installed statements below describe earlier checkpoints.

Owner reports the exact host-only update worked with no failures or freezes.
This is a general update/basic-operation pass, not a readback of installed code
or a successful worker callback test. Preserved previous-host/stock inputs do not
establish emergency recovery. Do not repeat the firmware update.

Use the existing frozen review controls at
`.private/review/20261122-worker-guard-host-01/controls/`.

| Step | Behavior | Z7APP.BIN SHA-256 |
| --- | --- | --- |
| A / disabled | Battery/six grids, no worker registered | 412dffaf9a2b5f9aa5cf9e715b66e778e9de1e9f4c67eabc2963df7899a200f9 |
| B / enabled | Identical plus return-only worker | 767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158 |

Both files are 5,324 bytes and differ only by one flag and CRC. They reproduce
the old-host A pass/B freeze packets exactly, with no restore/file I/O, new
selection atomics or GUI-seen wrapper. They passed the rebuilt host's full grid
and interleaved-worker audits. Physical scheduling and the fix remain unverified.

First preserve/disable the completed updater as
EG161080.WORKER-GUARD-HOST.disabled, without touching the previous
EG161080.BIN.disabled or any module/photo. Verify private backups, exact updater
hash f479950e... and the single intended rename. No active root BIN should remain.

After approval for A only: identify the same card, back up and verify every named
payload/seed/configuration if present, inventory file size/mtime and hash catalog.
Require no active root BIN; exclusively add A as Z7APP.BIN, flush, full readback,
verify other files/catalog unchanged and safely eject. Do not enable an updater.

With camera initially off, insert card and start normally; do not run Update.
Check battery percentage, MENU/touch, grid choices and about 30 seconds of normal
use, then normal power-off. Record actual owner result. A has no worker, so it
checks the familiar battery/grid baseline on the updated host first.

Only after A passes, separately approve B. Preserve A under an unused filename
such as Z7APP.POST-HOST-A.disabled and use the same backup/readback/eject process.
Repeat ordinary start, controls, grids, brief use and power-off. No new host flash.

If either trial stalls, do not repeat. If the camera recovers, report the actual
timing/state. Card removal and battery isolation previously restored controls;
that is prior experience, not a guaranteed recovery for these trials. Do not
remove power during firmware programming; no programming is part of A/B tests.
Return the card so the exact failed module can be preserved/disabled. Do not
automatically restore another module, run Update or activate settings/restore.

No active exclusive-address probe or store trial belongs on this card. A/B
success would establish a hardware checkpoint for the worker path, not clearance
of persistence, arbitrary module atomics or the entire feature release.
