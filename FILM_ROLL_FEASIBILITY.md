# Film-roll mode feasibility — October 24, 2026

**Assessment:** a Z7 film-roll experience is a plausible extension. A first
version can build on Nikon's existing Picture Controls and add a recipe/roll
interface. Reliable automatic counting, power-cycle persistence and a hard
exposure limit remain research work. No new firmware was built or staged for
this assessment, and no camera/card was accessed.

## Verified starting point

Nikon's original Z7/Z6 manual already lists 20 Creative Picture Controls, with
adjustable effect strength and other image parameters. These are existing
camera capabilities, not features this lab has unlocked. See Nikon's
[Set Picture Control documentation](https://onlinemanual.nikonimglib.com/z7_z6/en/07_the_i_button_02.html#subhead001).

The camera supports named custom controls in C-1 through C-9 and copying them
to/from a card through Manage Picture Control. That provides a supported base
for a small library of selectable looks. See
[Manage Picture Control](https://onlinemanual.nikonimglib.com/z7_z6/en/09_menu_guide_03_11.html).

Nikon documents NCP, NP2 and NP3 as distinct custom Picture Control file types,
with compatibility depending on the camera. NP3 is not synonymous with Flexible
Color: the latter has an additional camera-support requirement. Start with
camera-compatible profiles exported by Nikon's tools and verify actual loading;
an extension or magic string does not establish support for every parameter.
Sources: [file formats and export](https://nikonimglib.com/nxstdo/onlinehelp/en/copy_custom_picture_controls_50.html),
[Flexible Color restrictions](https://nikonimglib.com/nxstdo/onlinehelp/en/the_picture_controls_flexible_color_23.html).

## Correction to the inherited feasibility report

The vendored `docs/porting-feasibility.md` says the original Z7 never officially
received Creative Picture Controls and treats their presence as a dormant
subsystem. That premise conflicts with Nikon's own original-model manual.
Its blanket association of NP3 with EXPEED 7/Flexible Color is also too broad.
An independent correction banner now marks those conclusions as superseded;
the inherited analysis remains preserved below it.

Local read-only checks used the exact stock Z7 C 3.80 MAIN fingerprint:

- The first reported mapping table at 0x10654E90 really contains numeric values
  0x0801 through 0x0814. That agrees with the documented existing controls; it
  does not demonstrate new rendering capability or a hidden-feature unlock.
- Executing original helper 0x102D8562 in Unicorn with synthetic RAM shows it
  stores the supplied R1 word into the supplied context. It does not read a
  camera model identifier from a file.
- At parser entry 0x101F0252, the comparison with 0x04390080 follows a separate
  call to 0x102D8566. The inherited report's claimed model-field derivation is
  not established by that sequence. Do not construct test files from that claim.

Three narrow evidence checks passed. The complete parser, file acceptance and
rendering were not executed. Sanitized results are in
`evidence/20261024-picture-control-baseline.json`; native listings stay private.

## Feature-by-feature assessment

| Feature | Current basis | Remaining work |
| --- | --- | --- |
| Selectable film-style looks | Existing built-in/custom Picture Controls | Design original looks and verify export/import/output on this Z7 |
| Recipe library with readable names | Nine native custom slots; custom-menu experience in this lab | Identify native selection/setter contracts and keep slot identity stable |
| Recipe also sets white balance or ISO | Those settings exist separately | Define which settings a recipe owns; do not assume a Picture Control file stores all of them |
| 12/24/36-frame roll display | Small host-side state machine is straightforward | Add firmware UI/state with audited allocation, cleanup and settings restoration |
| Automatic one-frame-per-photo count | Native still-file record notification is a tracing anchor | Establish a genuine exposure identity; reject preview, duplicate output, replay, failed requests and movies |
| Resume the same roll after power-off | No persistent custom-state implementation established | Audit file-write APIs and transaction/error handling; RAM-only state is insufficient |
| Stop shooting exactly at roll end | No verified capture-admission gate | Audit a per-exposure permit path, including burst overshoot, cancellation and recovery to normal shooting |
| Hide review until the roll is finished | No custom implementation established | Audit playback/review behavior separately and retain a clear exit |
| New grain/halation/RAW development engine | No Z7 implementation established | Separate image-processing project with memory, performance and output validation |

The firmware source already demonstrates a custom page and owner-reported
Preview playback, but its port audit remains open. Reusing its menu code still
requires interface/lifetime review. The existing sound callback is explicitly
unsuitable for counting photos: stock assisted live view emits it without a
shutter action. See `CAPTURE_EVENT_TRACE.md` and `STILL_FILE_TRACE.md`.

## Proposed first version

Use existing rendering first, with an original recipe name, selected native
Picture Control, explicitly listed optional white-balance settings, and a
chosen roll length. Preserve ordinary exposure controls unless the user opts
into fixing ISO for that roll. Keep the original RAW alongside a styled JPEG
when using RAW+JPEG; confirm the actual camera output during later testing.

An example interface, not an implemented camera screen:

```text
FILM ROLL
Look:       Soft Color
Roll size:  24
Frames:     07 / 24
Status:     Ready
New roll    Exit film mode
```

Initially, an end-of-roll notice is a better acceptance target than forcing a
shutter lock. Even a reliable file-completion counter happens after saving and
cannot guarantee an exact burst cutoff. A hard limit needs independent capture
admission evidence before exposure, plus a dependable exit back to normal use.

## Order of investigation and acceptance

1. Establish a stock baseline using a Nikon-exported compatible custom control.
   Verify name, selection and look on the actual body before writing a new
   profile format or modifying a rendering path. No firmware update is needed
   to evaluate existing Picture Controls.
2. Prototype the recipe chooser and roll state outside the firmware, then use
   synthetic events to check state transitions. A manual frame-advance control
   can demonstrate the workflow while automatic photo detection is unresolved.
3. Continue native exposure/record tracing. Require one count for one exposure,
   including RAW+JPEG, and correct behavior for bursts, cancellation, replay,
   cardless shooting, failed writes, file-number reuse and card changes. File
   IDs alone are not yet a verified exposure key.
4. Audit persistent state and restoration. Detect incomplete/invalid saves and
   show an uncertain state rather than silently guessing the remaining frames.
5. Only then integrate an automatic counter and consider optional review/shutter
   restrictions. Any camera diagnostic build still needs the existing Z7 port
   audit and a concrete installation/recovery assessment.

This is a feasibility result and implementation sequence, not a ready camera
feature. The existing firmware flash hold remains active. No donor-camera code,
Ritual implementation, film assets or new image-processing engine was imported.
