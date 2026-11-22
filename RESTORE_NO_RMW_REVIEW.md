# Hardened read-only restore checkpoint - November 22, 2026

Prepared offline while the owner is AFK. Not staged, not hardware tested and not
cleared for automatic activation. The next hardware checkpoint is the no-I/O
progress marker; review its result before considering this separate read test.
The failed old restore file remains preserved/disabled and must not be reused.

Exact new module: 6,564 bytes, SHA-256
`839d8aaef7f404ba64f710d092aceba628552b969e54820867bd6b6d4c363b40`.
Private build: `.private/builds/20261122-grid-restore-no-rmw-01`.
The private 80-byte Z7GRID.DAT seed defaults to choice5 (6x6), SHA-256
`a0b38b760a81b292131af5944fa3ade0ce48bc9e21e9a424b712dc2368567ae0`.
An identical inert seed was already preserved on the card. Future staging must
inspect/back up the actual seed and never overwrite an unexpected existing file.

The worker still waits for the existing eligible battery GUI signal, performs
one read-only seed read, and publishes a validated result for GUI menu entry.
It does not write files, save settings, apply menu choices from the worker, retry
I/O or change native On/Off visibility. The GUI owns applying the restored layout.

The old selection revision fetch-add is replaced by a monotonic GUI-owned latch:
any owned layout selection (choices1..5) sets it to one. Menu entry checks it and
skips a pending restore instead of overriding that user choice. The worker never
writes this latch. Native Off continues to control visibility independently.
Other worker/GUI publication words keep aligned acquire/release loads/stores.
All 34 ELF-bounded compiled functions contain zero exclusive instructions.

Offline checks passed: 270 grid/publication checks, 450 geometry calls, 52 restore
codec/fault/preemption checks, repeated selections keeping the latch at one,
selection after ready vetoing restore, and actual selection while a worker read
is paused on a separate emulated stack. Missing/short/long/corrupt records and
open/read/close failures remain bounded/read-only; uncertain close parks the
adapter. These are supplied filesystem/native-service cases, not real-card proof.

The GUI signal is not a verified card-ready query. Real filesystem scheduling,
cache coherence, menu appearance and recovery remain unverified. The normal host
and empty-worker pass do not clear this I/O path. A future approved test needs
fresh card identity/backups, preserved working progress/B module, exclusive file
creation/readback/eject, then a normal start and SD marker/menu/controls result.
No firmware update, camera-side write or full-release trial is included.

Private evidence: `.private/evidence/20261122-worker-progress-restore-01.json`.
