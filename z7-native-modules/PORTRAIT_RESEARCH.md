# Original Z7 portrait port

Independent work against original Z7 C3.80, following the MIT-licensed
[pinned JKWTCN implementation](https://github.com/JKWTCN/z7ii-extensions/blob/50a22b24c50619cffa646dac386e8334659f475a/plugins/portrait_menu.c).
This is an incomplete port. No orientation drawing hook is installed by the
current display module. The accepted LCD/EVF highlight pair is unchanged.

## Native orientation and bounded geometry

`plugins/orientation_sample.h` calls the original read-only Thumb API
`101B331B`. It accepts native values0..3 and leaves the caller's output unchanged
for unknown4 or any larger value. It never changes the native override.

Observed native behavior, executing stock instructions:

| Gate word at A1809074 | Selector at A1D49784 | Raw return |
| --- | --- | --- |
| Exactly1 | Any | Sensor byte at A1D495DC |
| Other | 1 | 0, landscape |
| Other | 2 | 3, inverted landscape |
| Other | 3 | 1, portrait A |
| Other | 4 | 2, portrait B |
| Other | 0 or greater than4 | 4, unavailable |

The native wrapper at10532FD6 maps only unknown4 to landscape0. It passes other
values through, including invalid sensor bytes. Its connection to the graphics
task has not been established. It is not used by the bounded sampler.

The original override setter101B4224 stores its full selector, compares raw
orientation before/after and conditionally dispatches notification42051201 with
the new value through the callback at A1809088. A missing callback is allowed.
These are observed branches with supplied gate/sensor inputs, not physical IMU
validation or an explanation of the gate's real startup lifecycle.

`plugins/portrait_geometry.h` provides exclusive-edge box transforms between
LCD720x480 and portrait480x720. Portrait1 and2 select opposite quarter turns;
landscape0 and inverted3 are left to caller policy. Coordinates and dimensions
are bounded before subtraction. Failure preserves the output, and exact
input/output aliasing is supported. This is abstract geometry, not a native
payload layout or complete HUD reflow.

Private audit `20261120-orientation-02/result.json` passes13405 checks:9216 native
gate/selector/sensor combinations,504 original override/notification cases,
2604 valid compiled geometry cases, invalid/extreme coordinates, null pointers,
nonmutation and in-place round trips. The flat compiled probe is reproducible,
384 bytes including its header,320 image,0 BSS and0 relocations. Its manual
fixture loading does not exercise the module loader admission path.
Run02 refreshes the current header fingerprint after changing reusable geometry
helpers to `static inline`. The probe remains384 bytes, with a changed image
layout; run01 remains historical evidence for the previous source checkpoint.

## Native rectangle queue and dispatcher

The original rectangle painter10433912 reaches104FFED0 for clearing and
104FFD54 for shape rendering. The clear path reaches producer1042F5F6.

| Binding | Original Z7 address |
| --- | --- |
| Graphics task structure | A1D75D34 |
| Queue member | Task+20 |
| Registered dispatch slot | Task+2C, A1D75D60 |
| Dispatcher | 10372391, Thumb |
| Producer enqueue wrapper | 103726B9, Thumb |
| Queue-mode halfword | A180AD70 |
| Rectangle producer | 1042F5F7, Thumb |
| Rectangle backend adapter | 1042F5A9, Thumb |
| Producer completion callback | 1042EADF, Thumb |
| Completion event storage | A1D75E3C |

The original registration routine101F2414 writes the callback to task+2C,
initializes task+20 and starts the task. This slot differs from the pinned
Z7II task+24 layout. Do not copy its address or structure offsets.

For a nonzero signed queue-mode halfword,1042F5F6 builds command42010017 with
six payload words: x,y,w,h and two widened flag bytes. Its seven-word message
contains a queue self-link at+8, completion at+C, command at+10, payload pointer
at+14 and result at+18. The real enqueue wrapper writes the self-link. The
original dispatcher converts the payload back to a28-byte shape, zeroes unused
fields, calls1042F5A8 synchronously, writes result0 and invokes the original
completion with42010062/0. That callback signals the producer's event. With
queue-mode0, the producer calls the backend directly with the input shape.

Private `20261120-graphics-queue-05.json` passes27 checks covering original
registration, direct and queued paths, original enqueue wrapper, all message
fields used here, three boxes, modes0/1/2/FFFF, input preservation and completion.
Two Unicorn CPUs use an explicitly serialized schedule; queue/lock/event kernel
services and the renderer are supplied. This proves marshalling and dispatch,
not real task concurrency, installed-hook lifetime or pixels. Early fixture runs
01/02 expected the wrong completion code;03 failed a Python bytearray transfer;
04 passed26 before registration coverage was added in05. Failed runs are not
accepted evidence.

## Caller-admitted synchronous portrait drawing

`plugins/portrait_draw.h` now connects a caller-selected portrait box to original
Z7 message dispatch. It supports native rectangle commands13/16/17 and image
commands19/1A. This is callable software, not an installed graphics hook: the
caller must own the graphics task and admit the intended LCD output/page.

The Z7 payloads differ from the pinned Z7II layouts:

| Command | Source words | Original Z7 backend |
| --- | --- | --- |
| 13 | 8 | 1042F066,28-byte normalized shape |
| 16 | 7 | 1042F426,seven arguments |
| 17 | 6 | 1042F5A8,28-byte normalized shape |
| 19 | 18 | 104303E6,68-byte normalized image |
| 1A | 24 | 1042F894,88-byte normalized image |

Image angles are the low half of source word15. Source words16/17 become
two flag bytes, while1A skips source word18 and copies words19..23 into its
extra backend fields. Using the pinned angle word16 would alter a flag instead.
The adapter preserves other source fields, converts destination corners and
adds the intended quarter turn to angles0/90/180/270/360. Mode0/1 input becomes
explicit-destination mode0. Rectangles convert top-origin portrait geometry into
the native bottom-origin payload. Original source bytes are never changed.

The local message defers completion until original dispatch returns, then copies
its result and invokes the original producer completion exactly once. Admission
checks reject foreign callbacks, unknown commands, malformed RAM spans, invalid
angles/modes, unsupported orientations and invalid boxes without dispatch or
acknowledgement. Fixed-point image1C is deliberately pending its original-Z7
format conversion; text and page policy are also unfinished.

Private `20261120-portrait-draw-02/result.json` passes155 checks:138 draw cases
covering all five commands, both portrait directions, three boxes, both image
modes and five angles;17 rejected-input cases preserve message/payload state.
The original dispatcher, image normalization adapters and completion execute.
Only backend renderers and the kernel event boundary are supplied. Comparison
excludes backend padding bytes that native adapters leave undefined. Render,
deferred completion, original acknowledgement and event order are checked.
The probe builds reproducibly:640 file/576 image/0 BSS/0 relocations. Flat fixture
loading does not prove module-loader admission or actual renderer lifetime.
Draw01 failed compilation because the original shared header emitted an unused
direction helper under `-Werror`; reusable inline helpers corrected02.

## Remaining integration

Bind actual LCD output/target admission, fixed-point image and text payloads,
draw-task lifetime and callback ownership before installing a rotation hook.
Preserve producer completion and payload lifetime: never redirect asynchronous
native work to a temporary stack copy. Then port portrait reflow, navigation and
touch mapping, settings/persistence and cleanup across mode transitions. Physical
MENU, playback, magnified view and other upstream exclusions need their intended
policies preserved. Native startup, Info mirror, real histogram source and exact
installation/recovery assessment remain separate unfinished requirements.

The previously missing pinned `portrait_probe.c` was fetched read-only into
private research:7717 bytes, SHA256
`119c24c6846abb6df80969a4c56ee33ffcca9bd878555c0e55ac1db8723411ac`.
Its SPDX MIT notice is preserved. Firmware, probes and emulator output stay
private. No camera/card access, staging, flashing or push occurred.
