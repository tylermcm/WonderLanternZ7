# Findings and reusable lessons

These notes summarize independently implemented Z7 research experience without
publishing Nikon program bytes, assets or private traces. The compatible sample
and model boundaries are in the README and architecture document. Evidence from
one version must not be promoted to another camera's hardware fact.

## Separate three milestones

Parsing a firmware package, executing its program in an emulator, and loading
new software on a physical camera are different achievements. The Z7 experiment
provides assisted system emulation. It has no demonstrated physical-camera
execution entry. A QEMU Hello World or working UI does not establish a usable
camera add-on, signature acceptance or flashable image.

Magic Lantern is useful as a reference for emulator-assisted analysis, versioned
model profiles, diagnostic hooks, logs and incremental device modeling. It is
not an ABI or board specification for Nikon. No ML code is bundled here.

## Model waits before replacing behavior

RTOS initialization frequently blocks on a device condition or event flag.
First locate the producer, status/mask register, IRQ dispatch and consumer's
acknowledgment. A plausible return value can get past one wait while creating
an invalid state for a later task. Model meaningful transitions and ordering.

Keep read-only diagnostics distinct from HLE calls and RAM fixtures. An unchanged
firmware file does not imply an unmodified guest. Log the exact assistance and
what it does not model. Preserve negative controls so a later engineer can tell
which intervention was actually necessary.

## The CMOS → LCD chain needs several proofs

The early640×480 RAW source was an input tool, not a discovered physical sensor
mode. The functional live-view path later used a different observed descriptor
geometry and explicitly assumed Bayer packing. Bayer dimensions, firmware buffer
dimensions and LCD dimensions are different concepts.

A frame loaded on the host has transferred zero guest frames. A DMA write proves
delivery, not ISP consumption. A processed buffer proves an output, not native
selection for display. A screenshot proves a visible result, not correct CMOS
timing. Keep those counters and evidence separate.

Supplying RGB directly to a GUI surface would conceal the missing chain. The
functional path instead writes native submitted buffers after the modeled input
transaction. Its demosaic/tone/NV12 conversion is explicit and reproducible;
it must not be described as Nikon's actual image-processing algorithm.

## MENU restart is a capture shutdown problem

The former black return after MENU was not fixed by clearing a queue or drawing
another frame. The guest waited for RAW drain completion, while its next live-view
configuration remained queued. Completing four native drain requests separately
from new-frame processing lets the guest finish shutdown and start again.

TG parameter edges and RAW/ISP phases also need a coherent cadence. Mismatched
event rates can overflow finite guest queues even if individual callbacks look
correct. Reset stream latches at start, retain lifetime counters, respect masks
and W1C, and test repeated stop/restart in one process.

## Rendering symptoms often reveal format mistakes

A colored line at the image boundary can result from stored-row extent, stride
or chroma addressing. White text with missing outlines points to unimplemented
stroke state or incorrect alpha composition. A red no-card symbol becoming blue
points to RGBA byte order. Fix the command/pixel implementation and verify both
planes, padding and untouched guards.

The public tests use synthetic rectangles and levels, not extracted camera
icons. Detailed native pixel fixtures can be valuable privately, but their
usefulness is not a right to redistribute the original asset.

## Optimize only a measured bottleneck

Normal TCG blocks outperform one-instruction diagnostic blocks. CPSR lock paths
can spend significant time rebuilding cached execution flags; removing duplicate
work requires equivalence checks through mode transitions, not just a faster UI.

A RAW-byte cache is safe for a static source only when content identity includes
padding and output geometry/stride. Output destinations still receive every
transaction; reusing pixels must not imply reusing completion events. Hoisting
resampling divisions changes host work without changing selected cells.

The browser need not encode the same PNG on every poll. Hash the RGB buffer and
encode only changes. Keep screenshot scratch I/O on a Linux filesystem in WSL,
and read new log bytes incrementally. Measure host refresh time separately from
guest virtual time and frame-completion rates.

## Reuse across models

Reuse tools, state-machine design, tests and evidence conventions. Do not inherit
Z7's addresses, IRQs, memory map, protocol bodies or startup calls by product-family
name. Start a new sample with version/size/SHA-256, CPU ISA, endianness, container
layout and candidate load address. Establish a small boot checkpoint before GUI,
and GUI before sensor input.

Record facts, static inference, function emulation, system emulation and hardware
observation separately. A new configuration file or a shared EXPEED label does
not make a second model supported. Keep failed experiments and provenance.

## Recovery and publication are different exports

A private cold backup can include everything needed to resume a research guest.
A public source release cannot. This project has no full VMState serialization;
a cold restart is its recovery mechanism.

Public publication starts from a fresh Git history and a reviewed source
inventory. Never try to sanitize a private repository merely by deleting its
current firmware files: earlier commits and release assets can still contain them.
Keep local manifests, raw traces, screenshots and backups outside public artifacts.
