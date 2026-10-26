# Startup splash investigation — October 21, 2026

## Independent firmware lifecycle — October 24, 2026

The owner authorized building a firmware experiment and running it in QEMU.
`tools/build_splash_firmware.py` now generates a private, independent **Z7 C
3.80 MAIN and checksummed EG** from the exact original container. It builds
twice, checks reproducibility and independently rebuilds the complete candidate
before running it. This experiment is excluded from the normal installation
presets; no outer Nikon update package or camera-card staging is produced.

The new feature is `z7-firmware-extensions/src/z30_extensions/features/splash_z7.py`.
All three patch sites require their original, complete instruction windows:

| Site | Purpose |
| --- | --- |
| 0x101E3DA0 | Initialize independent state and reserve 64 bytes from the native monotonic workspace. |
| 0x10269842 | Retain both original resource calls, then atomically arm the cold-start latch. |
| 0x1042F152 | Consume the latch before the first native full-screen clear. |

State at 0xA9700000 is explicitly reserved by starting the original workspace
cursor at 0xA9700040; it is not an assumed unused RAM hole. Original allocator
initialization, locking and subsequent allocations remain native. The original
UI resource guard is still cleared by its original displaced instruction.
The renderer accepts only caller 0x104FFB19 and a black clear descriptor
`[0, 0, 720, 480, 255]`. It atomically changes armed to busy before drawing.
Other callers, dimensions, colors and later menu activity retain normal drawing.

The splash and black cleanup PNGs are immutable appended ROM data. An 88-byte
helper frame contains a small zeroed descriptor/result area, rather than placing
encoded image data on the task stack. Stock Z7 code at 0x10431738 performs
PNG decoding and GPU submission. Native OS delay 0x1017081E receives argument
2000. The firmware then draws black backing, marks the latch complete and
replays the original clear-function prologue. The OS delay's physical units and
end-to-end camera timing are not calibrated; QEMU wall time is reported separately.

Continuous QMP observation exposed a gap in the earlier sampled host prototype:
the first firmware candidate, hooked at PNG builder 0x10430256, allowed a gray
64-pixel sidebar to appear briefly before the splash. That candidate is retained
privately and rejected for first-screen order. Original graphics-queue traces
identify the earlier full-screen clear used by the revised hook. Initial test
comparisons also caught incomplete asynchronous menu text redraws; the observer
now waits for scene changes to settle before exact navigation comparisons.

`tools/audit_splash_firmware.py` executes the actual patched instructions with
controlled OS/GPU helper boundaries. Its 40 checks cover reservation guards,
stack/register forwarding, original resource calls, atomic one-shot behavior,
recursive rendering, unmatched clear rejection, synthetic reinitialization,
timer-error cleanup and cold-state reset. Unit evidence is
`evidence/20261024-splash-firmware-unit-v2.json`. These are instruction tests,
not native display or physical concurrency evidence.

`tools/probe_splash_firmware.py` loads the actual MAIN with the existing assisted
boot/power/system/MENU fixtures. Its observer adds QMP screenshots only: no
host splash trigger, rendering breakpoint, asset upload, splash-state write,
native drawing call or lifecycle timer injection. The firmware owns presentation,
hold and cleanup. The fixture's MENU action still schedules the underlying
scene; physical immediate power-on and live-view startup are not demonstrated.

Two fresh cold guests now pass **27 checks each** with the actual revised
firmware: exact first nonblack splash pixels, completed native handoff, reserved
state/guards, native menu focus changes and exact established-scene restoration,
MENU exit/re-entry without rearming, and a single observed splash throughout.
Public evidence: `evidence/20261024-splash-firmware-qemu.json`. Private captures
and complete runtime state: `.private/research/splash/20261024-firmware-03/`.
The retained build is `.private/builds/20261024-splash-emulator-02/`, MAIN
SHA-256 `dc6ec38c9b427374afd80be53d31d14edb4914e89f06abc73099a9e12f021f24`.

Reproduce with fresh private output directories:

```powershell
.\.venv\Scripts\python.exe tools/build_splash_firmware.py `
  --output .private/builds/splash-NEW
.\.venv\Scripts\python.exe tools/audit_splash_firmware.py `
  --candidate .private/builds/splash-NEW/splash.emulator.main.bin `
  --report .private/builds/splash-NEW/splash.emulator.json `
  --stock .private/stock/Z_7_0380.bin `
  --output .private/builds/splash-NEW/unit.json
.\.venv\Scripts\python.exe tools/probe_splash_firmware.py `
  --candidate .private/builds/splash-NEW/splash.emulator.main.bin `
  --report .private/builds/splash-NEW/splash.emulator.json `
  --output .private/research/splash/firmware-NEW --boots 2
```

This narrow build/QEMU authorization does not clear installation. Physical
LCD/EVF and wake semantics, low-memory/native decoder failure behavior, update
acceptance and recovery remain unverified. No camera/card access or flash occurred.

## First-screen ordering corrected — October 24, 2026

Historical host prototype: its sampled ordering claim is superseded by the
continuous firmware observations and earlier clear-function hook above.

The owner observed that the original replay entered the playback menu before
showing the splash. That satisfied the earlier overlay/lifecycle checks but
failed the actual startup requirement. The corrected probe now shows the
splash as the first nonblack scene, then continues the normal native draw.

`StartupCamera` intercepts the first native graphics call at 0x10430256 during
assisted boot. The observed caller is the stock PNG path (return address
0x104316FB); the current QEMU surface is still entirely black. The fixture
executes the splash PNG wrapper in that rendering task, consumes its own host
one-shot before drawing, and uses short original OS delays while holding the
normal first draw. Other guest tasks execute during these delays. After about
two host seconds, a black RGB PNG restores the backing surface through the
same native decoder/GPU path, then the original graphics call resumes. Without
that cleanup, parts of the splash could remain behind the initial menu.

Two independent cold boots pass **41 checks each**. Checks cover the black
pre-splash surface, rendering-boundary interception, exact splash pixels,
caller context/scratch and heap/descriptor guards for both draw operations,
the held splash, exact black backing restoration, subsequent menu rendering,
actual focus navigation, and no repeat during menu exit/re-entry/navigation.
The exact menu comparison uses the same established focus state: the native
help-icon backing changes after its first focus cycle, so comparing different
states would reject a valid redraw. Initial and subsequent frames are retained.

Sanitized evidence: `evidence/20261024-splash-first-frame.json`. Private runs
and rejected variants remain under `.private/research/splash/`. The reproduction
command below still applies, but now invokes the corrected first-render flow.

The native MENU diagnostic input still schedules the underlying first scene;
it does not become visible before the splash. An attempted no-MENU idle-task
draw showed a splash but failed normal UI handoff. It is not the retained
implementation. This remains host-assisted emulator work: physical LCD power
timing, a firmware cold-reset latch, native lifecycle timers, live-view startup,
wake and EVF behavior are unverified. The generic graphics function must never
be hooked unconditionally; the host intercept is restricted to this boot's
first rendering boundary. No firmware was built, staged or flashed.

## Automatic startup experiment — October 24, 2026

Historical result: the experiment below waited for an existing menu scene.
It demonstrated an automatic overlay, not the corrected first-screen ordering.

`tools/probe_splash_startup.py` now automatically shows the original test card
in two independent assisted stock QEMU boots. Each run passes **30 checks**:
the native initialization sequence arms a host one-shot, no postboot navigation
precedes the splash, the full LCD matches its source, and the splash remains
visible while the guest runs for about two host seconds. Automated native focus
navigation restores the exact startup scene. Subsequent MENU exit/re-entry and
left/right/down/up navigation do not show the splash again. The second cold
guest initializes and presents it once again.

The startup investigation distinguishes an outer initializer from its guarded
resource setup. Original code at 0x102697F4 reads 0xA1822D68. The original
initialized RAM image contains 1 at that location. If nonzero, the native path
initializes UI resources through 0x103F9C0A, then clears the flag at
0x1026984A. The cold traces observe the wrapper, resource initializer and clear
site in that order, with flag 1. Later checkpoints read 0. Crucially, MENU
re-entry reaches the outer initializer again while resource initialization
does not repeat. An unconditional hook on the outer function would therefore
be the wrong startup trigger.

The diagnostic arms its host-side pending state at 0x1026984A, after resource
initialization returns. It then waits for a nonblank stable LCD, consumes its
own one-shot before drawing, and uses the same heap-backed native PNG helper as
the presentation probe. No guest instruction or framebuffer pixels are patched,
and the native flag is only read. Native trace observations inside diagnostic
calls report an unknown flag value as null when it was not captured; later
checkpoint reads verify that it remains zero. No missing value is treated as a
zero observation.

Sanitized evidence: `evidence/20261024-splash-startup.json`. Reproduce with a
new private directory:

```powershell
.\.venv\Scripts\python.exe tools/probe_splash_startup.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --output .private/research/splash/startup-NEW
```

This is an automatic **host-assisted emulator lifecycle**, not an installed
firmware startup feature. The existing assisted menu boot supplies synthetic
power/system state and a native MENU action. Graphics readiness is detected from
LCD frames; the hold uses host monotonic time and dismissal uses synthetic
native focus keys. It does not establish a native graphics-ready event, timer
callback, early key dismissal, live-view startup, EVF behavior or physical wake
suppression. The initialized flag could have reinitialization semantics outside
these tested paths; it must not be assumed to mean once per physical power-on.

For production, the guarded block is an arming candidate to investigate, not a
cleared inline drawing site. Use an independent verified cold-reset latch,
defer work to a confirmed graphics-ready/render-task event, and establish
bounded cancellation/dismissal before connecting a patch. Do not reuse the
native initialization flag as custom state. No firmware image has been built,
staged or flashed; the existing port audit and installation hold remain active.

## Native QEMU presentation verified — October 24, 2026

An original full-screen test splash now appears on the assisted stock Z7
emulator's LCD. `tools/probe_splash_display.py` calls the original PNG drawing
wrapper at 0x10431738 from the existing application-task checkpoint. The wrapper
queries image dimensions, decodes the supplied PNG through stock libpng/zlib,
submits native graphics work and waits before releasing decoded storage.
Trace points observe the header/context/format/row routines (0x104310B4,
0x104313D0, 0x10431278, 0x104311F4), drawing at 0x10430256 and the wait at
0x1042EB0E. The host supplies encoded PNG data and diagnostic calls; it never
writes framebuffer pixels or adds a host screen overlay.

The fresh run passes **14 checks**. Its entire 720x480 RGB LCD output matches
the generated source pixels exactly. The 13,121-byte PNG and both 16-byte heap
guards remain unchanged, the descriptor guard survives, and the caller's
register packet and scratch bytes are restored. Normal tab-focus navigation
replaces the splash with an exact copy of a native menu scene sampled before
drawing; subsequent row-focus navigation also changes the display, and the
guest resumes running. The fixture closes only its own QEMU instance.

The encoded PNG is held in memory returned by original allocator 0x1016FE38
and released through 0x1016FE4A after rendering. Only an 80-byte descriptor and
result/guard area occupy caller scratch. Early exploratory runs staged the
whole PNG on the task stack and stalled or left later navigation unresponsive.
That approach is rejected. An attempted graphics lock from this other task
also stalled and is not retained. Neither experiment establishes a safe
production callback context. The successful path is a bounded diagnostic call.

Sanitized evidence: `evidence/20261024-splash-native-display.json`. Private
frames/traces, including unsuccessful runs, remain under `.private/research/splash/`.
Reproduce with a new output directory (the probe requires the private root):

```powershell
.\.venv\Scripts\python.exe tools/probe_splash_display.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --output .private/research/splash/display-NEW
```

This proves native image presentation and a menu redraw in an assisted guest.
It does not implement a once-per-power-on splash, timeout/key dismissal handler,
wake suppression, LCD/EVF switching or physical camera timing. The next task is
to identify a safe startup/render-task transition and connect bounded lifecycle
state without guessing a hook. No firmware image was built, staged or flashed;
the port audit and installation hold remain active.

## Native image path verified — October 24, 2026

The owner prioritized splash loading before film-roll features. New offline
work identified and executed a stock Z7 image-resource and PNG path before the
QEMU presentation above. These offline checks do not identify a power-on hook.

The original UI initializer at 0x103F9C0A registers resource table 0x10D0B7C0
through 0x104BD2EA. Records are 20 bytes apart; the descriptor getter at
0x104BD2F6 copies format bytes at offsets 0/1, encoded length at +4 and image
pointer at +16. Offsets +8/+12 are not established as freely reusable state.
Original entry zero points to a 36x72 PNG; large existing images use this same
table shape. A source-level branch encoding scan identifies callers of the
getter, and selected callers were checked in context rather than treated as
automatic hook candidates.

An original higher-level size query at 0x104E98A8 reaches the stock libpng
header path at 0x104310B4. The stock context constructor at 0x104313D0,
format/read setup at 0x10431278 and row decoder at 0x104311F4 provide a concrete
in-memory image path. The embedded library identifies itself as libpng 1.6.2.

`tools/audit_splash_image.py` now executes these original routines in Unicorn
against the pinned stock MAIN. **43 evidence checks pass**:

- Original stock entry and original synthetic 32x24 RGB, 32x24 RGBA and
  320x120 RGB PNGs report their expected dimensions through the native wrapper.
- Upper-bound image-index normalization and an unsupported wrapper mode take
  the observed native paths under the supplied one-entry table bound.
- Failing each of the three header allocations returns failure with no live
  fixture allocations. This does not clear all pixel-decoder failure paths.
- The three synthetic images decode to the exact expected RGBA pixels. RGB
  receives alpha 255; RGBA retains the supplied alpha 160. All 16-byte output
  guards remain intact, temporary allocations are freed and callee-saved
  registers/stack are preserved at each native call boundary.

Only allocation/free are controlled helper boundaries; the resource getter,
wrappers, libpng/zlib decoding and memory helpers execute original stock code.
The resource table/bound are supplied unit inputs, not a claim of safe spare
native image IDs. No GPU, display controller, live guest or camera is involved.
The initial one-million-instruction fixture bound was too small for the 320x120
pixel run; a bounded ten-million-instruction run completed. That is an emulator
fixture limit, not a measured camera delay or a native startup failure.

The 320x120 test PNG is 636 bytes compressed and produces 153,600 RGBA bytes.
This illustrates the difference between appended storage and runtime memory;
it does not define the dimensions or compression ratio of final artwork.
Use 8-bit RGB or RGBA, non-interlaced PNG as the initial tested asset profile.
Other depths, palette images, malformed inputs, decode-error cleanup and alpha
blending still need separate checks. Do not accept arbitrary images or negative
IDs based on these results.

Sanitized results: `evidence/20261024-splash-native-pixels.json`. The earlier
metadata-only result is preserved in `evidence/20261024-splash-native-image.json`.
Both contain numeric summaries, not Nikon image data. Reproduce with a new path:

```powershell
.\.venv\Scripts\python.exe tools/audit_splash_image.py `
  --stock .private/builds/20261021-silent-property-01/stock-main.bin `
  --output .private/research/splash/native-image-NEW.json
```

The native guest presentation milestone is now recorded above. A verified
startup transition, once-per-boot state and bounded dismissal still need to be
connected. Wake, menu entry and LCD/EVF changes
must be negative cases. No splash firmware has been built, staged or cleared;
the Z7 port audit and installation hold remain active.

## Earlier feasibility baseline — October 21

A custom startup image looks feasible as an independent firmware UI feature.
This investigation establishes useful image/resource support, not a completed
splash implementation or a camera-tested startup hook. No splash firmware was
built, staged or flashed; the card's capture-diagnostic candidate is unchanged.

## Findings from the private stock C 3.80 MAIN

- The input matches the pinned stock MAIN SHA-256. Raw firmware, extracted
  images and disassembly remain under `.private/research/splash/`.
- The payload contains PNG resources and libpng strings. Of the first 200 PNG
  signature hits, 198 pass Pillow's image verification. A separate scan verifies
  complete chunk CRCs for 16 resources at least 480 pixels wide and 240 high.
- The first three large images were inspected privately. They are a test chart
  and UI backgrounds, not identified startup logos. This is not an exhaustive
  visual classification of every resource; absence of a splash-named string does
  not prove there is no existing startup image.
- The emulator renders native firmware graphics and exposes distinct startup
  checkpoints for image-memory initialization, power/system state and application
  readiness. Those checkpoints use assisted startup; they do not establish the
  timing of a real camera's power-on sequence.
- At this splash investigation, the capture-diagnostic EG is 33,065,098 bytes. Under the existing
  33,554,432-byte patcher limit, 489,334 bytes (about 478 KiB) remain for appended
  code/data. This is the patcher's conservative budget, not a new hardware-capacity
  measurement. A raw 1024x682 RGBA frame is 2,793,472 bytes and would exceed it;
  a compact logo or suitably compressed image is a better candidate. Final image
  dimensions, format support and runtime decode allocation remain to be tested.

## Proposed implementation

Embed an original compact image in the appended MAIN payload, and use a native
UI drawing path after the graphics service is ready. Show it once per true
power-on with a brief bounded lifetime, then release it to the normal camera
screen. Drawing should not block the startup task or capture readiness. Normal
standby/wake, monitor/viewfinder switching and opening menus must not retrigger it.

First map the native image descriptor/decoder interface and its allocation and
cleanup rules. Then identify a startup notification or UI state transition that
is reached exactly once at power-on, with a separate lifetime/dismissal mechanism.
The `PowerOnBoot` command name found in the stock strings is only a research lead;
its name alone does not establish a suitable callback or hook address.

An embedded image would be installed as part of a new reviewed EG build. Merely
placing SPLASH.PNG on the card does not add this feature. Optional card-loaded
artwork would require additional file-I/O and fallback behavior and is a separate
implementation choice.

## Required proof before a camera candidate

Execute the native image path with an original test asset, verify descriptor
bounds and allocation cleanup, then inspect the emulator's actual guest-rendered
frames and return to live view. Check one-time display, dismissal and standby
transitions. The emulator's assisted boot limits must remain explicit. Real LCD/
viewfinder behavior, startup latency and capture readiness still need hardware
tests. Any installation uses the assessment in
[FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md); no separate bootloader write is proposed.

Current conclusion: a promising moderate reverse-engineering task. Native PNG
resources reduce uncertainty about artwork storage, while the exact callable
display interface, startup hook and hardware timing remain unresolved.
