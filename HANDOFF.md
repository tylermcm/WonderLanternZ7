# Laptop handoff — October 20, 2026

## Source push preparation — October 27, 2026

The owner requested pushing the code. Scope includes automatic spiral lifecycle,
gray native LCD/EVF routing, exact-candidate review and compatibility tools,
source-only evidence, clean-display research and the unresolved level-lag report.
The pending QEMU smoke helper change permits EOF/reset after a successful quit
request only, while retaining mandatory capabilities/status replies, zero exit
and bounded termination; its 12 synthetic process/TCP regressions are included.
No renderer performance fix or new firmware release is claimed.

Fresh checks: all 23 root tests and all 23 QEMU component Python tests pass.
The first restricted component run hit local file/socket access failures; the
properly permitted repeat passes. The QEMU publication inventory passes with
46 source-only files. The actual native QEMU executable also passes the updated
firmware-free QMP smoke check. No C renderer/ISP source changed, so those contract tests
were not redundantly rerun. Previous exact-candidate instruction/emulator results
remain scoped as documented above. Private firmware, dumps, binaries, media,
camera captures, keys and ignored graphs are excluded from this source push.

## Gray/EVF trial works; Golden ratio level lag — October 27, 2026

Owner reports the installed gray/EVF trial works, but electronic level motion
lags conspicuously in EVF and barely noticeably on the monitor, only on Golden
ratio. They recall no lag before the spiral. Exact report is recorded in
`evidence/20261027-grid-spiral-display-owner-hardware.json`. Associated EG remains
`c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`.
This is owner-reported post-update function/performance, not firmware readback
or independently timed observation. Do not keep claiming EVF is wholly untested;
the owner now reports the trial works, with this regression.

Read the new performance section of `GRID_SPIRAL_RESEARCH.md`. Each eligible UI
paint completion currently calls uncached PNG drawing under the shared native
graphics mutex. Native wrapper forces resource ID -1 and allocates/decodes/
synchronizes/frees a full image each call. EVF decodes 4,915,200 RGBA bytes for
7,589 curve pixels; LCD 1,382,400 bytes for 4,195 curve pixels. This is the leading
cause, not a measured hardware latency diagnosis. Candidate native path/paint
primitive `0x1042F066` and boundaries `0x10450852/0x10450A3E/0x104508A6` provide a
starting point for an allocation/decode-light curve renderer, but full argument,
state restoration and failure contracts remain unverified. No replacement
renderer, new firmware or lag fix was built in this triage. Preserve all current
builds. No new card access or staging occurred. No physical rollback or emergency
recovery is verified. Source manifest refreshed; firmware code unchanged.

## Gray LCD/EVF spiral staged for owner trial — October 27, 2026

Owner explicitly authorized staging/flash: "card is mounted lets flash it".
Read `GRID_SPIRAL_DISPLAY_FLASH_ASSESSMENT.md`. Fresh independent build at
`.private/builds/20261027-spiral-display-flash-01/` exactly matches tested candidate
02: full EG 33,074,646 bytes, SHA-256
`c3cbb8fd4aaa932fc74cfd662cbfaac3f5471ea6ab81edb6148766d5a93449b6`;
MAIN `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
New explicit `grid-spiral-display` review identity reconstructs all EG/MAIN/report
bytes separately from legacy yellow and rejects mixed/modified/legacy/explicit
artifacts. Twelve native updater header/name checks, 18 fresh previous-loader
compatibility checks and 23 root tests pass. Exact prior 132 instruction, 18 LCD
lifecycle and nine native EVF-bitmap results plus their frame/bitmap hashes verify;
QEMU was not redundantly rerun for byte-identical artifacts. Ignored code graph
refreshed. Review bundle retains stock and three prior rollback inputs separately.

Sony QD-G240F was freshly identified on E: by serial, size, volume and partition.
Its yellow EG exactly matched and is backed up at
`.private/card-backups/20261027-spiral-display-4d73d3a5/EG161080.BIN`.
New full EG is staged and fully hash-verified as the only root BIN. Other root
file sizes/hashes remain unchanged; photo directories were not edited. No
formatting, automatic ejection or camera operation occurred. Receipt is in that
backup folder; sanitized evidence is `evidence/20261027-grid-spiral-display-flash-review.json`.

Owner instructions: charged power, select 3x3 before update, safely eject, use
normal firmware updater (version stays 3.80), do not interrupt programming, follow
completion/restart instructions. Confirm normal rear-monitor use first, then
Golden ratio gray curve and MENU/3x3 removal, then EVF/monitor switching. No
physical EVF success, camera update completion, rollback or emergency recovery
is claimed. The camera has not been operated by the agent.

## Gray spiral and native EVF bitmap correction — October 27, 2026

Latest owner feedback: yellow spiral is visible only on the monitor; straight
custom grids work in EVF. The owner requests normal-grid gray and EVF support.
The installed legacy helper explicitly excluded EVF. Read the new top section
of `GRID_SPIRAL_RESEARCH.md` and `CLEAN_DISPLAY_RESEARCH.md`.

New private build `.private/builds/20261027-spiral-display-02/` uses original Z7
component-1 descriptors for LCD 720x480 and EVF 1280x960, exact registered
surface/shape checks, separate immutable gray assets and active IDs 1/4.
MAIN SHA-256 `7049b2120a9f88e3859a5d8ec335bb4858e6642ba9a278e5cd95474edf597543`.
Independent rebuild/CRC, 132 supplied-boundary instruction checks, 18 assisted
LCD lifecycle checks and 22 root tests pass; nine frame hashes verify. The gray
detector's first run falsely counted native grid/gradient pixels; the failed
run is preserved and a regression plus narrower upper-arc detector resolves it.
The complete gray spiral and Off frames were visually inspected.

Native EVF bitmap/decoder test is separate from eye-sensor/scanout validation.
Attempt 01 sampled two-byte instead of four-byte pixels; attempts 02/03 used
top-down coordinates against a bottom-up RGBA bitmap. These failed results
remain preserved. Attempt-03 full raw capture exactly matches all 7,589 source
curve pixels after vertical reflection, including 6,621 beyond LCD-sized bounds.
Corrected repeat 04 passes all nine checks, including native registration,
full-size gray pixels and previous target restoration. Its result is in
`.private/research/grid/20261027-spiral-native-evf-04/`. No physical EVF success
is claimed. Sanitized evidence: `evidence/20261027-grid-spiral-display.json`.
Default legacy build exactly reproduces installed yellow MAIN hash `06b89e2a...`.
The new identity is not admitted by the existing yellow flash assessment/review.
No new candidate was copied to the card; it is in the camera after the owner's
earlier trial. Fresh card identification and a new exact-candidate assessment
are required before a later staging request.

Clean-display emulator RAM masking hides most shooting widgets but leaves two
card-count brackets even after MENU clear/return. Original background/secondary
bitmap fills did not remove them. All original masks were restored, normal
simplified readouts returned, and that isolated guest was closed. No clean UI
firmware patch is included. Private research outputs remain under
`.private/research/display/20261027-clean-mask-03/`.

## Owner confirms spiral grid switching — October 27, 2026

After the reported update initiation below, the owner reports: "yep it appears
only when using golden ratio, and will disappear when swapping to another
gridtype". This is the first physical-camera report for the automatic spiral
image staged with EG SHA-256
`52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`.
It supports post-update display operation and expected layout selection/removal
on one original Z7. It is not independent observation or firmware readback.
The owner also answered "Yes, clears and returns" for opening MENU and returning
to Golden ratio. Exact completion text, EVF/crop/DISP/wake, capture/performance
and recovery remain unverified. The core selection and MENU lifecycle now have
both scoped emulator evidence and one owner's physical-camera report.
Evidence: `evidence/20261027-grid-spiral-owner-hardware.json`.

## Spiral trial staged; owner reports programming — October 27, 2026

The owner accepts the curve in front of status icons and explicitly requested a
camera trial. The owner confirmed charged power and a backed-up card connected
through its reader. Read `GRID_SPIRAL_FLASH_ASSESSMENT.md`. Clean-display research
is a separate task and is not in this BIN.

Fresh `.private/builds/20261027-spiral-flash-01/` exactly reproduces the tested
automatic-paint image: full EG 33,062,334 bytes, SHA-256
`52c593aff9895e31b4cfaf15ceb0335bdf4f26671d346dcb499080ea11c0f316`;
MAIN SHA-256 `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`.
The dedicated `grid-spiral` review rebuilds/completely compares EG, MAIN and report,
retains the CRC, rejects mixed/modified/explicit-only inputs and links the new
assessment. Other review modes remain separate. All 20 root tests pass.

Fresh 95 instruction, 12 selected original updater header/name and 18 previous
loader compatibility checks pass. The identical MAIN's existing 18 assisted-QEMU
checks and nine frame hashes verify; QEMU was not redundantly rerun for the copy.
Stock, prior six-grid and owner-tested three-grid inputs are kept separately in
`.private/flash-review/20261027-spiral-01/`. No emergency recovery or physical
rollback is verified. Foreground acceptance does not resolve LCD/EVF/crop/DISP,
allocation/concurrency or real timing limits.

The expected Sony QD-G240F was freshly re-identified as E: and its six-grid EG
fully hash-matched. Backup: `.private/card-backups/20261027-spiral-b20cb240/EG161080.BIN`.
The spiral was staged as the only root BIN using a flushed/verified temporary copy
and final readback. Settings/WAV/root inventory remain unchanged. No photo-folder
edits, formatting, automatic ejection or camera operation by the agent occurred.
Sanitized evidence: `evidence/20261027-grid-spiral-flash-review.json`.

The owner was instructed to begin with 3x3 selected and use the rear LCD, then
choose Golden ratio after update/startup. Golden ratio now includes the curve;
no separate spiral row exists. While asked for the current/new screen, the owner
reported "flashing now. ill report back". Programming is owner-reported in progress,
not observed complete. Do not interrupt an active update. Await completion and
test Golden ratio, MENU return, and 3x3/Off following the camera's instructions.

## Automatic spiral paint proof and upstream merge — October 27, 2026

The owner asked to investigate automatic spiral drawing/removal. Read the new
automatic section of `GRID_SPIRAL_RESEARCH.md`. Separate private candidate
`.private/builds/20261027-spiral-lifecycle-01/` hooks the original Z7 dirty-widget
paint completion, retaining the original walker/return/pending-flag behavior.
No custom workspace, timer, capture hook, settings record or flash writer is
added. It combines the spiral with existing Golden ratio value 3; there is no
separate spiral menu choice yet.

MAIN SHA-256 `06b89e2a4eb864a96599eea504dd1d2f8aba05c8f072243c3a7d51c999fbd136`,
33,062,332 bytes. The explicit-draw parent has one additional guarded 12-byte
window (11 changed bytes), plus 352 appended bytes. Full independent rebuild
and CRC pass. Preset `grid-spiral-lifecycle-emulator-only` is rejected by ordinary
grid and flash-review admission. The earlier six-grid card file is untouched.

95 supplied-boundary instruction checks, 19 root tests and 18 assisted-QEMU
checks pass. Native MENU clears the curve and both tested returns automatically
restore it, without host draw calls or asset uploads. Choosing 3x3/Off through
exact compiled handlers while MENU owns the screen removes it on return;
Golden ratio restores it. Nine saved PNG hashes verify. The first visual run's
second MENU check falsely counted Nikon's yellow sidebar highlight; that failed
run remains preserved. Narrower observed-color classification has two new
regressions, and the full repeat passes. Sanitized evidence:
`evidence/20261027-grid-spiral-lifecycle.json`.

This is a feasibility proof, not a flash-ready implementation. The curve draws
over some status icons; layer ordering/owned UI integration is the next concrete
problem. Direct live-view erase, DISP/playback, EVF/crop/rotation, allocation
failure, concurrent painting and hardware performance remain unverified. No
camera/card access, new staging, flash clearance, publication or push occurred.

The owner also reported the WonderLantern PR merge. GitHub metadata confirms
`WonderLantern/z7-qemu#3`, "Support native Windows builds and controller
execution", is merged. Head `109671a14bd48729d6a7ed92402b2d7b229789d6` merged as
`110c8ab93278e32870ae136533b5ee8b17db19b3`, timestamp
`2026-10-28T02:12:21Z` (October 27 in Denver).
https://github.com/WonderLantern/z7-qemu/pull/3 . No additional upstream comment,
repository update or vendored-snapshot rebase was performed for this observation.

## Six-choice grid prepared and staged — October 27, 2026

The owner requested preparing a camera flash with the new grids, then confirmed
the card was mounted in response to the staging request. Only 4x4 / 3x3 /
Golden ratio (phi lines) / Center cross / 6x6 / Off are included. The Fibonacci
curve, sound and splash remain excluded. Read `GRID_LAYOUTS_FLASH_ASSESSMENT.md`.

Fresh `.private/builds/20261027-grid-layouts-flash-01/` exactly reproduces tested
candidate 02. Full EG is 33,056,174 bytes, SHA-256
`437e1f8edbb89f1409ad768dcf50e91725280481561fcaa8f0f161cc64e5dccc`;
MAIN SHA-256 `6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
Review bundle: `.private/flash-review/20261027-grid-layouts-01/`.
Convenient copy: `.private/flash-ready/20261027-grid-layouts/EG161080.BIN`.

Fresh 484 instruction checks and 12 updater header/filename probes pass. Eighteen
new previous-build compatibility checks show native journal loading retains all
89 payloads, old visibility/menu treat new values as Off, and old 3x3 can be
selected/saved/reloaded. These are supplied-boundary tests, not physical rollback.
The identical MAIN's earlier 35 QEMU checks and frame hashes were verified;
QEMU was not rerun for a byte-identical copy. All 17 root tests pass. The new
explicit `grid-layouts` review mode rejects old-mode/spiral report substitution.

The Sony QD-G240F was re-identified by model, serial, physical capacity, USB
bus and volume identity as E:. Its old EG matched the owner-tested saved-grid
build and was backed up/read back at
`.private/card-backups/20261027-grid-layouts-951c3dab/EG161080.BIN`.
The new EG was staged through a verified temporary copy, then renamed into
place. Final full hash matches, it is the only root `.BIN`, and settings/WAV
hashes plus the non-firmware root inventory are unchanged. No photo-folder
write, formatting, ejection or camera programming was performed.

Next checkpoint: safely eject, insert into the original Z7 C 3.80/no paid RAW
upgrade with fully charged supported power, and inspect the actual current/new
version screen before starting an update. There is no verified emergency
recovery if the camera becomes unbootable. Stock and prior EGs are preserved
normal-updater rollback inputs only, not a full flash/calibration backup.
Sanitized evidence: `evidence/20261027-grid-layouts-flash-review.json`.

## QEMU PR fix and reply published — October 27, 2026

The owner approved responding, requested no dash punctuation, and asked that
the public reply focus on Windows without mentioning other host testing.
The five-file smoke-test fix was committed and pushed to the existing fork
branch `tylermcm/z7-qemu:codex/windows-native-support` as
`109671a14bd48729d6a7ed92402b2d7b229789d6`. PR #3 now reports that head SHA.

Posted and read back the revised reply as `tylermcm`:
https://github.com/WonderLantern/z7-qemu/pull/3#issuecomment-6458021615 .
It acknowledges the overly strict quit-reply check, links the fix, and reports
23 passing Python tests on Windows plus three passing firmware-free smoke runs
against the existing QEMU 10.2.4 build. Its wording was verified against the
approved revision, including the requested punctuation and host scope.

The GitHub connector's comment action returned 403 (integration permission),
so the explicitly authorized comment was posted with the authenticated GitHub
CLI instead. The PR branch checkout is clean. The lab's vendored copy remains
updated locally; no additional lab main-branch push or release was made here.
No firmware, screenshots, dumps or runtime artifacts were published.

## QEMU PR response and prepared quit fix — October 27, 2026

The owner asked to look into answering the response on
https://github.com/WonderLantern/z7-qemu/pull/3 . R3tr0ooo reported that the
smoke helper falsely fails when QEMU exits cleanly before its quit reply;
their Python and sanitized GPU/ISP tests passed. Original pinned QEMU 10.2.4
`qapi/control.json` explicitly permits EOF before the quit acknowledgement.
The firmware-extension PR #1 had no returned comments at this check.

Prepared locally in the vendored component and the existing isolated PR
checkout `.private/pr-review/z7-qemu` on `codex/windows-native-support`:
require capability/status replies, send quit separately, and require process
exit 0 within ten seconds without reading a mandatory quit reply. Twelve new
synthetic TCP/process regressions cover EOF/reset, ordinary replies, errors,
nonzero exit and timeout. The synthetic server tolerates abandoned connection
attempts before the first command, after observed Windows loopback setup aborts;
it does not retry an actual protocol scenario.

All 23 Python tests passed on the isolated PR source. Three firmware-free runs
against the existing lab-built QEMU 10.2.4 executable passed. No Linux build,
ASan/UBSan run, firmware/UI run or camera test was repeated for this helper
change. QEMU C sources are unchanged. Publication inventories and code graph
were refreshed after review. This is a prepared patch and reply draft only:
no PR comment, PR push or main-branch push has been performed for this response.
The owner's request did not explicitly authorize posting the drafted message.

## Source push requested — October 27, 2026

The owner authorized pushing the additional grids, Fibonacci drawing prototype,
research notes, tests and sanitized evidence to `tylermcm/WonderLanternZ7` on
`origin/main`. This source update does not change the published preview tag or
assets. Nikon firmware, generated BINs/PNGs, screenshots, raw traces, local
runtime and Graphify output remain private and excluded from the commit.

The new straight-grid mode has 484 instruction and 35 assisted-QEMU checks;
the spiral drawing entry has 15 instruction and nine assisted-QEMU checks.
The 16 root tests pass. The earlier three-choice image/report still reproduce
exactly. These are scoped lab results, not new camera installation clearance;
automatic spiral redraw/removal is still pending. Exact evidence and remaining
work are in the two research documents below.

## Fibonacci overlay drawing proof — October 27, 2026

The owner asked to draw a Fibonacci curve on the golden-ratio grid. The
compiled UI-surface diagnostic now shows both over a live test image in QEMU.
Read `GRID_SPIRAL_RESEARCH.md` and `evidence/20261027-grid-spiral.json`.
Private successful frames: `.private/research/grid/20261027-spiral-native-ui-01/`.

`tools/build_spiral_probe.py` appends an immutable RGBA PNG and explicit drawing
entry, preserving every MAIN byte of the six-layout parent. New preset
`grid-spiral-draw-emulator-only`; MAIN SHA-256
`e76f8678add993cd0a665557c09bf081e675eb470937212761d108b0a8f1f5aa`.
The helper guards Golden ratio value 3, locks the native graphics mutex, selects
the registered 720x480 UI surface at 0xB045F200, draws through the original Z7
PNG path, restores the prior target and unlocks. No new lifecycle hook exists.
Use `tools/probe_grid_spiral.py --compiled` with this private build.

16 root tests, 15 supplied-boundary instruction checks and nine assisted QEMU
checks pass. The combined scene/grid/curve frame remains identical after two
seconds resumed. Direct-call experiment 01 had weak startup readiness; stricter
experiment 02 failed because its draw targeted a rotating live-image buffer.
Do not claim those earlier probes proved a usable combined overlay.

Automatic redraw/removal, grid-Off and MENU transitions, dynamic crop/EVF state,
memory/performance and concurrency still need integration/validation. Do not
blindly call PNG drawing from the geometry worker. No camera/card write, flash
clearance, push or publication occurred during that experiment. The source push
is authorized separately above. Existing grid and flash-review admission
reject the new image identity, and published default build outputs are unchanged.

## Additional grid layouts — October 27, 2026

The owner requested golden ratio and other photographic grids. A separate
optional lab mode now provides 4x4 / 3x3 / Golden ratio / Center cross / 6x6 /
Off, retaining existing scalar values 0..2 and adding 3..5. No card or camera
was accessed, and no new flash/release was authorized or performed.

Read `GRID_LAYOUTS_RESEARCH.md` and `evidence/20261027-grid-layouts.json`.
Build with `--native-choice --extra-grids`; preset is
`grid-layouts-emulator-only`. Tested private candidate 02 MAIN SHA-256:
`6485b0a579eb469701bcb89c442ab6b7faa1cea748dd3716cc524e500595b97f`.
Candidate 01 is superseded: its native geometry notification ran before the
golden adjustment. Candidate 02 adjusts before notification and passes both
native tail branches. Neither was staged.

484 instruction checks and assisted QEMU's 22 menu / 13 live-view checks pass.
All three new layouts were visually inspected, and each choice restores from
synthetic native flash into fresh CPU/RAM. Native journal schema/save policy
remain unchanged. The original three-choice image and report reproduce exactly
and its 107 checks pass; 12 root and 16 patcher tests pass with no skips.
Existing flash-review presets deliberately reject the additional-layout image.
Physical shutdown/durability/recovery and generic consumers remain unverified.

The default `--native-choice` output, published tag/assets and source-only
redistribution decision remain unchanged. Curves and diagonals require a
separate drawing path; the subsequent Fibonacci drawing proof is described
above. Diagonal guides remain unimplemented.

## Published source-only preview — October 26, 2026

Source commit `3a441180f80e6be26abff46d41d9210b53b7087c` was pushed to the
owner's `origin/main`. Public prerelease:
https://github.com/tylermcm/WonderLanternZ7/releases/tag/v0.1.0-grid-preview.1
The annotated tag resolves to that exact source commit. The release is
published, marked prerelease, and includes only the source ZIP, SHA256SUMS.txt
and RISK_NOTICE.md. **No Nikon BIN, dump, key or camera screenshot was uploaded.**

The source ZIP contains 208 reviewed source/text files, matching every hash in
its source manifest. It was extracted and used to reproduce the exact private
EG with SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
All three published assets were downloaded and verified byte-for-byte against
their local originals. Source ZIP SHA-256:
`2b9b8837a9e2b8d3320cc2c2c318c1428912133b04356a50627bf5140a9ba106`.
The private publication receipt is under `.private/releases/v0.1.0-grid-preview.1/`.

Release-time checks passed 16 patcher tests with private input/no skips, 11 root
and 11 QEMU Python tests, 292 renderer checks, 398 ISP checks, a firmware-free
QEMU smoke test, and the 45-file QEMU publication audit. Sanitizers were not
run. Scoped summary: `evidence/20261026-grid-release-validation.json`.
Prominent risk/no-warranty/liability notices are in README, RISK_NOTICE.md and
the release body, preserving component licenses and independent-work credits.
Reddit recommendations/draft are in REDDIT_POST_DRAFT.md; nothing was posted
or sent to Reddit/moderators by the agent. The release tag/source archive are
immutable to this follow-up bookkeeping update on main.

## Owner persistence confirmation and public preview — October 26, 2026

The owner confirmed that the latest existing-setting build was installed and
keeps the selected 3x3 grid after more than ten seconds off: "Yes, installed
and it stays 3x3". Associated staged EG SHA-256 is
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
This is one owner's report on one original Z7, without independent observation
or camera readback. Broader behavior/durability/recovery are not established.
Evidence: `evidence/20261026-grid-saved-owner-hardware.json`.

The owner requested pushing all code, an experimental release, a Reddit draft,
and very prominent camera-damage/no-liability wording. After reviewing Nikon's
official page (Reproduction: Not permitted), the owner chose **source/patcher
only**, keeping the full BIN private. Do not upload Nikon firmware as an asset.
`RISK_NOTICE.md` and `RELEASE_GRID_PREVIEW.md` contain explicit brick/data-loss,
repair/replacement, no-warranty and liability-disclaimer language, subject to
applicable law. Do not promise that this wording guarantees legal protection.
The release remains an independent modified preview, preserving all licenses
and credits; not official Nikon or Wonder Lantern work.

Planned preview tag: `v0.1.0-grid-preview.1` on the source-only lab repository
`tylermcm/WonderLanternZ7`. The user authorized publishing a prerelease, but
not posting on Reddit; `REDDIT_POST_DRAFT.md` is for their manual use. Check
GitHub for the actual tag/release/commit before reporting publication as done.

## Existing-setting grid staged for owner flash — October 25, 2026

The owner explicitly requested "lets copy it. im gonna flash it" after the
exact-candidate assessment was prepared. The Sony QD-G240F was identified again
as USB disk 2, E:, exFAT `NIKON Z 7_2`, with the same partition/volume identity;
the identity was rechecked immediately before copying.

`E:\EG161080.BIN` now contains the reviewed existing-setting candidate, 33,054,026
bytes, SHA-256 `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
It matches tested native-value candidate 02, and is the only root `.BIN`.
Temporary copy was flushed and verified, followed by final-name readback.
The previous working RAM-only file (SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`)
is verified in
`.private/card-backups/20261025-grid-saved-050104-05d1f496/EG161080.BIN`.
Its private `staging.json` records the operation at 2026-10-26 05:01 UTC
(October 25 local Denver time). No formatting or photo edits occurred;
NIKON001.DSC and SHUTTER.WAV root-file hashes were checked unchanged.

Card was not automatically ejected. The agent did not operate the camera or
observe programming. Owner intends to flash; installation/completion and actual
persistence are not yet reported. Use supported fully charged power and normal
on-screen update completion; select 3x3 once afterward, then check after at
least ten seconds off and a longer off period. Those intervals are persistence
tests, not expiry delays. Read `GRID_NATIVE_FLASH_ASSESSMENT.md`; physical
durability, other consumers and emergency recovery remain unverified.

## Existing-setting grid binary prepared — October 25, 2026

The owner requested the firmware build. Fresh
`.private/builds/20261025-grid-native-flash-01/` reproduces tested native-value
candidate 02 exactly (EG, MAIN and report). The convenient full component file
is `.private/flash-ready/20261025-grid-saved/EG161080.BIN`, 33,054,026 bytes,
SHA-256 `07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
Read `GRID_NATIVE_FLASH_ASSESSMENT.md`, not the older RAM-only assessment.
No card access, staging, ejection or camera programming occurred in this build.

The owner clarified the requirement: the selected grid should remain across
shutdowns of any duration until manually changed. Ten seconds off is only a
regression-test interval beyond the old retention cutoff, not a reset delay or
time-to-live. The new implementation has no timed expiry. Its intended durable
behavior still needs physical validation. Select 3x3 once after installation;
the old RAM-only type was not in native storage and cannot be migrated from it.

Review bundle `.private/flash-review/20261025-grid-native-01/` keeps this exact
candidate, untouched stock EG and official container separately. The helper now
admits `--preset grid-native` for offline review only, flags the changed value
encoding separately from the unchanged journal format, and links the correct
assessment. Six tests pass, including rejecting RAM-only files as native-value
artifacts and vice versa. All 12 exact-EG header/filename probes pass and three
bundle copies verify. Full CRCs/capacity/private-path checks pass. Prior 107
instruction and 16 QEMU checks apply to the identical MAIN; they are not a
physical persistence or emergency recovery result. Public scoped review summary:
`evidence/20261025-grid-native-flash-review.json`.

Before any future card staging, identify the actual card/drive again. Do not
replace the earlier working file merely because E: was used previously. Shared
reader consumers, presets/import/export, complete power lifecycle and recovery
limits are explicitly listed in the new assessment. The 90-record build remains
held and must not be substituted for this existing-setting candidate.

## Existing-setting grid persistence solution in the lab — October 25, 2026

Read `NATIVE_GRID_SETTINGS.md`. After the owner requested a solution for the
approximately three-second retention cutoff, a separate existing-scalar
prototype was implemented and tested. It stores Off/4x4/3x3 as 0/1/2 in Nikon's
existing grid scalar, normalizing only successful 0x102D/value-2 scalar reads
to boolean On. Owned menu/geometry code reads raw 2. Nikon's original worker
saves its original 89-record journal and original startup restores the choice
in fresh CPU/RAM instances. No added record, custom flash writer, journal hook,
heap reservation or conversion is used. This is the preferred next experiment;
the older 90-record prototype remains held.

Private candidate `.private/builds/20261025-grid-native-value-02/`, MAIN
33,054,024 bytes, SHA-256
`7f29bfda937c90261eff989d5f27dbf71ca2b142308b70879b1a7ef3d46c4075`.
Full EG 33,054,026 bytes, SHA-256
`07d77574bc9fed84d357b4e7c3df808127d361106c10ca26e0b6e2c818f6d0a7`.
Four guarded windows total 28 bytes, with 1,936 appended bytes. Independently
reproduced, valid CRC; preset `grid-native-value-emulator-only`.

107 instruction checks pass: 21,130 differential reads covering all 2,111
indexed properties plus invalid keys, native getter/visibility/menu/packed
snapshot, actual native request/worker/completion, fresh-RAM 3x3/4x4/Off reload,
original-stock startup preserving all 89 records with selected grid consumers
falling back to Off, sampled program cuts 1/269 and failed programming, plus
90 geometry calls. Candidate 02 also preserves original NZCVQ flags across the
shared reader and compares them across all indexed reads; candidate 01 is
superseded. Supplied OS/events/flash/UI/viewport/secondary datasets are
explicit boundaries; this is not a complete camera shutdown or physical flash
test. The optimized scalar differential helper avoids per-call Windows host
timers while enforcing instruction and ABI bounds; both full-key runs passed.

QEMU passes 10 native-key menu and 6 assisted live-view checks. Real native UI
service writes stored 2; both grid planes and Off work. These do not implement
persistent flash between QEMU processes. Scoped public summaries:
`evidence/20261025-grid-native-value.json` and
`evidence/20261025-grid-native-value-qemu.json`.
Patch/container/Thumb tests pass 14 with 2 optional stock-location skips; five
review path/admission tests pass. The previously installed RAM-only candidate
still independently rebuilds unchanged.

No new card/camera access or firmware staging occurred. At the initial prototype
stage the experiment was excluded from the review helper; the newer build
preparation above adds offline review admission. It changes a shared scalar-get
API for one key/value; generic consumers, U1/U2/U3, settings-file import/export,
toggles, wake, complete shutdown and physical durability remain review items.
Off stores 0 and forgets the prior type, unlike the older RAM-only last-type
behavior. Do not use the older RAM-only assessment to clear this new image.

## Owner-reported grid hardware success — October 25, 2026

The owner reports that the grid build works and measured its retention behavior:
selecting 3x3 survives switch-off/on when off for less than approximately three
seconds; longer off periods return to 4x4. This concerns the selected spacing,
not merely visibility. It resolves the earlier ambiguous delayed-reset report:
the observed threshold relates to time switched off. Exact boundary/repeat
counts were not supplied. Reliable persistence is not established.

The associated staged full EG SHA-256 is
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
Laptop hash/report were rechecked: only `grid`, 64-byte workspace, no journal
hooks. The initializer writes choice 0 when executed; equating it with every
physical off/on was an unverified assumption. The observed quick-restart
retention is consistent with temporary retained state, but that mechanism and
the actual shutdown/init paths have not been traced. No evidence of an on-state
spontaneous reset was reported. No new firmware changes or flashes were made
while recording these findings. The optional journal prototype remains held.

Next lifecycle regression should distinguish a rapid off/on from at least ten
seconds switched off; battery-removal retention remains untested. The threshold
is approximate owner timing, not a measured electronic cutoff. There is no
camera firmware readback or independent hardware observation. LCD plus EVF,
all choices, standby/wake, recorded-image checks, rollback and recovery remain
outside this report. The earlier staging entry describes laptop operations
before the owner's physical test. Evidence: `evidence/20261025-grid-owner-hardware.json`.

## Grid binary rebuilt and staged — October 25, 2026

The owner requested the binary for flashing and connected the XQD. E: was
identified afresh as the Sony QD-G240F, USB disk 2, 217,701,154,816 bytes,
exFAT volume `NIKON Z 7_2`; its partition/volume identity was checked again
immediately before staging. The card contains DCIM/NIKON directories and user
files; no formatting or photo/audio/settings-file edits occurred.

A fresh normal grid build at `.private/builds/20261025-grid-flash-01/` reproduced
the previously tested exact MAIN/full EG and report. The convenient local binary
is `.private/flash-ready/20261025-grid-only/EG161080.BIN`. The same full EG is
now the only root `.BIN` at `E:\EG161080.BIN`, 33,053,802 bytes, SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
Source rebuild, CRC, laptop copy, temporary card copy and final card filename
readback matched. Temporary card writes were explicitly flushed before readback.

The older root EG (SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`)
was copied to `.private/card-backups/20261025-grid-035528-be76f89e/EG161080.BIN`
and its backup hash checked before replacement. `staging.json` there records
the private operation at 2026-10-26 03:55 UTC (October 25 local Denver time).
It is the previous experimental sound file, not stock recovery firmware.

No camera flash occurred and the card was not automatically ejected. Next:
safely eject, insert into the original Z7 with supported fully charged power,
inspect Setup → Firmware version and obtain its actual current/new versions
before proceeding. Physical acceptance and emergency recovery remain unverified;
read `GRID_FLASH_ASSESSMENT.md`. Internal persistence remains held.

## Grid-only hardware-test preparation — October 25, 2026

The owner explicitly selected the simpler RAM-only grid build for the first
hardware test, holding internal persistence. Read `GRID_FLASH_ASSESSMENT.md`.
Preparation is complete at `.private/flash-review/20261025-grid-01/`.
Its full `candidate/EG161080.BIN` is 33,053,802 bytes, SHA-256
`ae46a48d52f4a89dac7c54bf63fc4b6d40b6c7d5adc49f67335e8b50fe97973b`.
It matches the complete independent rebuild of grid-emulator-03; MAIN hash
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
Only the grid feature is included: stock-based 4x4 / 3x3 / Off, with 4x4 as
cold-start choice. This replaces earlier custom sound/splash/M900/dual-display
features. No internal settings-schema change, outer-container repacking, version
spoofing, card access, staging or physical flash occurred.

Current checks: 192 grid instruction checks/270 geometry calls, including actual
native workspace allocator non-overlap; 12 exact-EG native filename/header
probes; 5 preparation path/admission tests; 14 patch/container/Thumb tests with
2 optional stock-location tests skipped. The same MAIN already passed 10 QEMU
native-key menu checks and 6 diagnostic live-view checks; current QEMU binary
and all five input source hashes match that evidence. Full EG/container CRCs,
capacity and three bundle file hashes verified. Scoped summaries are
`evidence/20261025-grid-preflash-instructions.json` and
`evidence/20261025-grid-flash-review.json`.

Next hardware step: identify the actual card/drive again, confirm current body
and power, stage the exact EG with readback hash, then inspect recognition.
Programming needs explicit owner authorization for this concrete reviewed
candidate. No verified emergency recovery exists. The assessment explains
normal-updater stock rollback limits and the post-install grid/wake/LCD/EVF
checks. Do not reuse historical E: identity or the old sound assessment as
clearance for this candidate. Do not select a persistent candidate for staging.

Separately hardened persistent prototype: `.private/builds/20261025-grid-persistent-05/`,
MAIN 33,058,292 bytes, SHA-256
`e230338d7d513a54b44cea6e0f2073e3b8f22aee15f0aa848f552d293ce1d8e7`.
It passes 74 persistence checks. Missing/damaged workspace or destination/length
tables now reject load/save without falling through to original journal writes.
Nikon-format conversion survives modified-firmware restarts and normal saves;
only an explicit grid choice reenables the extension. Important native contract:
the third word of each schema triple is a mutable flash-source cache, not a
dirty flag. An initial overly strict guard rejected those native cache updates;
candidate 04 is superseded, candidate 05 validates immutable pairs instead.
The rollback function is still diagnostic, with no camera-accessible action.
It and full lifecycle/concurrency/physical durability remain on hold. Candidate
02 separately passed 10 native-key QEMU menu checks this turn; that does not
validate later candidate 05 or persistence across QEMU restarts.

## Compiled persistent-grid prototype — October 25, 2026

The owner authorized implementing internal persistence and building/testing it
in the lab. Current private candidate:
`.private/builds/20261025-grid-persistent-02/`, MAIN 33,057,940 bytes, SHA-256
`a0cda3a3c4acac326cfbc56ac9aca48b075f09c3a5742f8470a5f7da79bd508c`.
It is reproducible with valid EG CRC and independent full rebuild validation.
No outer update package, staging, camera/card access or installation clearance.

`features/settings_z7.py` adds guarded native journal descriptor/load/save/reset
hooks to the optional `grid_z7.build(..., persistent=True)` path. Ordinary grid
builds remain unchanged. `tools/build_grid_firmware.py --persistent` explicitly
selects the new emulator-only preset. It reserves 0x500 bytes at A9700000,
including an owned 90-record table. Record 89 is 16 bytes: magic WLS1, version 1,
grid choice 0/1, IEEE CRC32 of the first 12 bytes. Native property 0x102D stays
0/1; the live choice remains one aligned word at STATE+4.

Load tries extended format, retries original format before Nikon's reset path,
and defaults only extension data when its CRC/version/value is invalid. Saves
hook the normal main-journal routine, capture all native payloads plus extension
state into an immutable snapshot, and read back into separate buffers. The
176,744-byte temporary allocation is checked/freed; all payloads are compared,
native descriptor/logical-view pointers restored, and dirty state retained on
failure or generation changes. No UI/geometry hook writes flash directly.

`tools/audit_grid_persistence.py` passes 53 checks: compiled CRC, cold ABI,
fresh-instance 3x3/4x4 reloads, actual native startup caller, native reset,
old-format migration, CRC corruption, failed readback, allocation/program
failure, busy saves, generation changes, original-format conversion and six
program-boundary interruptions during first migration. All 89 native records
survive the sampled interruptions. These execute native instructions in
Unicorn with supplied OS/allocation/flash-controller boundaries; they do not
establish physical durability or a full QEMU persistence/reboot cycle.

The updated grid instruction audit passes 190 checks/270 geometry calls on
candidate 02. It also passes all 190 on the unchanged earlier RAM-only build.
Patch/container/Thumb tests pass 14; two optional integrations remain skipped.
Assisted QEMU live view passes all six checks at
`.private/research/grid/20261025-persistent-live-01/`, session
`20261025-141908-5174`; compiled handlers select native grid planes and Off
restores the scene. This QEMU probe does not persist flash across restarts.
The native-key menu probe has not been rerun on this persistent candidate.

Public scoped summaries are `evidence/20261025-grid-persistence.json`,
`evidence/20261025-grid-persistent-geometry.json`, and
`evidence/20261025-grid-persistent-live.json`. Read the implementation section
in `SETTINGS_PERSISTENCE_RESEARCH.md` before continuing. A diagnostic rollback
function is compiled and verified against a fresh unmodified stock loader,
but has no camera menu/updater integration. Its mode is RAM-only: do not power
cycle the modified firmware between conversion and a future stock update.
Wake/concurrency, repeated compaction/endurance, complete shutdown policy,
updater ordering, user-visible failure reporting and physical recovery remain
open. Invalid/missing workspace state currently falls through to original
storage APIs; audit fail-closed behavior before considering any installation.
The splash experiment still cannot compose with this workspace reservation.

## Internal settings persistence investigation — October 25, 2026

Read `SETTINGS_PERSISTENCE_RESEARCH.md`. The owner wants extension settings
inside the camera, independent of card swaps. `tools/trace_settings_storage.py`
passes 45 checks against pinned original instructions in isolated Unicorn.
The main settings journal is logical `0x0F`, with 89 native records and two
`0x40000`-byte regions at `0x12E00000` / `0x131E0000`. A supplied 90th record
survives fresh-instance save/load while preserving all native payloads. Explicit
old-schema retry/migration and original-format rollback conversion also work
with supplied descriptors. Bare schema replacement fails in both directions.
No migration, rollback or persistence hook has been installed in firmware.

Correction: the raw `0x102D` scalar writer accepts 32-bit values, including 2;
it does not enforce boolean semantics. Native menu/display code supplies or
compares 0/1. Raw setter acceptance is not compatibility. The main journal
wrapper also returns success after injected program failure; read-back is
required. Public scope/results: `evidence/20261025-settings-storage.json`.
No firmware build, camera/card access or full QEMU cold boot occurred. The
existing grid candidate remains RAM-only.

## Native 3×3 grid investigation — October 25, 2026

Read `GRID_3X3_RESEARCH.md`. The original investigation now has a standalone
emulator-only firmware candidate with native d9 choices **4x4 grid / 3x3 grid /
Off**. Keep the existing 4x4 choice. Grid choice is separate RAM state, defaulting
to 4x4 at workspace initialization; Nikon's native property 0x102D stays boolean.
The choice is not saved persistently. No card access, physical flash or outer
Nikon update package was involved; camera installation remains on hold.

Current private build: `.private/builds/20261025-grid-emulator-03/`.
MAIN is 33,053,800 bytes, SHA-256
`2762ccd5276e1c4720c06e26f636c6c551cafe3772eb6d24400b769c200cd348`.
Four guarded windows total 32 bytes, with 1,712 appended bytes. Builds/reports
are reproducible with valid EG CRC; the probe independently rebuilds the entire
MAIN/report. Normal installation presets exclude this feature. Do not compose
it with the splash experiment: both own the same workspace-init reservation.

`features/grid_z7.py` derives its geometry/table/property/UI contracts from
original Z7 C 3.80. The builder 0x10376DA0 uses three immutable 32-byte records
at 0x1064FD90; an atomic RAM choice selects the stock table or an appended
copy with two internal lines per axis. Dynamic-label flag 0x1209 and both native
focus/current-value helpers are required; earlier candidates exposed these UI
details and were superseded.

`tools/build_grid_firmware.py`, `tools/audit_grid_firmware.py`, and
`tools/probe_grid_firmware.py` provide build, instruction audit and isolated
menu/live probes. Final instruction audit passes 190 checks/270 geometry calls,
including cold reservation/ABI, invalid-state fallback and current-value marking.
The earlier pure geometry audit passes 91 checks. The QEMU production renderer
suite passes 292 checks; strict firmware-free register contracts pass 14.
Existing patch/container/Thumb suites pass 14, with 2 optional integrations
skipped; RAW-input suites pass 11 with workspace-local temporary storage.

The grid is a separate hardware display plane. The stock 0x20145620=1 stop
was resolved by the traced boolean write contract, then a functional LCD-grid
model was added from native registers 0x1600..0x1618. Observed black/gray styles, half-open
edges and plane priority remain explicit hypotheses. No invented completions
or host drawing injection is used. EVF and physical bit accuracy remain open.

Final native-key menu probe passes all 10 checks: initial Off plus 3x3, 4x4 and
Off selection/reopen, with correct labels, focus and current-value outlines.
Private evidence: `.private/research/grid/20261025-selector-final-02/`.
The earlier `20261025-selector-final/` run hit its 420-second watchdog; it is
superseded, preserved, and not a full pass. The runner now allows 900 seconds.

Final assisted live-view probe passes all 6 checks: compiled choice handlers
and the native visibility update produce visible thirds/quarters through the
emulated hardware plane, then Off disables the plane and restores the sampled
scene pixels. The entire final Off PNG additionally matches the initial PNG
byte-for-byte. Private frames: `.private/research/grid/20261025-live-final-02/`.
Native 1024x682 alignment yields thirds x=342/684, y=228/456; quarters
x=256/512/768, y=170/340/510. Color/priority remain emulator hypotheses.

Public source-only evidence: `evidence/20261025-grid-firmware-qemu.json`,
`evidence/20261025-grid-firmware-unit-v3.json`, and
`evidence/20261025-grid-display-latch-final.json`. Camera LCD/EVF behavior,
recorded files, wake/concurrency, persistent choice storage, composition,
installation acceptance and recovery remain unverified. Do not stage or flash.

## Image-creation feature shortlist — October 25, 2026

The owner wants useful shooting features inspired by newer Nikon bodies with
similar hardware. Read `IMAGE_CREATION_FEATURES.md` for the official-manual
comparison, current Z7 baseline, ranked candidates and evidence gaps.
Suggested first investigations: native 3×3 grid/framing guides, still-photo
highlight stripes using the existing movie path, independent M900 property/timer
audit, then a recipe selector based on compatible native Picture Controls.
The D780 provides an EXPEED 6/900-second precedent; Z7II/Z6II are dual EXPEED 6
and cannot be treated as throughput-equivalent to the original body.

The source review confirms that existing M900 still overrides property 0x11A3;
the port audit requires independent Z7 meaning and physical timing verification.
Do not turn that experiment into a newly completed feature claim. Existing
Creative Picture Controls, focus shift/peaking-stack preview, bracketing and
supported-lens focus recall are part of the stock baseline, not new unlocks.
Newer display/AF examples are design references; port feasibility is estimated.
No new firmware build, staging or camera access occurred for this research.

## Firmware-owned splash experiment — October 24, 2026

The owner explicitly authorized building a firmware and running it in QEMU.
That is a narrow exception to the earlier no-build hold for this emulator
experiment. Camera installation, staging and flash recommendations remain on
hold; no card/camera access or outer Nikon update package was involved.

`tools/build_splash_firmware.py` builds independent Z7 C 3.80 MAIN/EG images
from the pinned original container, twice reproducibly with valid EG CRC.
Every QEMU input is independently rebuilt and compared in full, including its
report. The feature is excluded from ordinary installation presets.

Current private build: `.private/builds/20261024-splash-emulator-02/`.
MAIN is 33,067,836 bytes, SHA-256
`dc6ec38c9b427374afd80be53d31d14edb4914e89f06abc73099a9e12f021f24`.
EG SHA-256 is
`a60b0c9db5003db532ffe596848e8ea8ae9e390b3b4928ab3c1066316ede2fd3`.
Three guarded instruction windows totaling 32 bytes are replaced; 15,748 bytes
of independent code/padding/PNG assets are appended.

`features/splash_z7.py` reserves 64 bytes at 0xA9700000 through the original
monotonic workspace initializer (cursor starts at 0xA9700040), arms after
original UI resource setup, and atomically consumes its own latch at the first
native full-screen clear. The 0x1042F152 hook accepts caller 0x104FFB19 only
with `[0,0,720,480,255]`; it runs before any visible menu paint. Both PNGs
are embedded in ROM. Native 0x10431738 performs splash/black cleanup drawing;
native delay 0x1017081E receives argument 2000. That argument is not a physical
two-second timing claim. The displaced original prologue then resumes.

`tools/audit_splash_firmware.py` passes 40 instruction/ABI checks, using mocked
OS/GPU boundaries. Evidence: `evidence/20261024-splash-firmware-unit-v2.json`.
The existing patch/container suites pass 11 + 3 tests. Physical low-memory,
concurrency, wake/LCD-EVF behavior, updater acceptance and recovery remain unverified.
Read the current section in `SPLASH_SCREEN_FEASIBILITY.md` for reproduction.

Two fresh assisted QEMU cold boots pass 27 checks each, with the exact embedded
splash as the first observed nonblack frame, native timed handoff, intact state
guards, complete native menu redraw/navigation and one presentation through
menu exit/re-entry. No host splash controller or drawing injection is involved.
The base boot still supplies synthetic power/system/MENU fixtures. Public
source-only evidence: `evidence/20261024-splash-firmware-qemu.json`; private
frames/state and logs: `.private/research/splash/20261024-firmware-03/`.
This proves the firmware lifecycle in assisted QEMU, not physical instant-on,
unassisted boot, live-view startup or readiness to flash.

Rejected first build and test runs remain private. Continuous QMP observation
caught an earlier 64-pixel gray sidebar before the PNG-builder hook; the earlier
host prototype's sampled "first-visible" claim did not test that interval.
Original queue tracing identified the earlier clear hook used now. Test-only
redraw waits were also corrected after exact comparisons caught text still being
painted. Keep these failures in the record; do not turn their partial successes
into installation clearance.

## First visible screen corrected — October 24, 2026

Historical host prototype, superseded by continuous firmware observations above.

The owner correctly rejected the previous preview's menu -> splash ordering.
The startup probe now intercepts the first native drawing call at 0x10430256
while the QEMU surface is still black. It draws the splash in that native
rendering task, holds that task with native OS delays while other guest tasks
run, restores a black backing through native PNG/GPU drawing, and resumes the
original first draw. The menu is only visible after the splash.

Two cold boots pass 41 checks each; source-only evidence is
`evidence/20261024-splash-first-frame.json`. Private artifacts are in
`.private/research/splash/20261024-first-frame-startup-02/`. The first normal
scene and later navigation are verified, including exact scene comparison at
the same established focus state. A native help-icon backing changes on its
first focus cycle; preserve the initial screenshot rather than masking that
difference in an exact-pixel comparison.

The original MENU fixture still schedules the first native scene internally;
the splash runs before that scene paints visible pixels. Removing MENU setup
and drawing from the idle application task produced a splash but no usable
handoff. Those unsuccessful runs remain private and are not cleared methods.
The new method is still a host-assisted rendering-boundary experiment, not a
firmware patch, physical instant-on result or live-view startup implementation.
The local replay viewer uses this corrected sequence. No camera/card access,
new firmware image or flash occurred; the port/installation hold remains.

## Automatic splash lifecycle experiment — October 24, 2026

Historical overlay experiment: this version waited for the menu, so its passing
checks did not establish the owner's required first-screen startup order.

The owner asked to investigate automatic startup. `tools/probe_splash_startup.py`
observes original UI initialization and automatically schedules the existing
native PNG draw after the first stable native display. Two fresh assisted cold
boots pass 30 checks each: one presentation, exact pixels, approximately two
host seconds of visible hold, exact scene restoration, MENU exit/re-entry and
navigation without re-showing. Results are source-only in
`evidence/20261024-splash-startup.json`; frames/traces remain private in
`.private/research/splash/20261024-auto-startup-02/`.

Important: the outer UI initializer 0x102697F4 runs again on MENU re-entry. It
is not a boot-only trigger. Its resource-setup block checks initialized guard
0xA1822D68, calls 0x103F9C0A, then clears the guard at 0x1026984A. Both cold
traces observe guard 1 in this block and guard 0 afterward; subsequent menu
initialization does not rerun resource setup. The host prototype arms at the
post-resource-return observation, consumes its own one-shot before drawing and
never modifies the native guard. This does not prove physical wake semantics.

Readiness detection, the one-shot state and timed synthetic focus redraw are
host policy, not installed firmware hooks. Production work still needs a native
graphics-ready/render-task event, an independent cold-reset latch and verified
timer/dismissal/wake/LCD-EVF behavior. Do not hook the outer initializer
unconditionally or repurpose its guard. The original display probe shares the
heap-backed drawing helper; its regression evidence is kept privately alongside
the new runs. All 14 original display checks pass after that refactor in
`.private/research/splash/20261024-display-probe-07/`. No firmware build,
card staging or camera access occurred; the
port/flash hold remains active.

## Splash takes priority — October 24, 2026

The owner wants splash loading investigated before film-roll work. Read the
new section in [SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md).
`tools/probe_splash_display.py` now presents an original 720x480 RGB PNG through
stock Z7 code in an isolated assisted QEMU guest. All 14 presentation checks
pass: exact full-screen pixels, native decoder/GPU trace, encoded-image heap
guards, caller register/scratch restoration, exact native menu restoration and
subsequent menu navigation. The PNG uses original heap allocation; only an
80-byte descriptor is staged on the diagnostic caller's stack. A fresh run and
private screenshots are in `.private/research/splash/20261024-display-probe-06/`;
sanitized results are `evidence/20261024-splash-native-display.json`.

This is host-assisted native presentation, not an automatic startup hook or
flashable splash feature. Earlier oversized stack-data and cross-task graphics
lock probes stalled or left the guest unresponsive; do not reuse those methods.
The successful probe supplies encoded PNG data only, with no host framebuffer
pixel writes. It closes its own guest and leaves existing app sessions alone.
Next: establish the correct startup/render-task transition, once-per-boot state,
bounded dismissal, wake suppression and LCD/EVF behavior. No firmware build,
card staging or camera access occurred; the port/flash hold remains in force.

Earlier offline milestone:
`tools/audit_splash_image.py` executes the stock resource getter, image wrapper,
libpng/zlib and original memory helpers with a controlled bounded allocator.
All 43 checks pass, including exact RGB/RGBA pixel output, buffer guards,
callee-saved registers/stack and selected allocation-failure cleanup. The
320x120 synthetic PNG decodes to 153,600 RGBA bytes. Evidence is source-only.
These unit checks alone do not verify GPU/LCD presentation. Startup event
semantics, production dismissal and wake suppression remain unverified.

## Film-roll feasibility — October 24, 2026

The owner asked whether a Canon Ritual-style experience could be built for Z7.
Read [FILM_ROLL_FEASIBILITY.md](FILM_ROLL_FEASIBILITY.md). Native custom Picture
Controls provide the initial recipe path. Nikon's original-model manual already
documents 20 Creative controls, contradicting the inherited report's dormant-
feature premise. A correction banner preserves that report while marking its
unsupported conclusions. Three narrow stock-image checks are recorded in
`evidence/20261024-picture-control-baseline.json`; no complete parser or new
rendering was validated. Photo counting, persistence and a hard shutter limit
remain research tasks. No firmware build, staging or camera/card access occurred.

## Source publication checkpoint — October 24, 2026

The owner requested a source push and review of possible contributions to both
vendored upstream projects. The root README now reflects the hardware reports:
WAV Preview works, automatic capture sound repeats during live view, and Enabled
OFF contains the loop. Historical preparation and test instructions below are
not current installation clearance. The port audit and flash hold remain active.

The latest stock assisted-emulator observation collected three distinct
0x041F0001 -> 0x04190001 callback deliveries without a shutter action. Controller
mode was 0 and the native capture-service state byte was 9 in each observation.
Read the new section in [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md) and the
sanitized summary `evidence/20261024-stock-liveview-observation.json`. This is
negative evidence against the current trigger, not a physical-camera trace.

A separate stock capture-request probe timed out before recording any action;
it establishes no positive capture signal. No firmware source was changed for
these observations and no new candidate was built, staged or installed. Private
RAM, disassembly, emulator sessions and probe logs stay excluded from publication.

Publication checks were rerun on October 24: 8 root host tests, 11 QEMU Python
tests, 270 renderer contracts, 398 ISP contracts, firmware-free QMP realization,
and 14 synthetic patch/container tests passed. Existing-image probes passed 24
native-callback, 14 still-file and 60 selected callback/property checks. The
retrigger audit still fails both required no-photo rejection checks; its two
OFF checks pass. These results do not clear automatic shutter sound. No new
firmware build, camera update or sanitizer run was included. See
`evidence/20261024-source-validation.json` for scope and exclusions.

## Backward tracing anchor: still-file record — October 22, 2026

The owner asked how to obtain a verified per-photo signal. Read
[STILL_FILE_TRACE.md](STILL_FILE_TRACE.md). Original still-file finalization wrapper
0x1026FADC sends 0x041E0002 with a record ID through a separately registered
callback. Native record helpers expose slot/group/number/kind fields and compare
records while ignoring kind. Fourteen offline evidence checks execute that
wrapper, registration/dispatch and ID helpers with controlled file operations.

This is a new backward-tracing anchor, not a chosen shutter hook. File completion
can lag exposure, repeat or occur multiple times per photo; physical timing and
per-photo cardinality remain unverified. Follow upstream exposure/record creation
before connecting audio. No firmware source, image or camera/card content changed;
Enabled OFF and the flash hold remain in force.

## Native callback trace — October 22, 2026

The owner asked to keep tracing. Read [CAPTURE_EVENT_TRACE.md](CAPTURE_EVENT_TRACE.md).
The new audit executes the original registered Z7 callback instead of stubbing
its return. Two supplied classification cases schedule no native work, but the
existing sound hook still queues audio. Six stock/patched cases retain native
scheduling while exposing that unconditional custom admission. A separate native
zero-count AutoRelease probe also emits its request notification without invoking
release control, ruling that notification out as sufficient per-photo evidence.

All 24 trace evidence checks pass; this confirms the defect, not a replacement
trigger or candidate clearance. Real per-photo signal semantics remain unresolved.
Enabled OFF is owner-confirmed to stop repetition. Firmware source and existing
images were untouched; no rebuild, staging or camera write. The flash hold remains.

## Latest hardware failure: repeated live-view audio — October 21, 2026

The owner reports repeated sound during live view and Capture audio busy on
opening the menu. Read [LIVEVIEW_SOUND_REGRESSION.md](LIVEVIEW_SOUND_REGRESSION.md).
The owner confirms Enabled OFF stops the repeating sound on the camera. Leave it
OFF. This confirms containment, not correct shutter triggering. The latest
silent-property candidate is associated by sequence, without firmware readback.
It fails the shutter-cue behavior requirement; audible repetition is not success.

An audit-only probe of the existing binary queues three requests from three
notifications without an independently identified photo transaction, and confirms
the pending/finished restart path. Two required rejection checks fail; two compiled
OFF checks pass with controlled device boundaries. The callback's photo-specific
meaning was never established. Earlier passing callback tests missed this case.
No firmware source change, rebuild, staging, camera write or rollback occurred.
The port audit and flash hold below remain in force.

## Current owner caution and port audit hold — October 21, 2026

The owner raised the risk of ported camera code leaving the Z7 unusable and asked
for more care. Further flash recommendations and candidate staging are on hold
pending an independent Z7 port audit. Read [PORT_AUDIT.md](PORT_AUDIT.md) before
continuing. The most recently staged silent-property image remains experimental;
the earlier preparation/testing notes below are not clearance to install it.
Do not interrupt a camera update already running. Do not automatically roll back,
reflash stock, or prepare another candidate as a response to this concern.

Initial review confirms a Z7 stock base with Z30-derived custom feature code, not
proof that all copied interfaces are correct. The inventory identifies 23 direct
literal native sound call targets and 17 full-image edits; dynamic/assembly-embedded
targets and lifecycle/recovery gaps remain. The native translation dictionaries
are not used by the generated routines, so reviewing them alone is insufficient.
No camera/card/firmware mutation occurred in this audit turn. No complete port
audit or verified emergency recovery is claimed.

## Current Silent photography property correction — October 21, 2026

The owner followed the capture-start candidate's installation/test instructions:
still no audio, now with heading Silent mode required after a silent photo.
This supports trigger reachability; the remaining mode gate queries the wrong
property. The Z7's own Silent photography page 0xB2 constructor reads 0x576;
the port retained Z30 key 0x57B. Read [SILENT_PROPERTY_FIX.md](SILENT_PROPERTY_FIX.md).

New private build/review suffix: `20261021-silent-property-01`, full EG SHA-256
`9e636d645281ee9f92cb150b6dcc8d771b21ff95c47e45f538d951a1d932420b`.
Exactly one appended instruction byte plus two CRC bytes differ from the previous
candidate; length and menu/Preview code are unchanged. Both sound presets pass
60 capture checks and 18 playback checks using the original native property
getter/tables. Contradictory Z7/legacy values also execute the original Silent
photography menu constructor, exposing the previous mocked-getter test gap.
Sixteen firmware tests and reproducible/CRC checks for all four presets pass.
The candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 04:38 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above. The previous card EG was backed up privately; SHUTTER.WAV and
other card files were preserved. The review bundle's card-staging.json records
the copy. The subsequent live-view regression above supersedes this pending
status: installation is inferred, and correct physical capture audio has failed.

## Current normal-capture callback correction — October 21, 2026

The owner now reports Waiting for capture after silent shooting, and Silent mode
required after one mechanical photo with the feature still enabled. This supports
the installed diagnostic build and late-hook mode gating, with no late-hook
notification observed for silent capture. Installation is inferred from the unique
headings; no readback or explicit updater-completion report was supplied.

Read [CAPTURE_START_FIX.md](CAPTURE_START_FIX.md). A separate normal native
callback at 0x100726AC was outside the previous diagnostic's coverage. The new
hook queues sound from its normal notification and retains the late hook for
diagnostics only, avoiding duplicate cues. All three callback paths and the full
native dispatcher now pass 48 capture checks for each sound preset; the existing
18 playback checks and 16 firmware tests also pass. Hardware triggering remains
unresolved until a camera retest.

New private build/review suffix: `20261021-capture-start-02`, full EG SHA-256
`efcfbda40439354e8707a2c1e8c0b16b5e47a27c0fe8999110ca98eb9f15dc1c`.
It was staged on the re-verified E: Sony QD-G240F card at 2026-10-22 04:10 UTC
(October 21 locally). Full SHA-256 readback matched the candidate above. The
previous card EG was backed up privately; SHUTTER.WAV and other card files were
preserved. The private review bundle's card-staging.json records the copy.
The owner subsequently followed the installation/test instructions and reported
Silent mode required after the silent photo, with no audio. Installation is
inferred from that sequence without readback; the property fix above supersedes
this candidate. The first offline relocation attempt failed
null-callback branch checks and was corrected before producing this candidate.
The candidate passes 13 admission checks, 12 private review checks and all 17
assisted-QEMU sound-menu checks with 30 native key events and return to live view.
No abort was observed in that run. The source graph has been refreshed locally.

## Startup splash investigation — October 21, 2026

The owner asked whether a custom splash could be installed. Read
[SPLASH_SCREEN_FEASIBILITY.md](SPLASH_SCREEN_FEASIBILITY.md). Private stock scans
confirm PNG resources and libpng strings, with 198 of the first 200 signature
hits verified by Pillow and 16 large resources verified by chunk CRC. An original
compact embedded image plus a one-time native UI hook is promising; no startup
logo replacement, callable decoder interface or power-on-only hook is yet proven.
The current EG has 489,334 bytes of room under the existing patcher limit. This
was read-only firmware investigation; no splash build or card/camera write occurred.

## Current capture-trigger investigation — October 21, 2026

The owner clarified that WAV playback works but shutter replacement does not,
with Enabled ON, SHUTTER.WAV selected and Nikon Silent photography ON. Read
[SHUTTER_TRIGGER_FIX.md](SHUTTER_TRIGGER_FIX.md). A native branch bypasses the
old hook entry and lands inside its patched literal; this is reproduced offline.
The new shared-callback hook preserves both native paths and passes 24 capture/
diagnostic checks for both sound presets. Diagnostic titles distinguish callback
reachability from mode/busy gating. The role of this defect in the failed camera
test remains unknown; actual shutter-triggered sound still fails by owner report.

After diagnostic staging, the owner again reported no shutter sound and initially
could not identify the expected heading (described as a "tile"). The later
Waiting for capture / Silent mode required comparison is recorded above. The diagnostic
is the page title above Enabled/Sound file/Preview/Reload, not a new menu row.
With Enabled ON and no error it should initially read Waiting for capture;
after a photo read that heading without power-cycling or selecting ON again,
which resets the capture status.

New private build/review suffix: `20261021-shot-fix-01`, full EG SHA-256
`51dd7feb01e991d0cbce93e952ac42be98981dca510187e2767141ec8974dd9b`.
The diagnostic candidate was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:39 UTC (October 21 locally), with full SHA-256 readback matching
the candidate above. The previous card firmware was backed up privately;
SHUTTER.WAV and other card files were preserved. The private review bundle's
card-staging.json records the copy. The later unique diagnostic headings above
support this build running on the camera, inferred without firmware readback.
The new build also passes 13 candidate checks, 12 private review checks and all
17 assisted-QEMU sound-menu checks on an isolated retry. The first QEMU attempt
stopped during assisted menu entry; both outcomes are preserved in the sanitized
capture evidence. Card staging and the later inferred installation are recorded
above; shutter-triggered audio has not passed.

## Current audio correction — October 21, 2026

**Latest owner result: "the wav actually works now!"** This follows staging the
corrected candidate below and the installation/Preview instructions. Record this
as owner-reported audible WAV playback; the subsequent capture failure above
separates that result from shutter-triggered playback.
Corrected installation is inferred from that sequence, without firmware readback.
Shutter-triggered playback, repeated-use stability and recovery are not established.

Read [AUDIO_PLAYBACK_FIX.md](AUDIO_PLAYBACK_FIX.md). The owner tested the stronger
WAV: still no audible output; Sound busy appears when moving the selector after
activation. The file matches every documented 8 kHz/mono/16-bit/canonical-header
requirement. The installed code reads the format table instead of the native busy
byte, and requests a type outside the native exclusive range. Both blockers are
corrected in source, with five failing checks reproduced against the installed
image and all 18 request-path checks passing for corrected full and sound-only.

New private build/review directory suffix: `20261021-audio-fix-01`. Full EG SHA-256
is `770408b99ff547dd972486656285307b17e4ff2674937dbb50f144200233b7be`.
The corrected firmware was staged on the re-verified E: Sony QD-G240F card at
2026-10-22 03:08 UTC (October 21 locally). Full SHA-256 readback matched the
candidate above; the previous card firmware was backed up privately, and the
stronger SHUTTER.WAV and other card files were preserved. The private review
bundle's card-staging.json records the copy. The owner subsequently reported
working WAV playback as recorded above. Earlier silent-playback reports below
describe the previous build, before this correction.

The corrected full image passed 17 isolated QEMU menu checks with 30 native key
events. All four builds are reproducible with valid CRCs; 16 existing firmware
tests, 13 candidate checks and 12 private review/header checks passed. Both sound
presets passed 18 playback-admission contracts. Results are recorded in
`evidence/20261021-audio-playback-fix.json`. Root default/native app configuration
still names the earlier private build; launch the corrected build explicitly
when inspecting it. Restart validation of an older payload against the changed
patcher source will intentionally reject it; the previous binaries are preserved.

## Latest hardware result — October 21, 2026

The owner reports **the flash worked and the sound setting is present** on the
original Z7 C 3.80, no paid RAW-video upgrade. This follows the camera's
`Current A3.80 → New A3.80` confirmation and an updating warning/progress report
at about 30%. The verified card candidate was the full EG with SHA-256
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.

This establishes an owner-reported same-version installation, subsequent camera
operation and visible sound-menu entry. The exact completion message, firmware
readback, submenu operation, WAV loading/playback, capture, video and recovery
have not been independently observed. Do not expand this result to full hardware
validation or a proven rollback path. Earlier preparation notes below describe
the state before this first installation.

A private canonical test sound is prepared at
`.private/sound-test/20261021-01/SHUTTER.WAV`: 0.18 seconds, 660 Hz, 8 kHz,
mono signed 16-bit PCM, with fades and approximately 6% full-scale peak. Its
44-byte header, sample count and exact normalization roundtrip passed. At the
owner's request it was copied to the verified E: Sony QD-G240F card root as
`SHUTTER.WAV`; complete readback matched SHA-256
`e8bc84dc82c53e36c5ec8fc8a28556272b367a7e93ed0e0c91782797ea7ea5cb`.
Existing card files were preserved. The private sound-test `card-staging.json`
records the copy. The owner then reported **Sound file shows SHUTTER.WAV;
Preview produces no error but nothing audible**. Loaded-file/menu behavior is
owner-reported; audible output has not passed. Preview is designed to work with
Enabled OFF. Ordinary photo/playback has not been explicitly reported.

On resuming October 21, a stronger test WAV was staged on the re-verified E:
Sony QD-G240F card: `.private/sound-test/20261021-02/SHUTTER.WAV`, 14,444 bytes,
SHA-256 `d9b38aae45fbe7cb6ccbe79e64bafc40c2d69d987beb6608f00d8c0fc1145ac0`.
It contains three faded notes at 1, 2 and 3 kHz, 0.9 seconds total, 50% peak
amplitude. The earlier 0.18-second/6% tone is preserved locally, including a
verified copy of the old card file. Both WAVs passed the exact installed full
image's native validator and converter; every converted stereo PCM byte matched
the independent interpolation reference, output was nonzero and buffer guards
held. This checks parsing/conversion, not audio scheduling or speaker output.

The new card file passed complete SHA-256 readback. Firmware and other card
files were not changed; another flash is not needed for this test. Next safely
eject, insert into the camera, select Sound file → SHUTTER.WAV again and use
Preview with Enabled OFF. Audible output from this stronger file is pending.
If still silent, investigate native audio routing/gain and use normal Nikon
beeps as a separate control; do not infer a volume-only cause from the first test.

## Native Windows continuation — October 21, 2026

The app now runs on this laptop without WSL. Double-click `Start-Z7.cmd` or open
<http://127.0.0.1:8787/> while the prepared server is running. It was left paused
after verification to save CPU; click **Resume**. English browser controls and
keyboard/menu instructions are included. The selected private build is
`.private/builds/20261021-laptop-01`; the earlier laptop build is preserved.

QEMU 10.2.4 was compiled from the pinned archive with a separate MSYS2/UCRT64
toolchain under `.private/`. The existing system MSYS2 was not updated. A private
CPython 3.12.14 core and the local virtual environment keep the prepared app
independent of the Codex runtime cache. Firmware, binaries, guest diagnostics,
screenshots and Graphify output remain ignored. No camera/card writes occurred.

Current native validation: 16 firmware tests with no skips; all four payloads
match the accepted emulator baseline; 13 candidate admission/corruption checks;
5 launcher tests; 11 Python RAW/input tests; 270 renderer and 398 ISP contracts;
firmware-free QMP/TCP realization; 21 general UI checks; 17 sound-menu checks
each for full and sound-only. ASan/UBSan were not run on this Windows host.
See [the sanitized native results](evidence/20261021-windows-validation.json).

Cold assisted boot took about 140 seconds. The old fixed 12-second menu-return
verification window expired on this host despite subsequent scene recovery.
The verifier now records per-cycle timing with a configurable bounded deadline;
the three successful returns took 16.890, 16.985 and 18.453 seconds, each with
zero scene-region pixel RMS difference, continued ISP batches and the same guest
session. Native Windows stdio corrupted batched QMP smoke requests; the smoke
check now uses sequential commands over localhost TCP, matching the controller.

Fresh setup/rebuild commands are in [WINDOWS_BUILD.md](WINDOWS_BUILD.md).
`Setup-Z7.ps1` builds privately and runs native host/candidate checks;
`tools/check_windows.ps1` repeats firmware-free host checks. Linux setup now
also adds the vendored patcher to the new venv's import path, which is required
for candidate validation outside the firmware builder. WSL command construction
was unit-tested; an actual Linux/WSL run was not repeated on this laptop.

No complete modified Nikon container, complete camera updater acceptance,
recovery route or actual WAV playback was validated by the emulator work.

## Hardware preparation continuation — October 21, 2026

The owner authorized an experimental flash attempt and confirmed original Z7,
C 3.80, **no paid RAW-video upgrade**. Read [FLASH_ASSESSMENT.md](FLASH_ASSESSMENT.md)
before continuing. A separate native EG path was found in the Z7 stock code;
a complete outer container is not the only route worth investigating. Twelve
bounded native header/filename checks and all stock container/module CRC checks
passed. The private bundle `.private/flash-review/20261021-01/` contains the
reproducibly rebuilt full candidate as `candidate/EG161080.BIN` and separate
untouched stock inputs. This is an offline review, not hardware acceptance.

The candidate retains its CRC and entire appended tail. The native filename
pattern is `EG1610??.BIN`; the longer literal filename used in upstream build
examples does not match the tested loop (FAT aliases are untested). The storage
descriptor accommodates the candidate, but the complete updater and flash writer
remain untested. Same-version acceptance is unresolved. No verified emergency
recovery is available; stock files are not a full flash/calibration backup.

The owner then identified E:. It was verified as a removable, writable Sony
QD-G240F XQD/exFAT card, with no root user/firmware files. At 10:47 UTC the
candidate was copied as `E:\EG161080.BIN` and its complete SHA-256 read back as
`9e98eae9b726d1ced0e9cef60c89b6ef25eff369430673e753b5c3054be4f6b4`.
No formatting/deletion or camera flashing occurred. The private bundle's
`card-staging.json` records the copy. Battery charge and the real firmware screen
are still unconfirmed. Eject normally and stop at the camera's firmware version
screen, before selecting Update or Yes, for the proposed recognition check.

The owner subsequently reported the actual camera page shows **C 3.80** with
**Done, Update, Delete firmware files**. This is a user-reported recognition
observation; update execution, same-version installation and post-boot behavior
are still untested. Next inspect the separate confirmation dialog after choosing
Update, before choosing Yes, and confirm a fully charged battery.

The owner then reported the separate warning/confirmation dialog: **Update?
Current A3.80 → New A3.80**, Yes/No. This confirms the same-version choice is
offered, not that programming or post-boot operation succeeded. No Yes selection
or completed flash has been reported. The battery prerequisite remains necessary.

## Current state

The local firmware build and assisted QEMU run work. We corrected the sound
port's live-view failure and custom-menu crashes. Build `20261020-09` is the
accepted emulator baseline. All source and local fixes are included in the two
component directories as regular files; cloning this repository needs no submodule
initialization. Upstream origins/commits are recorded in `UPSTREAMS.json`.

The owner's physical camera is an original **Z7, C 3.80**, without the paid
RAW-video upgrade (confirmed October 21). The first same-version full-EG flash
and visible sound-menu entry are now owner-reported successful; see the latest
hardware result above. Audio, capture and recovery still need physical tests.

## Verified results

| Gate | Result |
| --- | --- |
| Upstream patcher tests with real private input | 16 pass, none skipped |
| Repeated builds and module CRC | All four presets pass |
| Histogram/level gate executions | 1,024 pass per applicable preset |
| Config hook calling convention | 3 cases pass per sound preset |
| Route fallback versus native instructions | 6 cases pass per sound preset |
| Data fallback versus native instructions | 4 cases pass per sound preset |
| Menu layout/callback/native hierarchy contracts | 20 checks pass per sound preset |
| Candidate admission and corruption rejection | 13 checks pass |
| Full image general UI, pause/resume, three MENU roundtrips | 21 checks pass |
| Full and sound-only submenus, independently | 17 checks each, 30 native key events each |
| Earlier QEMU synthetic tests | 11 Python, 270 renderer, 398 ISP checks; ASan/UBSan clean |

The submenu checks include the actual active page and RAM state, visible titles,
OFF, ON without a WAV, failed file selection, Preview/Reload without a file,
back/reopen with native selection retention, and return to the reference processed
live-view scene with continued ISP batches. Real WAV loading/playback is untested.
Read `SOUND_MENU_FIX.md` for the exact bug mechanisms and `LAB_REPORT.md` for history.

## Fresh laptop setup

Use Python 3.12+ in Linux or an explicitly selected WSL distribution. The desktop
used **Ubuntu**, not the unrelated `ubuntu-noble` coursework distro. Do not reset
or replace an existing distro. The upstream component docs mention older paths and
`ubuntu-noble-nikon`; the root instructions below govern this workspace.

1. Clone this repository and open a Linux/WSL shell in the checkout.
2. Install the OS dependencies and run setup:

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 tools/setup_lab.py --jobs 4
```

The helper creates `~/.local/share/wonderlantern-z7/venv`, installs the tested
dependencies, builds checked QEMU 10.2.4 and generates synthetic CMOS inputs.
The QEMU archive hash is checked by `z7-qemu/tools/build.py`. Allow several GB;
use `--jobs 2` on a smaller laptop. Generated build files live on the Linux
filesystem. The local interpreter/distro configuration is stored in ignored
`.private/lab-environment.json`; no desktop username is required.

3. Obtain your own official input from
   <https://downloadcenter.nikonimglib.com/en/download/fw/558.html> and place it at
   `.private/stock/Z_7_0380.bin`.

| Input | Size | SHA-256 |
| --- | --- | --- |
| Original container `Z_7_0380.bin` | 34,472,614 | `07cf19513ada5b770caec4cfc3531a6734c48aede28dcec037f0f8374ef441a2` |
| Extracted stock MAIN | 33,052,088 | `e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff` |

The patcher validates the original container and extracted module automatically.
Keep original firmware and all generated candidates private.

4. Build and validate locally:

```sh
LAB_PY="$HOME/.local/share/wonderlantern-z7/venv/bin/python"
"$LAB_PY" tools/build_firmware.py --output .private/builds/20261020-09
"$LAB_PY" tools/check_candidate_inputs.py --build .private/builds/20261020-09
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --output .private/evidence/laptop-full-menu-01 --exercise
"$LAB_PY" tools/probe_sound_menu.py --build .private/builds/20261020-09 \
  --preset shutter-sound --output .private/evidence/laptop-sound-menu-01 --exercise
```

Output directories must be new. After the first build use a new suffix and pass
that directory to the launcher. Expected MAIN outputs for unchanged firmware source:

| Preset | Size | SHA-256 |
| --- | --- | --- |
| full | 33,064,940 | `1d456c84709650e90cc6decd0877a9a51d4692bacc5477fa21ea28fba67cfb76` |
| shutter-sound | 33,064,840 | `0fe02a264926fe215484fd233b994d26fbdf9e6e4b2358df30027b8d82a93c0d` |
| liveview-dual | 33,052,156 | `b15532154d9bff9aea4649b8977f2c9ed737aba4256a7cc5e40880024761b9ff` |
| m900 | 33,052,120 | `806c026b3c1aed197326ad8cc7e78692016b488d863264b6ce3a7f24d28038db` |

5. Start the browser demo:

```sh
"$LAB_PY" tools/launch_z7.py
# Another local terminal, while the server runs:
"$LAB_PY" z7-qemu/tools/verify_ui.py --menu \
  --output .private/evidence/laptop-general-ui-01
```

On Windows use `Run-Z7.ps1 -WslDistro Ubuntu` after completing Linux setup/build.
`--linux-python` and `--wsl-distro` on `tools/launch_z7.py` support custom setups.
Open <http://127.0.0.1:8787/>. MENU/arrows/OK/DISP are native guest inputs. From
fresh shooting: MENU, left twice, down four times, right, up, OK opens Shutter sound.
Stop an existing owned server before reusing its port. The browser Stop control
stops the guest but leaves the HTTP server available for inspection.

## Next investigation

1. Continue the dedicated EG updater investigation from `FLASH_ASSESSMENT.md`.
   Stock container/module layout and CRCs are mapped; the complete outer digest
   remains unsolved for Z7. Our `.main.bin` is a QEMU payload; `.eg.bin` is an EG
   module. Neither is a validated camera update container.
2. Establish complete updater version/compatibility checks. The owner's camera
   already has 3.80; Nikon's official page lists 1.00–3.70 as the supported starting
   versions. Modified same-version acceptance is unknown. No paid RAW upgrade.
3. Find a concrete, model-specific boot recovery/rollback route and what still works
   after a bad boot. Reinstalling stock requires a functioning installation path;
   do not assume a saved stock file alone provides recovery.
4. Investigate actual WAV/card/audio and capture behavior. Current tests only prove
   missing-file handling and selected assisted-emulator paths. No verified real
   sensor, AF, shutter timing, recording or update acceptance follows from them.

Preserve all original inputs and earlier candidates. Card staging is complete;
the reviewed camera recognition step is next. This handoff does not authorize posting firmware, private dumps or
screenshots to the public repository.

## Source orientation and troubleshooting

- Sound fixes: `z7-firmware-extensions/src/z30_extensions/features/` files
  `shutter_sound_z7.py`, `sound_layout_z7.py`, `sound_ui_z7.py`.
- Root `tools/verify_sound_*.py`: native instruction/layout regressions.
- `tools/probe_sound_menu.py`: owns an isolated guest and captures abort context.
- `z7-qemu/tools/firmware_input.py`: re-creates the candidate from private stock
  and compares every payload byte before launch/restart.
- `z7-qemu/tools/interactive.py`: native-key browser controller and assistance.
- `z7-qemu/qemu/nikon-z7-lab.c`: emulated peripherals and diagnostics.
- Use Graphify when available: `graphify .`, then `graphify query "question"`.
  Generated graphs are excluded and can be recreated from this source.

Do not trim appended patch code back to the stock MAIN length. Only the final two
EG CRC bytes are omitted for QEMU. Keep calibration/startup assistance explicit;
do not conceal unknown device accesses by supplying invented completion values.
Capture the abort reporter at Thumb `0x100545EC`; R0 identifies exception kind,
R1 points to saved context. Copied exception strings on its stack are insufficient
to identify the fault. See the probe for checked offsets.

Some desktop command-runner contexts could not start WSL/network worker threads;
the existing Ubuntu environment worked through the desktop process runtime. That
was a host tool issue, not a reason to reset the distro. A normal laptop shell
should use the ordinary commands above. Do not copy desktop `.local` manifests:
they contain absolute host paths and QEMU fingerprints; regenerate them.

## Included and excluded

All component source, local fixes, root helpers, license notices, reports and a
sanitized validation summary are included. Original Nikon input, generated firmware,
QEMU executable/source downloads, RAM/disassembly traces, camera UI PNGs, local
tokens, virtual environments and runtime logs remain only on the desktop. Rebuild
them from your own input. The public source is sufficient to reconstruct the lab;
it is not a backup of the ignored private artifacts.
