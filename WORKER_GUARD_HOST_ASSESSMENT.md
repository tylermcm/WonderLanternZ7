# Worker guard host-only update assessment - November 22, 2026

Prepared for owner review. No card staging, firmware update or physical fix is
authorized or completed by preparing this assessment. Original Nikon Z7 only,
pinned to the original C 3.80 firmware input. Independent modified MIT host;
firmware inputs, binaries and the complete review bundle remain private.

## Exact change and candidate

The worker dispatcher is private to the resident loader task. An ordinary
task-owned recursion flag replaces LDREX/STREX on the guard at 0xa97000cc. This
is not a cross-task mutex. The existing 44-byte module API and 256-byte state
layout remain unchanged. No file restore, persistence, custom dispatcher,
portrait, zebras or extra output modes are included in this test.

The complete display host has been rebuilt from the pinned original input,
including regenerated native bridges; this is not the earlier in-memory overlay.
Host code is the exact reproducible 4,573-byte blob already audited for zero
exclusive instructions in the worker guard. Native bridge addresses changed as
required by the new code layout.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| New EG161080.BIN | 33,058,842 | f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140 |
| New MAIN payload | 33,058,840 | 24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce |
| Previously installed host EG | 33,058,862 | fa709dba7eb7a9addc8bd5b90f839edd578cfb6d4bb0df87a1cd8cb4a7beaa4d |

Complete private host build: `.private/builds/20261122-worker-task-display-host-01`.
Private exact review: `.private/review/20261122-worker-guard-host-01`.
The review also preserves the previous host, untouched stock module/container,
and A/B modules separately. None is copied to the card by the review tool.

## Evidence and limits

Hardware controls established ordinary guard read and CLREX control passed;
CLREX/LDREX/CLREX reproduced the freeze without STREX or a retry. No actual
exception, physical PC or MMU attributes were captured. The revised guard avoids
that access pattern, but a physical fix has not yet been demonstrated.

Complete host rebuilt twice with identical bytes and valid EG CRC. Offline checks:

- 99 loader checks, including actual native workspace/task wrappers, single task
  creation, delayed/missing module handling, cache publication and failure cleanup.
- 55 worker checks, including callback bounds, initializer rollback, recursion,
  legacy API rejection and the actual resident task loop.
- 316 display checks including native paint bridge, geometry and histogram
  fallback, and 2,114 indexed-property reads per image against stock.
- Exact A/B pair: 270 grid checks and 450 geometry calls each, then 64 interleaved
  GUI/worker ticks each. B callback enters 64 times, guard returns to zero and no
  module file I/O occurs. A callback is never entered.
- Prior implementation checks: local dispatcher ELF binding, sole production
  caller, zero guard exclusive instructions, four guard traces and 99 root tests.

The A/B files reproduce the camera-tested packet hashes exactly: A412dffaf... and
B767ada05... . Their current source fingerprints are refreshed; code is unchanged.
They are controls for later steps, not payloads for the first host-only update.

The review independently rebuilds the complete host again, verifies all CRCs and
hashes, and runs selected native header/name/capacity probes for the exact candidate
and preserved inputs. Those probes supply file/property boundaries. They do not
exercise full updater admission, erase/program/readback, real scheduling or boot.
An earlier modified host update was owner-confirmed accepted; acceptance of this
exact new update and recovery from a failed host boot remain unverified.

## Proposed first step: host only

Obtain explicit approval for this exact host-only update test before staging.
Confirm the camera still starts normally without the card, its Setup firmware
screen reports C 3.80, and its battery is fully charged. If the model/version or
normal boot differs, stop and reassess. No updater downgrade/version bypass is
part of this plan.

On the laptop, identify the same Sony card, back up and verify all named firmware,
modules, seed and configuration files if present, and inventory existing metadata
and catalog. Require no active root BIN. Preserve every disabled payload and
photo. Exclusively create ONLY EG161080.BIN from `host-only/`; flush and full-readback
verify its exact hash/CRC, verify existing contents/metadata/catalog and identity,
then safely eject. No active Z7APP.BIN, no A/B/control module or settings write.

For an approved test, the owner uses the camera's normal manual firmware-update
menu with this single EG file. Do not interrupt an update in progress. After the
camera reports completion, follow its power-off instruction. First check ordinary
no-card cold boot, MENU, touch and normal power-off. Then inspect/preserve and
disable the completed update file on the laptop before any later module trial.
Stop on an error or abnormal behavior; do not run repeated updates as a diagnosis.

Only after the owner confirms the new host behaves normally do we separately
review/stage A (worker disabled), record that result, then B (same empty worker
that froze on the old host). No automatic advance, settings/restore trial or
exclusive-address probe is included. Existing probes that fingerprint the old
guard should not be reused with this host.

## Recovery boundary

The current old host with no active module boots normally by owner report. Every
SD-triggered failed payload was preserved/disabled; no-card recovery is confirmed.
That does not guarantee recovery from a faulty replacement host, which executes
even with no card. Removing the card could therefore be insufficient after a host
update. Battery removal is not a remedy to apply during flash programming.

The exact previous host and original stock inputs are preserved as possible
normal-menu reflash inputs if the camera still boots and accepts them. Restoring
either is a separate deliberate action requiring review/authorization. They are
not a demonstrated emergency recovery mechanism. There is no verified installed
image readback, hardware debugger/programmer or unbootable-camera recovery path.
If the new host prevents normal no-card boot or updater access, stop software
trials; further recovery cannot be promised by this lab.

These limits are material to approval. A successful software audit cannot clear
flash acceptance or recovery. No physical fix or finished feature release is claimed.
