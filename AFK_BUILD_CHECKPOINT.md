# Offline build checkpoint - November 22, 2026

Current follow-up: November 22 LCD save/restore package is complete offline.
See [LCD_PERSISTENCE_CHECKPOINT_REVIEW.md](LCD_PERSISTENCE_CHECKPOINT_REVIEW.md)
and the newest HANDOFF entry. Owner-working RAM-grid module remains active; no
card change or new firmware flash. New candidate88b53ce4 has six passing reports;
startup-only hardware gate precedes any preference-write test. The milestones
below are historical: worker progress, read-only restore and volatile LCD/grid
now have scoped owner passes. Grid-shape persistence remains unfinished.

The owner-tested host and active empty-worker B remain the working hardware
checkpoint. No card writes, camera operations or firmware builds/updates were
performed during this AFK work. All new SD modules below remain private,
unstaged and hardware-unverified. No permission question is pending while away.

## Completed

| Checkpoint | Result | Hardware status |
| --- | --- | --- |
| Visible worker progress | Off menu row shows a single-writer counter; no extra file I/O or worker UI writes | Next proposed test |
| Hardened read-only seed restore | Replaced selection fetch-add with GUI-owned monotonic latch; still read-only | Gate after progress observation |
| Persistence publication | Replaced revision fetch-adds with single-writer odd/fence/payload/even publication | Regression-tested offline only |
| Storage-free LCD profile | Existing four presets/compact menu/battery/focal/grid/horizon controls without worker or persistence | Separate UI/overlay test candidate |

Details and exact installation/recovery boundaries:

- [Worker progress](WORKER_PROGRESS_REVIEW.md)
- [Read-only restore](RESTORE_NO_RMW_REVIEW.md)
- [Persistence ownership and checks](PERSISTENCE_PUBLICATION_REVIEW.md)
- [Storage-free LCD](LCD_VOLATILE_REVIEW.md)

The no-I/O progress review is the next test to discuss on return. Storage-free
LCD menu/overlay testing and read-only restore can then be scheduled as separate
steps. Persistent/full LCD activation remains behind those observations; no
automatic jump to a write-capable module is authorized.

## Validation

101 root tests pass. Both progress and read-only restore pass 270 grid checks
and 450 geometry calls each; restore also passes 52 codec/fault/preemption checks.
Progress checks cover count formatting/carries/saturation/reset, GUI read-only
sampling, no worker text/UI effects and no settings file I/O.

The broader persistence diagnostic passes 84 checks. A new actual-writer test
pauses after the odd revision store, runs four bounded worker reads on a separate
stack without I/O, resumes the GUI writer, and saves the completed even revision.
The persistent LCD candidate's 48 compact menu/legacy/save/DISP checks pass; the
storage-free variant separately passes 44 checks and ignores existing journals.

Compiled scans find no exclusive instructions in 28 progress, 34 read-only
restore, 91 persistence-diagnostic, 83 persistent-LCD and 68 volatile-LCD function
ranges. Native firmware callees are outside the scans. All new candidates build
reproducibly. Current working A/B packets rebuilt byte-for-byte unchanged.

The optional builder function-bound export leaves default packets/reports
unchanged; tests check that contract and reject out-of-image function bounds.
Code graph refreshed after edits; existing conditional-C parser limits remain.

The model/file formats and v1 journal are unchanged. Single-writer/GUI ownership
remains a requirement; no replacement spinlocks, guessed cached aliases or native
mutex addresses were introduced. Remaining advanced highlight/cache/portrait RMW
sites were left alone and remain deferred. Emulator success does not establish
physical execution, native rendering/lifecycle, card durability or recovery.
