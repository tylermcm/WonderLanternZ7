# Original Z7 development update — November 23, 2026

Work has moved beyond emulator-only testing. The latest LCD checkpoint has
been tried by the project owner on **one original Nikon Z7, C 3.80**. This
update publishes the source, test summaries and current limitations. It is
not a new ready-to-flash firmware release.

**Hardware status: owner-reported verification of the specific tests below,
with saved-file integrity checks. Photo/video documentation is pending. This
is not independent certification, verification of every feature, or proof
that another camera can be updated or recovered safely.**

**Experimental firmware can brick a camera or damage settings/data. Earlier
checkpoints froze camera inputs. Those particular trials were isolated and
retested after changes, but further faults remain possible. There is no verified
emergency recovery procedure. Read [RISK_NOTICE.md](RISK_NOTICE.md).**

## What has been tried on the camera

| Area | Observed result and limits |
| --- | --- |
| SD module host and worker | The owner installed the reviewed host and tested normal startup, menu/touch response and power-off. A previously failing worker comparison passed with the revised host; a visible worker counter advanced on the camera. This does not validate every callback or native service. |
| Rear-LCD battery percentage | The owner enabled and disabled the percentage and confirmed both settings survived normal shutdown/restart. Read-only card checks found valid records matching the reported ON/OFF sequence. Current scope is the rear LCD. |
| Custom pages / DISP | The owner reported Custom pages retained its setting after restart and DISP cycling worked. Menu navigation and responsiveness were also tried. This is not a separate visual verification of every preset, information group or focal overlay. |
| Grid selection | The owner reported working 3x3, Center cross, 6x6 and Off selections in the incremental LCD tests. All five shapes also have offline geometry checks; that is a separate kind of evidence. |
| Saved grid shape | On the latest checkpoint, the owner confirmed the selected grid returns after normal shutdown and after battery removal. Center cross and 6x6 both returned after normal shutdown; Center cross also returned after battery removal. Physical readback verified valid v3 records in both slots (Center cross generation0, 6x6 generation1), with the earlier record and both older settings files unchanged. |
| Basic shooting / playback / restart | The owner reported an overall pass of the combined test: DISP cycling, conditional focal-display check, autofocus, a few single photos, playback/photo zoom, return to shooting and saved configuration after 20 seconds off. Individual observations and lens/zoom details were not separately described; this is a representative smoke test. |

The latest module checkpoint is identified by SHA-256
`f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`
(21,560 bytes). This identifies the tested local build; **no BIN is included**
in this source update. Hardware observations do not transfer automatically to
other profiles, older hosts, later builds or different cameras.

Source-safe records include the
[grid hardware report](evidence/20261122-lcd-grid-persistence-hardware-result.json),
[physical first grid journal readback](evidence/20261122-lcd-grid-journal-readback.json),
[physical second grid journal readback](evidence/20261123-lcd-grid-second-journal-readback.json),
[combined owner smoke test](evidence/20261123-lcd-combined-smoke-hardware-result.json),
[battery journal readback](evidence/20261122-lcd-battery-journal-readback.json) and
[second battery journal inspection](evidence/20261122-lcd-battery-second-journal-readback.json).
These are text records of observations and checks, not photographic proof.

## What remains open

- After battery removal, the wrong grid can appear for a split second before
  the saved grid appears. The owner reports normal controls throughout. The
  visual transition's cause has not been physically measured or established.
- Center cross and 6x6 have physical v3 journal readbacks and two-slot
  preservation checks. The core combined LCD smoke test also has an owner pass.
  Hardware coverage remains representative; 277 additional instruction checks
  cover preset edits/reset/save/reload combinations without requiring a separate
  camera restart for every toggle.
- Basic single-photo/playback and normal restart have an overall owner pass.
  EVF, movie, external output, burst/long exposure and full sleep/wake/interrupted
  shutdown lifecycles are not cleared by that smoke test. Portrait, zebras, the custom information
  page and broader histogram/highlight work remain outside this first LCD scope.
- The separate Golden-ratio spiral experiment still has reported electronic-level
  lag, especially in the EVF. Its older result is not validation of this profile.
- No deliberate interruption of an active settings save has been tested on
  hardware. Checksums, normal power cycles and emulator fault injection do not
  establish abrupt-power-loss durability or camera recovery.

## What is in the code update

The source includes the original-Z7 module host, incremental LCD/display
checkpoints, native grid and compact DISP controls, and versioned preference
storage. The latest grid profile writes only new `Z7DSP0.DAT` / `Z7DSP1.DAT`
journals; compatible older `Z7CFG` files are a read-only fallback. The
[exact checkpoint review](LCD_GRID_PERSISTENCE_REVIEW.md) explains its format,
installation assessment, preservation plan and rollback limits.

The exact latest packet passed 152 grid-preference/codec/file checks, 262
grid/storage assertions with 450 geometry comparisons, 15 native menu-status
checks and a bounded writer/worker preemption check. An independent rebuild
scanned 84 module functions with no exclusive instructions. The root suite
passed 101 tests. These checks use supplied native-service boundaries and do
not substitute for hardware testing.

The published `v0.1.0-grid-preview.1` source/patcher prerelease is an older,
separate preview. It does **not** contain this LCD checkpoint. No stock or
modified Nikon firmware, generated module binaries, dumps, keys or camera
screenshots are redistributed with this update.

## Credit where it belongs

This port builds on **[JKWTCN/z7ii-extensions](https://github.com/JKWTCN/z7ii-extensions)**,
pinned at [`50a22b24c50619cffa646dac386e8334659f475a`](https://github.com/JKWTCN/z7ii-extensions/tree/50a22b24c50619cffa646dac386e8334659f475a).
JKWTCN's module framework, format/relocation/build approach and custom-DISP
concepts are an important foundation for this work. Their copyright, MIT
license and component notices are retained.

Original-Z7 addresses, native bindings, ownership/scheduling adaptations,
validation and these incremental camera checkpoints are independent local
work. Z7II hardware reports are not counted as original-Z7 verification, and
this port is not an official or endorsed upstream release. See
[CREDITS.md](CREDITS.md) for the other upstream projects and their separate
licenses, and [UPSTREAMS.json](UPSTREAMS.json) for pinned provenance.
