# Startup splash investigation — October 21, 2026

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
