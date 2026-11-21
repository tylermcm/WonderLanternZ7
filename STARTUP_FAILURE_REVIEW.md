# Original Z7 startup failure: offline findings

November 21, 2026. Full release withdrawn. All card trial files disabled.
No firmware or card deployment authorized by this review.

The owner reports normal controls and speed with the no-init diagnostic, but
the full module and settings-I/O-disabled diagnostic both freeze controls and
the power switch. Normal no-init operation does not prove its entry executed.
Camera responds normally without the card. The failed diagnostic was preserved
and disabled; the card was safely ejected. Installed host remains modified.

## Compiled initialization comparison

`tools/audit_z7_startup_publication.py` regenerates the two exact diagnostics
in memory from the preserved failed module, then runs all three through the
exact installed-host build with existing fixture boundaries. It writes private
evidence only. It does not generate a deployment payload or touch a card.

| Observation in instruction fixture | Full | No-init | Settings I/O skipped |
| --- | --- | --- | --- |
| Loader returns status 8 | Yes | Yes | Yes |
| Settings-file operations during init | 2 missing-file opens | 0 | 0 |
| Native menu object and dispatcher published | Yes | No | Yes |
| Publication precedes host display readiness | Yes | No publication | Yes |
| Sampled load stack depth in bytes | 1724 | 1068 | 1068 |
| Owner camera result | Freeze | Normal controls | Freeze |

The trace captures native writes, not merely source ordering. In both variants
with initialization, `sm_publish` writes the page-zero object header at
0xa1833548 and the native event dispatcher at 0xa182ed34 while host
`display_ready` is zero. Host readiness is published only after module entry
returns. The dispatcher is reachable through a direct native pointer rather
than the host display callback readiness gate.

Sources: `examples/settings_menu_policy.h:393` and `host/z7_380.c:1142,1192`
under `z7-native-modules`. The APPIDLE descriptor copied by `z7_module_boot`
contains an 8192-byte stack. Stack observations sample basic-block boundaries;
they are lower bounds and exclude supplied service internals and task-entry
wrapper effects. They do not establish a hardware stack safety margin.

## What this establishes

Skipping settings preparation/worker is insufficient to prevent the hardware
failure. Native menu publication remains common to both failed variants.
The menu's worker-side publication and lack of an application/card-ready gate
deserve review before another hardware trial. Neither is a proven freeze cause.
The active EG update file was unnecessary for the second recurrence, assuming
the card remained as staged; its absence was verified before that trial.

The old fixtures execute one task and supply kernel, filesystem and selected UI
services. They seed native runtime RAM and application state. They cannot show
what another camera task does during these writes or whether startup services
are actually ready. More green fixture checks cannot clear hardware acceptance.

## Next offline work and acceptance boundary

Review native menu ownership/lifecycle and the pinned upstream readiness gate.
Determine which native task may safely publish the menu; model task preemption
and startup state changes at publication boundaries. Any proposed sequencing
change must preserve existing menu ownership and prevent partially published
objects from being consumed. Merely moving `display_ready` earlier would expose
callbacks sooner and is not an established repair.

Do not alter firmware behavior on the strength of this correlation alone.
Do not stage another diagnostic automatically. A future camera proposal needs
new consent, exact artifact review, preservation and a recovery assessment.
Persistence remains required for the actual smaller LCD release.

Validation: all 95 existing root tests pass; three exact-artifact initialization
traces satisfy publication-order assertions. These results validate the offline
audit scope, not a repair. No camera test, firmware image, or card write occurred.
