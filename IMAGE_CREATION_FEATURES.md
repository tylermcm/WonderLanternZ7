# Image-creation feature candidates — October 25, 2026

The owner wants useful shooting and image-creation features beyond cosmetic
startup work. This is a research shortlist, not a claim that any new feature
has been ported, tested on a body or cleared for installation. No firmware was
built and no camera/card was accessed for this investigation.

## Comparison baseline

Nikon identifies the original [Z7 as EXPEED 6](https://imaging.nikon.com/imaging/lineup/mirrorless/z_7/index.html).
The [Z5 also uses EXPEED 6](https://imaging.nikon.com/imaging/lineup/mirrorless/z_5/),
but its sensor, controllers and firmware contracts still differ. The
[D780 uses EXPEED 6 and offers shutter times up to 900 seconds](https://www.nikonusa.com/press-room/d780-announcement).
The [Z7II/Z6II use two EXPEED 6 processors](https://www.nikonusa.com/press-room/z7ii-z6ii).
Their shared processor generation is useful evidence for investigation, not
proof that their throughput, autofocus or video features fit the original Z7.

Features on newer Zf/Z6III bodies below are design references. Their existence
does not establish EXPEED 6 compatibility or a dormant Z7 implementation.
Feasibility rankings are engineering estimates based on the identified work,
not measured probabilities of success or safety.

## Strongest candidates

| Candidate | Image-creation benefit | Basis and missing evidence | Relative prospect |
| --- | --- | --- | --- |
| Timed 60–900 second exposures | Long-exposure landscapes, ND-filter work and night photography without manually timing Bulb. | D780 and Z7II provide this officially. Existing lab M900 code overrides a property read, but the copied property identity still needs independent Z7 derivation; a real 900-second capture is unverified. | Strong research lead; existing experiment needs audit. |
| Highlight stripes in still-photo live view | Warn about bright skies, white clothing and other highlights before taking a photo. | Original Z7 already has movie highlight display. Trace its native producer, display eligibility, peaking interaction and photo/video buffer differences before attempting a still-mode extension. | Plausible reuse of an existing native capability; unproven. |
| Selectable 3×3 grid and framing masks | Rule-of-thirds composition, consistent portrait crops and planning panoramic crops. | Newer Nikon bodies offer grid selection. Our native graphics work supports investigating overlays. First inspect the original grid geometry; an existing line table could be simpler than a new renderer. LCD/EVF scaling, zoom and clean recorded output need verification. | Strong candidate for a first composition feature. |
| Named recipe library with explicit WB settings | Faster selection of repeatable JPEG looks without reconstructing several settings manually. | Original Z7 already supports custom Picture Controls C-1 through C-9 and card import/export. The extension would manage selection and optional WB settings, not create Flexible Color compatibility or an unlimited native slot bank. | Strong workflow candidate; setters, restoration and persistence need audit. |
| Custom shooting-display layouts | Keep the histogram, level, grid and essential exposure information visible together. | Newer bodies expose selectable information layouts. The lab has histogram/level work, but simultaneous native histogram visibility was not confirmed in the earlier synthetic no-lens profile. Native visibility and layout contracts remain open. | Plausible, with existing local starting points. |
| Dim/warm or red night interface | Reduce bright interface elements while working in darkness. | Nikon's newer Warm Display Colors offers display-only options. Start with UI colors/brightness; preserve captured images. Full live-view recoloring is a separate, harder display-pipeline task. | Plausible UI extension; not improved sensor sensitivity. |

Nikon's relevant references:

- [D780 extended shutter speeds](https://onlinemanual.nikonimglib.com/d780/en/14_menu_guide_05_d06.html)
  and [Z7II extended shutter speeds](https://onlinemanual.nikonimglib.com/z7II_z6II/en/09_menu_guide_05_d06.html).
- [Original Z7 movie highlight display](https://onlinemanual.nikonimglib.com/z7_z6/en-nsg/09_menu_guide_05_g06.html).
  This is a processed-display brightness threshold, not an established RAW
  clipping meter. Picture Control and preview settings must be considered.
- [Z6III grid selection](https://onlinemanual.nikonimglib.com/z6III/en/csmd_grid_type_252.html)
  and its [documented 3×3 default](https://onlinemanual.nikonimglib.com/z6III/en/csm_menu_items_and_initial_setting_212.html).
  Custom 4:5 or 2.39:1 masks would be our proposed display guides, not a claim
  that these are new Z7 recording formats or RAW crops.
- [Original Z7 custom Picture Control management](https://onlinemanual.nikonimglib.com/z7_z6/en/09_menu_guide_03_11.html).
  See [FILM_ROLL_FEASIBILITY.md](FILM_ROLL_FEASIBILITY.md) for compatible profile
  limits, setting ownership and why a reliable photo counter remains separate.
- [Zf custom shooting displays](https://onlinemanual.nikonimglib.com/zf/en/csmd_custom_monitor_shooting_display_234.html)
  and [Warm Display Colors](https://onlinemanual.nikonimglib.com/zf/en/csmd_warm_display_colors_228.html).

## Worth researching after those

**Waveform and false-color exposure tools.** Nikon documents a video waveform
on the [Zf](https://onlinemanual.nikonimglib.com/zf/en/csmg_brightness_information_display_271.html).
A proposed Z7 overlay could analyze a reduced-resolution live-view buffer;
it need not process every 45.7 MP still image. However, real preview-buffer
ownership, pixel format, stride, transfer function, refresh cost and GPU task
synchronization have not been established for this extension. A false-color
overlay is an additional lab idea, not an inferred hidden Nikon feature.
Neither should be called a RAW exposure meter without independent calibration.

**Area-restricted face/eye selection.** The
[Z7II/Z6II offer Wide-area AF people/animal modes](https://onlinemanual.nikonimglib.com/z7II_z6II/en/05_basic_settings_01.html).
Constraining the original Z7's existing detections to a selected region might
help portraits in crowded scenes. This is a hypothesis: the detector output,
region/selection interfaces, tracking behavior and processing budget need to be
identified. Do not copy the II model's AF firmware or promise its performance.

**More capable capture sequences.** Long-exposure brackets, exposure ramps or
near/far focus-sequence setup could extend existing camera workflows. They need
audited parameter setters, a genuine per-exposure transaction, cancellation,
card-failure handling and settings restoration. The current looping sound
notification is not a valid frame counter or sequence trigger. These are
harder than overlays and are not first targets.

## Existing features to avoid relabeling as new

The original Z7 already has
[Creative Picture Controls](https://onlinemanual.nikonimglib.com/z7_z6/en/07_the_i_button_02.html),
[focus-shift shooting and a peaking-stack preview](https://onlinemanual.nikonimglib.com/z7_z6/en/09_menu_guide_03_32.html),
plus [bracketing, multiple exposure, HDR and interval shooting](https://onlinemanual.nikonimglib.com/z7_z6/en/09_menu_guide_03.html).
Its C 3.80 firmware also includes earlier additions such as supported-lens focus
memory recall and dog/cat detection; see Nikon's
[firmware history](https://downloadcenter.nikonimglib.com/en/download/fw/558.html).
Any proposed enhancement must identify what it adds beyond those capabilities.

High-speed pre-release capture, internal high-bit-depth codecs, newer subject
detection models, pixel-shift capture and higher-resolution/frame-rate video
need separate sensor, bandwidth, accelerator or precision-control evidence.
IBIS existing in the body does not prove suitable subpixel positioning and
calibration. These are not ruled out categorically, but shared EXPEED branding
is insufficient to put them on the near-term implementation list.

## Suggested investigation order

1. **3×3 grid and optional framing guides:** inspect original grid generation,
   geometry and display routing, then test native overlay behavior in QEMU.
2. **Photo-mode highlight stripes:** independently trace the stock movie path
   and identify exactly why still mode excludes it.
3. **M900 audit:** derive the Z7 property and timer consumers independently,
   including timeout, EXIF, cancellation and error paths.
4. **Recipe selector:** start with compatible existing profiles and explicit
   setting ownership; keep a supported manual-import baseline.

Suggested order favors small, inspectable changes with useful photographic
results. The splash work provides native graphics experience, not proof of
continuous live-view overlay correctness. All physical firmware experiments
still require the open port audit and installation/recovery assessment.
