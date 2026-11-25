# Combined LCD and movie orientation checkpoint

This independent MIT original-Z7 offline profile combines the existing
[LCD highlights build](LCD_HIGHLIGHTS_INTEGRATION.md) with the original-Z7
[movie orientation implementation](MOVIE_ORIENTATION_RESEARCH.md). The runtime
shadow and per-file orientation design credits JKWTCN's MIT Z7II work; native
bindings and relocation maps are independently derived for Z7 C 3.80.

## Exact candidate

Build with `tools/build_z7_lcd_volatile.py --movie-orientation`. The private module
is 35,348 bytes, SHA256
`79e3bff2780092409fbb8f751540053a289e08afa635a49ed0c69e9aa9285293`.
Two compiler passes produce identical bytes. Its minimum host API is 72; the
offline host MAIN hash is
`f77f0ced784403ffe99bd413c1ce71c07ecbd6a94e25c19919cb55a80c175b7c`.
**DO NOT STAGE: this module is incompatible with the installed API44 host.**
There is no host installation or recovery clearance for this pair.

Display initialization attempts movie callback publication only after fallible
registrations finish. A rejected movie guard leaves display initialization
successful and the native movie callback intact. Publication requires the
expected native callback/control binding, initialized idle mux state, zero
file count and no pending open/close. It fingerprints and prepares the runtime
shadows, cleans their code buffers, invalidates instruction/branch caches and
rechecks guards before publishing. These are necessary checks, **not proof of
task quiescence**. There is no live removal or hot-unload path.

Unlike the standalone prepare-only diagnostic, this cumulative profile attempts
publication during initialization. It is an offline integration experiment,
not a camera-approved default. A failed guard is not retried. Real startup timing
and publication coordination still need implementation and verification.

The LCD menu and version-4 `Z7EXT` preference schema remain unchanged. Movie
orientation has no new persistent setting. Earlier DSP/CFG journals remain
read-only fallback inputs as described in the highlights review.

## Verification and limits

- 44 cumulative startup checks: supplied idle, recording, active task,
  uninitialized task, pending open/close and foreign callback/control cases.
  Successful publication runs the copied open wrapper; highlight menus still
  open with highlights OFF by default. Initialization does not write settings.
- 828 renderer/codec checks on the exact cumulative binary. This separate
  fixture deliberately excludes movie publication; positive and negative
  startup coverage belongs to the preceding audit.
- 103 root tests pass. The highlights-only profile rebuilds byte-for-byte at
  `aa56f2b8...`; its previous checkpoint remains available independently.

The startup fixture explicitly supplies mux state 0 for the positive case;
the ROM's initial state 3 is a rejection case. Filesystem, GUI/kernel, pose,
cache-clean services and contexts are supplied. Native task scheduling,
physical cache behavior and camera responsiveness are not established.

The standalone implementation's 318 checks additionally exercise native track
construction and metadata serialization with empty sample descriptions and
supplied append/flush services. Those are separate standalone-binary results;
they do not establish playable output from this cumulative candidate.

A subsequent 30-check audit on this exact cumulative binary executes the native
event dispatcher across three supplied publication boundaries. It verifies
callback reload on the next event, native matrix fallback for an already-fetched
old callback, and immutable published code. It rejects automatic publication
during initialization and exercises explicit publication afterward; automatic
camera startup timing remains unverified. See the
[dispatcher review](MOVIE_ORIENTATION_RESEARCH.md#native-event-dispatcher-boundary).

The exact cumulative binary also passes 64 dispatcher-to-metadata lifecycle
checks: eight sequential file-slot reuse cycles, including open/split/close,
all four poses, actual native metadata serialization, native close-to-idle and
record-context cleanup. File operations, requests, empty descriptions and kernel
boundaries remain supplied. Actual file splitting, playable output, negative-I/O
lifecycle and physical scheduling remain pending. See the
[lifecycle scope](MOVIE_ORIENTATION_RESEARCH.md#dispatcher-to-metadata-lifecycle-checkpoint).

Playable MOV/MP4 output, recording/split lifecycle stress, task quiescence,
player compatibility, physical orientation and exact installation/recovery
review remain pending. No camera, card or firmware update was performed.
