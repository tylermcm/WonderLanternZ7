# Laptop handoff — October 20, 2026

## LCD battery preference save/restore owner PASS - November 22, 2026

Owner: "yep its owkring even after turning off and keeping it off for several minjtes"
in response to battery-only enable/Saved/normal shutdown/restart instructions.
Record battery preference retained across normal shutdown and several minutes
powered off on exact88b53ce46ae816b634c249cfe011f05a501f2619447d9c156e2828c2cf82a71e.
Saved title not separately described; journal bytes/CRC/generation not inspected.
No claim for other preference restoration, abrupt power-loss durability or all
filesystem behavior. Startup-only pass already recorded. Public evidence:
evidence/20261122-lcd-battery-persistence-hardware-result.json; private staging
updated. No card access/write or firmware flash by agent this turn.
Next: owner camera OFF and card to reader for read-only private journal backup/
decode/CRC/generation inspection before another preference or second-slot test.
Keep current active module and all files intact; do not stage or toggle anything
as part of journal inspection. Grid shape remains RAM-only.

## LCD persistence startup-only owner PASS - November 22, 2026

Owner reports "nothing noteworthy to report, it worked like it should" for the
requested startup/Defaults/MENU/touch/response/normal-poweroff sequence on88b53ce4.
This is an overall startup-only pass, not a journal write or restart-restore pass.
Public evidence: evidence/20261122-lcd-persistence-startup-hardware-result.json;
private staging record updated with scoped pass. Card/firmware unchanged this turn.
Next single preference test on same module: enable only Battery percentage, wait
for Saved (reopen page if necessary), then normal poweroff/cold-start and check
Battery stays ON with normal controls. If no Saved or any stall/error, stop/report
without repeated toggles or further tests. Do not run Update. After result, inspect
new card journal privately before selecting another write test. No new staging.

## LCD persistence startup-only trial staged and safely ejected - November 22, 2026

Owner returned and connected card in response to startup-only staging instructions.
Same Sony card identity and active working8ec66cea verified. Both settings journals
ABSENT, preservation name unused; all frozen report/source/tool hashes verified.
Staged exact21296-byte88b53ce46ae816b634c249cfe011f05a501f2619447d9c156e2828c2cf82a71e
as Z7APP.BIN. Working8ec module retained as Z7APP.LCD-GRID-BOOL-WORKING.disabled.
All245 prior files preserved through intended rename; private backups, payload/
seed bytes, metadata/catalog, flush and full readback checks pass. Updaters stay
disabled. Safe eject independently verified. No firmware flash. HW result pending.
Private staging .private/card-staging/20261122-lcd-persistence-startup-test-01/staging.json;
backup .private/card-backups/20261122-before-lcd-persistence-startup-test-01.
Next owner gate ONLY: camera OFF insert card, normal start NO Update, open Display
settings and expect Defaults. No preference edits. Check MENU/touch/responsiveness
and normal power-off; report before any battery-setting write/restart test.
If failure, preserve/disable candidate and all resulting files before restoring
working8ec. Exact-candidate recovery and physical durability not established.

Historical entries through November 21 are preserved in
[HANDOFF_HISTORY_THROUGH_20261121.md](HANDOFF_HISTORY_THROUGH_20261121.md).
The newest status below supersedes historical pending states.

## AFK LCD preference save/restore candidate complete - November 22, 2026

Owner authorized further building while AFK. Card and firmware untouched.
New wrapper z7-native-modules/plugins/lcd_persistence_checkpoint.c combines
existing LCD preference persistence with tested RAM-grid/native-bool policy.
V1 journal and preference model unchanged. DISP grid visibility is saved;
grid shape intentionally remains RAM-only, not silently added to the v1 journal.
Older generic persistent LCD profile remains unapproved; use this reviewed wrapper.

Exact candidate 21296 bytes SHA256
88b53ce46ae816b634c249cfe011f05a501f2619447d9c156e2828c2cf82a71e.
Build .private/builds/20261122-lcd-persistence-bool-01; immutable review package
.private/review/20261122-lcd-persistence-bool-01 with candidate, assessment,
six passing reports and size/hash/source/tool manifest. Root review:
LCD_PERSISTENCE_CHECKPOINT_REVIEW.md. No staging or hardware test authorized yet.
Requires the existing owner-tested task-worker host; no new firmware update.
Current owner-working card baseline remains 8ec66cea... (18060 bytes).

Checks: reproducible exact build; 48 LCD menu/DISP/save/restart; 262 grid/storage
assertions with450 geometry comparisons and native setter args0/1 only; 69 fault/
restart checks;15 native menu-status checks; actual odd-store writer preemption
with4 bounded separate-stack worker reads then completed save;83 ELF functions
zero exclusive instructions/19DMB;101 root tests. Working volatile LCD rebuilt
byte-identical8ec66cea. Public evidence uses20261122-lcd-persistence-bool prefixes.
Graphify refreshed4370nodes/12096edges; known conditional-C extraction gaps.

On return review exact candidate. First staging gate REQUIRES BOTH Z7CFG0.DAT
and Z7CFG1.DAT absent, so initial boot cannot normalize a legacy journal. If
present, preserve/back up and stop until contents/scope reviewed. Preserve active
baseline as unused Z7APP.LCD-GRID-BOOL-WORKING.disabled, all prior files/seed/
updaters intact, exclusive create/flush/full readback/metadata/catalog/eject.
Initial owner gate: normal boot NO Update, Display: Defaults, no preference edits,
MENU/touch/response/normal poweroff. Await result before one battery preference
write/Saved/restart gate, then privately inspect new journals. Review details
physical write/shutdown/menu lifecycle and recovery limitations. Grid-shape
persistence and remaining feature/capture validation are still unfinished.

## LCD native-bool grid revision owner pass - November 22, 2026

Owner: "nothing noteworthy to report, it worked like it should" in response to
the requested rear-LCD 3x3/Center cross/6x6/Off/reenable, responsiveness and normal
power-off sequence. Record overall owner pass for exact 18060-byte module
8ec66cea22ebf33755944591351d7d7f4c728e361af2b2bd7794323a72ef52ea.
No per-selection descriptions or captured pixels; no EVF, capture-lifecycle or
settings-persistence validation implied. Evidence: evidence/20261122-lcd-grid-bool-hardware-result.json;
private staging record updated. No card access/write or firmware update this turn.
This is the current working LCD baseline; preserve it on any next staging.
Next unfinished smaller-release work: resolve full-profile grid persistence
contract, then prepare a separately reviewed incremental settings save/restore
checkpoint. Existing persistent candidate remains unapproved; do not stage it
unchanged or treat volatile layout behavior as completed persistence.

## LCD native-bool grid revision staged and safely ejected - November 22, 2026

Owner explicitly approved staging with yes. Active Z7APP.BIN is 18060 bytes,
SHA256 8ec66cea22ebf33755944591351d7d7f4c728e361af2b2bd7794323a72ef52ea.
Working 9b076c6d module retained as Z7APP.LCD-VOLATILE-WORKING.disabled.
All 244 existing files preserved through intended rename; prior payload/seed
bytes, file metadata and catalog checks pass. Private backup and complete
flushed readback verified; safe eject independently verified. Updaters remain
disabled. No firmware flash. New candidate hardware result PENDING.
Private staging: .private/card-staging/20261122-lcd-grid-bool-test-01/staging.json.
Backup: .private/card-backups/20261122-before-lcd-grid-bool-test-01.

Next owner test: normal boot, NO Update. On rear LCD choose 3x3, Center cross,
6x6 and Off individually, checking displayed grid and selection, then reenable
a layout. Check controls and normal power-off. Settings/layout are volatile;
Custom pages and battery begin OFF. Native flag1 starts3x3 at each boot; legacy
2..5 is read without startup rewrite until next explicit choice. Stop/report
any stall rather than repeating. No new persistence or EVF test authorized.

## Live LCD menu/toggles pass; native-bool grid revision prepared - November 22, 2026

Owner reports navigating all settings, turning some on, normal speed/controls/
power-off and no observed detriments on9b076c6d... . Clarification: does not
remember names, enabled the two OFF settings and flipped through everything.
Likely Custom pages+battery from defaults, INFERRED, not individually confirmed.
Actual grid-layout selection unknown; do not claim every feature/pixel tested.
Private LCD staging and evidence/20261122-lcd-volatile-hardware-result.json updated.
No card write/quarantine/new staging this turn; current working9b remains active.

Source review confirmed generic full LCD set_grid sends IDs1..5 to native0x102d.
Old packet dense argument5 observed in instruction fixture; no physical failure
or flash write demonstrated. Volatile wrapper now opts into existing RAM-only
layout policy plus optional legacy2..5 read compatibility. At startup no rewrite;
next explicit layout writes native0/1 only, layout retained in RAM. Native flag1
starts3x3 each boot, legacy2..5 renders/marks its old layout until user selection.
EVF/movie geometry native; all A/B/progress/RO default code unchanged by macro.

New module18060bytes SHA8ec66cea22ebf33755944591351d7d7f4c728e361af2b2bd7794323a72ef52ea
built reproducibly, private .private/builds and .private/review/20261122-lcd-volatile-grid-bool-01.
Review LCD_GRID_BOOL_REVIEW.md.262 grid/storage checks,450 geometry calls,
44 menu/DISP checks,68 function exclusive-free scan,101 root tests pass. Legacy
read/no-init-write, next-choicebool, 7rows/selection and EVF/movie fallback covered.
Source-safe evidence matching grid-bool prefixes; tools/audit_z7_lcd_grid_storage.py.

Working A/B rebuilt .private/builds/20261122-lcd-grid-bool-baseline-pair-01 exact
412dffaf/767ada05; progress and RO rebuilt with refreshed source hashes under
20261122-worker-progress-checkpoint-02 and20261122-grid-restore-no-rmw-02, exact
3b5aced1/839d8aae respectively. Frozen older reviews keep historical source hashes;
use refreshed metadata if rebuilding, do not rewrite immutable old evidence.
No firmware update/host source change. Remaining persistent full LCD3e885483...
profile does NOT yet have this new grid policy; do not activate before its grid
storage contract/review is resolved. No settings-write test approved.

Ask explicit approval for new grid-bool module before staging. Preserve current
9b as unused Z7APP.LCD-VOLATILE-WORKING.disabled, backup/verify every existing file,
seed and config as usual, exclusive create/readback/eject. Initial next HW goal:
3x3, Center,6x6,Off selections and rear-LCD result with controls/power-off; no
new firmware. Current profile remains owner-working; don't reclassify it failed.

## Storage-free LCD approved/staged/ejected; INITIAL MENU ONLY - November 22, 2026

Owner approved yes, then "plugged in, load it" after missing card. Same Sony card
verified. Working RO839d8aae... preserved as Z7APP.RESTORE-RO-WORKING.disabled;
only active Z7APP.BIN17868bytes
9b076c6db032d6b17884aadda8ec75934be9b9456655e2ef30010870d51c8592.
All243 prior size/mtime/catalog preserved except intended rename; all named
payloads/seed/settings preserved, updaters disabled. New private backups/flush/
full readback pass; safe eject VERIFIED. No firmware update, no worker/file I/O
in this module. Hardware LCD result pending. Battery and custom pages startOFF.

Private .private/card-staging/20261122-lcd-volatile-test-01/staging.json;
backup .private/card-backups/20261122-before-lcd-volatile-test-01. Frozen review
.private/review/20261122-lcd-volatile-01 and LCD_VOLATILE_REVIEW.md. Owner first
check: normal start NO Update, responsive MENU/touch/power-off, Framing grid
display > Display settings row and compact menu presence; leave toggles/actual
grid selections untouched. No automatic full feature or persistence test.

Before later ACTUAL GRID CHOICE testing, review generic grids_histogram set_grid
in this full LCD profile: unlike small battery-grid checkpoints it currently
lacks Z7_GRID_VOLATILE_CHECKPOINT and passes layout1..5 to native On/Off setter.
Initial menu-only observation makes no such selection. Verify native encoding/
geometry policy and avoid extended native writes before authorizing grid choices.
This concern is separate from fixed worker-exclusive freeze; do not claim a new
physical failure or modify/reflash working host. Source stayed unchanged this
staging turn. Preserve every file and current baseline on any failure.

## Volatile LCD staging approved; card unavailable - November 22, 2026

Owner explicitly approved storage-free LCD test (yes). Authorization persists;
do not ask again on card connection. Windows inventory: E absent, D reader0bytes,
no other external media. No card writes. Working RO remains last active payload.
Prepared .private/stage-lcd-volatile-test-01.py for subsequent verified staging,
NOT run. Reidentify same Sony card once connected. Source frozen review
.private/review/20261122-lcd-volatile-01, module9b076c6d...17868bytes, no worker/I-O.
Preserve activeRO839d8aae as unused Z7APP.RESTORE-RO-WORKING.disabled; retain all
other files/seed/updaters. Initial owner test normalboot/controls and Display
settings menu presence ONLY, no feature toggles yet. Battery/custompages start
OFF intentionally. No Update; settings reset each boot. After staged verification
safely eject and record actual result; never claim staged while card missing.

## Hardened read-only restore hardware PASS; volatile LCD approval pending - November 22, 2026

Owner confirms6x6 [SD] marker, normal responsiveness and normal power-off. Exact
RO839d8aae... now scoped HW pass: worker read/validated seed and GUI applied it.
No file save/journal write or broader cache/lifecycle proof. Current working
active module isRO; progress/B backups remain intact. No card writes this turn.
Private RO staging and evidence/20261122-grid-restore-no-rmw-hardware-result.json
updated. Hardware gates now host, A/B, direct progress, read-only seed all pass.

Next prepared test is storage-free LCD .private/review/20261122-lcd-volatile-01;
all files/source hashes reverified. Module17868bytes SHA9b076c6db032d6b17884aadda8ec75934be9b9456655e2ef30010870d51c8592.
44 scope tests/68 exclusive-free functions software only. No worker/settings file
I/O or native persistent menu-dispatch replacement. Four compact DISP presets,
grid/horizon/info/battery/focal controls, volatile per boot. Custom pages AND
battery startOFF, expected entry Framing grid display > Display settings. Read
LCD_VOLATILE_REVIEW.md. First approved hardware result should normalboot/controls
and menu presence only; enable features one at a time after observing initial
state. No Update. Preserve current RO as unused Z7APP.RESTORE-RO-WORKING.disabled;
old failed Z7APP.RESTORE-RO.disabled0714... stays untouched. Ask approval before
staging. Full persistent LCD/settings writes still unapproved; no automatic jump.

## Hardened read-only restore approved/staged/ejected - November 22, 2026

Owner explicitly approved next RO module (yes) after progress full hardware pass.
Same Sony card identity/current named bytes verified; working progress3b5aced1...
preserved as Z7APP.PROGRESS-WORKING.disabled. Only new active Z7APP.BIN6564bytes
839d8aaef7f404ba64f710d092aceba628552b969e54820867bd6b6d4c363b40.
Existing Z7GRID.DAT80 bytes SHAa0b38b760a81b292131af5944fa3ade0ce48bc9e21e9a424b712dc2368567ae0
matches frozen6x6 seed and was NOT changed. All242 preexisting size/mtime/catalog
unchanged except intended module rename; all named contents preserved, updaters
remain disabled. Private backups/flush/full readback pass. Safe eject VERIFIED.
No firmware update, no camera-side settings writes; no hardware RO result yet.

Private stage .private/card-staging/20261122-grid-restore-no-rmw-test-01/staging.json;
backup .private/card-backups/20261122-before-grid-restore-no-rmw-test-01. Frozen
review .private/review/20261122-grid-restore-no-rmw-01. Exact source hashes checked.
Next owner: normal coldstart NO Update, let liveview/battery appear, open grid
menu before changing a choice; report6x6 [SD] marker or exact Off [SD miss/error]
label and controls/power-off. If no marker yet, leave briefly/reopen without
selecting another grid. Native On/Off visibility stays as it was. If stalls stop
and report trigger; no repeat/reflash. Old0714... restore remains disabled.
No automatic volatile/full LCD/settings-write trial authorized after this result.

## Worker progress checkpoint fully owner PASS; RO approval pending - November 22, 2026

After counter4->6, owner "yeah everthtbing works like it should" confirms ordinary
controls/power-off. Progress module3b5aced1... now complete scoped hardware pass,
physical worker execution via counter and GUI observation confirmed. No measured
cadence or blanket native I/O/lifecycle proof. Progress remains current working
active module; B backup preserved. No card operations this result-recording turn.

Prepared next RO revision2 review .private/review/20261122-grid-restore-no-rmw-01
reverified all files/current source fingerprints. Module6564bytes
839d8aaef7f404ba64f710d092aceba628552b969e54820867bd6b6d4c363b40;
seed80bytes a0b38b... is6x6 and already preserved on card. No camera writes;
GUI-owned monotonic selection latch replaces old RMW. Requires newly working
host and progress gate now passed. Read RESTORE_NO_RMW_REVIEW.md. Ask approval
before staging; preserve progress as unused Z7APP.PROGRESS-WORKING.disabled,
inspect/back up actual seed and never overwrite unexpected contents. All other
files/updaters intact/disabled. No new host update or automatic full LCD trial.
Next result: normal boot/controls and grid menu6x6 [SD] marker, normal power-off.
Old failed0714... restore remains disabled; never re-enable it.

## Visible worker callback progress CONFIRMED; power-off pending - November 22, 2026

Owner reports Off W0004, then W0006 after leaving/reopening menu. Progress module
3b5aced1... worker is sole counter writer; menu only samples. This directly
confirms physical callback execution and GUI publication in this observed context.
No measured elapsed time/cadence; do not infer native delay units. Owner has not
separately confirmed general controls or normal power-off in this progress test.
Record status partial completion, not failure or full lifecycle clearance.

Private .private/card-staging/20261122-worker-progress-test-01/staging.json updated;
source-safe evidence/20261122-worker-progress-hardware-result.json. No card writes
or new staging in this result-recording turn. Active progress module remains;
working B preserved Z7APP.POST-HOST-B.disabled. No firmware update needed.
Next ask normal power-off/controls confirmation, then separately choose/review
one next checkpoint (read-only restore or storage-free LCD menu) and approve
staging. Do not auto-activate full persistent LCD or repeat retired probes.

## Worker-progress module approved/staged/ejected - November 22, 2026

Owner returned, asked ready for test/flash, then explicitly approved progress
module (go ahead). No firmware update. Same Sony card verified. Current working
B767ada05... preserved as Z7APP.POST-HOST-B.disabled; every previous payload and
updater left intact/disabled. Only new active Z7APP.BIN5452bytes
3b5aced1e58f56ebad9d5f945452254d82614549e6904acb5ff3d460909e51a9.
Frozen review/files/source hashes verified, new private backups/flush/full
readback pass. All241 prior size/mtime/catalog unchanged except intended rename,
all named contents preserved. Safe eject VERIFIED. No hardware result yet.

Private stage .private/card-staging/20261122-worker-progress-test-01/staging.json;
backup .private/card-backups/20261122-before-worker-progress-test-01. Review
WORKER_PROGRESS_REVIEW.md and frozen .private/review/20261122-worker-progress-checkpoint-01.
Owner test: normal coldstart NO Update, open grid-choice menu, note Off [W nnnn]
WITHOUT selecting it, leave menu/brief ordinary use, reopen and report two values
and controls/power-off. Counter changes only in worker, menu reads never increment.
No exact callback cadence claimed. If stalls stop/report, no repeat. Saturation
9999/unchanged number needs report, not assumption. Other AFK candidates remain
unstaged/unapproved; do not auto-stage restore or LCD after this test.

## AFK offline build checkpoint complete; working card UNCHANGED - November 22, 2026

Owner "just keep building im going afk" authorizes continued engineering. Agent
committed to offline work, NO camera/card writes or new staging/firmware update.
No pending question while AFK. Read AFK_BUILD_CHECKPOINT.md first for this sprint.
Installed owner-tested host/B remain hardware checkpoint: EGf479950e... /
MAIN24b20745... plus active B767ada05... . Host source hashes still match installed
candidate build; A/B rebuilt byte-identically after tooling changes. No new
hardware success/callback count claimed. All existing card files untouched.

New private builds/reviews (all staged/hardware authorization flags FALSE):
1) Worker progress,5452bytes SHA3b5aced1e58f56ebad9d5f945452254d82614549e6904acb5ff3d460909e51a9,
 .private/builds and .private/review/20261122-worker-progress-checkpoint-01.
 Off row shows W0000..9999 on menu entry. One worker writer, GUI samples atomic
 word; no file I/O, native UI calls or text writes from worker, no exclusive ops.
 Counter saturates9999, resets each boot. NEXT proposed HW gate: two increasing
 menu observations, no selections required; review WORKER_PROGRESS_REVIEW.md.
2) Read-only restore revision2,6564bytes SHA839d8aaef7f404ba64f710d092aceba628552b969e54820867bd6b6d4c363b40,
 .private/builds and .private/review/20261122-grid-restore-no-rmw-01.
 GUI-owned monotonic user-selected latch replaces fetch-add; worker never writes
 latch, menu refuses to override owned user choice. Reads existing Z7GRID.DAT
 only, no writes; no native card-ready proof. RESTORE_NO_RMW_REVIEW.md. Old failed
 0714... restore stays disabled; do not reuse it. Hardware gate AFTER progress.
3) Storage-free LCD,17868bytes SHA9b076c6db032d6b17884aadda8ec75934be9b9456655e2ef30010870d51c8592,
 .private/builds and .private/review/20261122-lcd-volatile-01. Existing four DISP
 presets/compact menu/grid/horizon/info/battery/focal without worker/file adapter.
 Defaults master+battery OFF, expected Framing grid display > Display settings.
 Settings reset each boot; old journals ignored/preserved. LCD_VOLATILE_REVIEW.md.
 This separates UI/overlay tests from storage; no physical UI/capture clearance.

Persistence policy revised offline: one GUI writer/loader-before-publication;
replace odd/even revision fetch-add with load/store+fence and final release.
Bounded snapshot reader returns after at most3 attempts. Not multiwriter mutex.
PERSISTENCE_PUBLICATION_REVIEW.md. Current refreshed source builds:
 .private/builds/20261122-persistence-no-rmw-02,24048bytes SHAb4f4be274e4249587bacf5a252b9508e7ed7ff0ab30123275325c29db903161d;
 .private/builds/20261122-lcd-no-rmw-02,21104bytes SHA3e8854834417bb29e0b4ea9ea3c5a7be5b37fcb941826e1099adc43be3f5d954.
 Both byte-identical to tested -01 after optional volatile-mode source branches.
 No save-capable/full LCD activation approved. Deferred highlight/cache/portrait/
 advanced-host RMW sites inventoried but not mechanically rewritten.

Validation:101 root tests; progress+RO270 grid checks/450 geometry calls EACH;
RO52 codec/fault/preemption checks incl actual paused read + GUI user choice;
progress format/carry/saturation/reset/GUI-read-only/no-I-O checks. Full persistence
84 checks; targeted actual odd-store writer preemption with4 bounded reader
calls/no I/O on separate stack, writer resume/ABI and complete revision save.
Persistent LCD48 checks; volatile LCD44. Exact function scans:28/34/91/83/68
functions respectively, zero exclusive instructions found; native callees outside
scan. Python compile/diff pass, graph4338nodes/11997edges (conditional-C gaps).
Optional build_z7_module function_details export preserves default packet/report;
2 meaningful ELF bounds tests added. New builders/audits under tools/.

Source-safe consolidated evidence/20261122-afk-build-checkpoint.json and related
prefix reports. Private audit originals remain under .private/evidence; frozen
reviews include exact module/metadata/assessment/audit hashes, no firmware images.
The no-storage audit was adjusted to distinguish loader cache maintenance from
settings file I/O and require NO worker, preserving persistent-profile contracts.
No live build/audit process remains after final completion. Root memories not edited.

## B owner PASS: targeted worker-freeze hardware checkpoint - November 22, 2026

Owner "works perfectly, no issues" confirms B general normal coldstart/controls/
battery/grids/brief-use/power-off prompt pass. Same exact B767ada05... packet
froze old host and now works after revised host update. New-host A and B both
owner-pass. This validates targeted registered-empty-worker responsiveness on
camera; no direct callback-entry counter, physical exception PC or installed
image readback. Do not claim every worker body/module atomic/persistence safe.
No file I/O/restore attempted by this B. Full feature release remains incomplete.

Working checkpoint: host EGf479950e... / MAIN24b20745... (owner installed exact
staged update, not readback), active SD Z7APP.BIN5324bytes
767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158.
A preserved Z7APP.POST-HOST-A.disabled, prior updater/module trials intact and
updaters disabled. Card last safely ejected for owner test; no card mutations
this result-recording turn. B staging record and source-safe evidence
 evidence/20261122-post-host-B-result.json updated. Source commit recorded later.

Next useful incremental work: observable worker progress (volatile counter/
marker) without I/O before restoring file paths; then review remaining module
atomics independently. Do not reuse LX/combined exclusive probes, reflash host
or activate failed restore module. No next hardware trial staged/approved.

## Post-update B staged/ejected; owner result pending - November 22, 2026

Owner explicitly approved B only (yes) after new-host A owner pass. Same Sony
card identity verified, all named earlier files vs pre-A backup verified/new
private backups made. Native rename ONLY active A -> Z7APP.POST-HOST-A.disabled;
exclusive add B as Z7APP.BIN5324bytes SHA767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158.
Same return-only worker packet that froze old host; no I/O/restore/new selection
atomics/GUI-seen wrapper. Source fingerprints and new-host integration evidence
verified. All240 preexisting size/mtime/catalog unchanged except intended rename,
all named contents intact, updater remains disabled. Flush/full readback pass;
safe eject VERIFIED. No firmware update or further module staged.

Private stage .private/card-staging/20261122-post-host-B-01/staging.json;
backup .private/card-backups/20261122-before-post-host-B-01. Await normal coldboot
NO Update, battery/MENU-touch/grids, about30s ordinary use and normal power-off.
If freezes stop/report, no repeat. No menu probe selection required. A result
cannot establish worker responsiveness; B pass would support fixed freeze path
with worker registered, but this bx-lr callback has no visible execution marker,
so do not claim direct physical callback-entry observation. No arbitrary atomics/
persistence/full release clearance. No further trial approved.

## Post-update A owner PASS; B approval pending - November 22, 2026

Owner "works as intended, no issures" confirms general A check pass on updated
host: normal start/battery/MENU-touch/grids/brief use/power-off prompt. No itemized
timings. A412dffaf... registers no worker; baseline+new bridges working by owner
report. Worker fix still unverified until B. Source-safe result
 evidence/20261122-post-host-A-result.json and private A staging record updated.

Exact B already frozen/rebuilt/integration-audited at
.private/review/20261122-worker-guard-host-01/controls/enabled/Z7APP.BIN,
5324bytes SHA767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158.
Same empty callback packet that froze old host; only flag/CRC differ from A.
Ask approval to stage B only, preserve active A under unused
Z7APP.POST-HOST-A.disabled. No firmware Update, restore/I-O or exclusive probe.
No card mutation/staging in this result-recording turn. Reidentify card and
verify all prior bytes/backup/readback/eject before any approved B stage.

## Post-update A staged/ejected; owner test pending - November 22, 2026

Owner explicitly approved A only (yes). Same Sony card verified, prior named
hashes/update-disabled file verified, private backups/flush/full readback pass.
Only Z7APP.BIN added,5324 bytes SHA412dffaf9a2b5f9aa5cf9e715b66e778e9de1e9f4c67eabc2963df7899a200f9.
Worker DISABLED, battery/six-grid control on new owner-confirmed host. All239
preexisting file size/mtime/catalog unchanged and named contents preserved.
EG161080.WORKER-GUARD-HOST.disabled and old updater remain disabled, no active
EG. Safe eject VERIFIED. No firmware flash or new code change this turn.

Private stage .private/card-staging/20261122-post-host-A-01/staging.json;
backup .private/card-backups/20261122-before-post-host-A-01. Await ordinary
coldstart (NO Update), battery percentage/MENU/touch/grids, about30s normal use,
normal power-off owner result. A is not worker fix proof; do not claim callback
hardware success. B767ada05 requires separate approval after A pass; do not
repeat LX/combined probe or activate restore/persistence. All files kept intact.

## Completed updater disabled; A approval pending - November 22, 2026

Same identified Sony card returned/available. Verified completed EGf479950e...,
all named previous bytes vs pre-update backups and private new backups. Native
Move-Item ONLY EG161080.BIN -> EG161080.WORKER-GUARD-HOST.disabled.239 preexisting
size/mtime/catalog unchanged except rename; all prior modules/stock/seed intact.
No active root BIN. Card LEFT MOUNTED in reader for next approved staging, NOT
claimed ejected. All handles closed, backups flushed/readback verified. No module
staged and no further flash. Private record/backups:
.private/card-backups/20261122-worker-guard-host-update-complete-01/quarantine.json.

A then B next: WORKER_POST_UPDATE_CONTROLS.md. Exact frozen controls already
validated in .private/review/20261122-worker-guard-host-01/controls. A412dffaf...
worker-disabled battery/six-grid, B767ada05... sameplusreturn-onlyworker.
Ask approval for A ONLY; record owner coldstart/battery/MENU-touch/grid/normal
power-off result before separately approved B. No more Update, restore/I-O or
exclusive-probe trials. New host basic operation owner-pass but worker fix still
unconfirmed. Installed-image hash remains inferred, not physical readback.

## Owner confirms new host update/normal operation pass - November 22, 2026

Owner: "update worked as intended. not failures freezes or otherwise" in response
to exact host-only update/no-card basic-operation check. General owner pass, no
itemized timings. New host EGf479950e.../MAIN24b20745... presumed installed from
approved exact staged file; NO physical image readback. Do not claim verified
installed hash. Worker remains UNTESTED on new host; no hardware fix established.
All SD modules were disabled during update. Next preserve/disable completed
EG161080.BIN under unique EG161080.WORKER-GUARD-HOST.disabled if card available.
Keep previous old-host EG161080.BIN.disabled and every other file intact. Record
cleanup separately. Then separately approve/review A worker-disabled battery/
six-grid, record owner result, then B exactemptyworker767ada05. No restore/I-O or
exclusive-probe repetition. Host update itself need not be repeated.

## Owner approved host-only update; EG staged/ejected - November 22, 2026

Owner "yes" explicitly approves staging/testing exact reviewed host-only update.
Same identified Sony card privately backed up/verified. Exclusively added ONLY
EG161080.BIN33058842 bytes SHA f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140.
Full readback/CRC0, all238 prior file size/mtime/catalog unchanged, all named
payloads/seed/configurations preserved. No rename/deletion, no Z7APP.BIN or other
active root BIN. All SD modules disabled. Safe eject VERIFIED. No firmware flash
executed by assistant; owner update result/actual installed image still pending.

Private stage .private/card-staging/20261122-worker-guard-host-only-01/staging.json;
backup .private/card-backups/20261122-before-worker-guard-host-only-01. Source-safe
evidence/20261122-worker-guard-host-only-staged.json. Exact assessment remains
WORKER_GUARD_HOST_ASSESSMENT.md and frozen private review20261122-worker-guard-host-01.
Before camera Update owner must confirm Setup firmware C3.80 and fully charged
battery (not yet observed/confirmed). If differs/not offered/error, stop/report;
no bypass. Normal manual approved update; do not interrupt. On completion follow
power-off instruction, remove card, ordinary no-card boot/MENU/touch/power-off
check first. No custom overlay expected; all modules disabled. After owner pass,
preserve/disable updater on laptop before separately approved A then B control
staging. No automatic next module trial; no restore or probe repetition.

Recovery limits unchanged: old host and stock copies preserved, but no proven
unbootable-host recovery. New host fix still hardware-unverified. Current known
camera state normal without card before update. No fresh code/test suite this
turn; exact review/source hashes, identity, backups, copy/readback/CRC/catalog
and eject checks performed. Do not claim update acceptance/installed new hash.

## Complete worker-fix host rebuilt; exact review awaiting approval - November 22, 2026

Owner "lets keep going...look into fixing it" authorizes continued engineering,
NOT a specific host flash. Complete base display host/bridges regenerated and
built twice; third independent rebuild in exact review also matches. New EG
33058842 bytes SHA f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140;
MAIN33058840 SHA24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce.
Host blob4573 bytes SHA5b389010... unchanged from task-owned guard audit.
All native bridges regenerated, fixing the prior overlay limitation. Private
build .private/builds/20261122-worker-task-display-host-01.

Rebuilt A/B pair .private/builds/20261122-worker-task-pair-01 is byte-identical to
camera-tested A412dffaf and B767ada05 with refreshed source fingerprints.
Complete-host checks:99 loader,55 worker,316 display incl2114 indexed reads/image;
270 grid checks/450 geometry calls per A/B;64 interleaved GUI/ticks per control,
B callback64/A0, guard released, zero module I/O. No camera fix yet verified.
Root99 tests passed prior implementation turn; not repeated for integration-only
tools. Python compile/diff checks pass; graph refreshed separately.

Read WORKER_GUARD_HOST_ASSESSMENT.md. Exact private review frozen at
.private/review/20261122-worker-guard-host-01: only host-only/EG161080.BIN for
proposed first update; A/B controls SEPARATE, previous installed EG and original
stock/container preserved as normal-menu fallback inputs.14 native header/name/
capacity probes pass, CRC0, exact hashes/full readback. No flash writer exercised.
No proven unbootable-host recovery. Card removal cannot guarantee recovery from
a faulty host itself. No installed-image readback. Exact same-version new update
acceptance remains unknown despite prior modified update acceptance.

NO card writes/staging/flash authorized or performed. Next step: owner approval
for exact host-only update, confirm normal no-card boot/C3.80/full battery,
then card preflight/private backups/preserve all disabled files; exclusively add
EG only with no active Z7APP. After approved update first no-card normal boot;
then preserve/disable updater and separately review A then B after each owner
result. No automatic worker/restore/settings trial. LX remains disabled, camera
normal without card confirmed. Source-safe evidence20261122-worker-task-full-host.json.
Tools audit_z7_worker_host_integration.py and prepare_z7_worker_guard_review.py.

## Task-owned worker guard implemented/validated OFFLINE - November 22, 2026

Owner "go ahead" authorizes offline ownership/guard engineering, NOT a flash.
Read WORKER_TASK_GUARD.md. z7_module_worker_tick now static/noinline and removed
from host header. Production C/H references exactly definition plus resident
loader-task-loop call. SDK exposes registration only and documents one-task
ownership. ELF local binding verified. Replaces weakCAS with ordinary volatile
recursion flag + compiler barriers: busy skips; 1 before callback,0 after return.
Not a cross-task mutex; arbitrary raw-address/concurrent calls outside contract.
No layout/API change, cached alias, guessed RAM/mutex or native-task addition.

Private .private/builds/20261122-worker-task-guard-01: host-code.bin4573 bytes
SHA5b389010817fe30ae681c9526c45832f71dcc40547bc2d637215c0ae74051ccd,
reproduced twice. Private146-byte dispatcher has zero LDREX/STREX/CLREX.
55 existing worker checks +4 exact guard-write/recursion cases passed; actual
resident loop with success/failure/missing and legacy API refusal included.
99 root tests pass; Python compile/diff checks passed. Graph4261nodes/11774edges;
conditional-C parser limits retained, explicit source/ELF checks used.

Only blob/symbols/evidence saved, no complete MAIN/EG/update image. Audit uses
in-memory blob overlay + new C symbols; old out-of-blob native display bridges
NOT regenerated/tested. Code addresses moved with20-byte shrink, so MUST fully
rebuild host/bridges before any installable candidate. Optional advanced profiles
not validated. No card writes/new hardware trial/flash. Installed host unchanged,
LX disabled; camera recovery normal without card confirmed. Module atomics/shared
state still need their own review; no blanket exclusive-support claim.

Source-safe evidence/20261122-worker-task-guard.json. Root build helper now accepts
optional symbol_details dict to inspect ELF function size/type/binding; normal
return tuple unchanged. Next checkpoint: complete base-host+bridge rebuild,
minimal no-I/O worker integration, then exact install/recovery review and fresh
flash authorization. Do not claim hardware fix or firmware readiness yet.

## Recovery confirmed after LX failure - November 22, 2026

Owner confirms "Yes, normal without card": battery reinserted, normal boot and
MENU/touch responding. Records updated. No-card recovery confirmed, not stock
firmware restoration or exact physical exception diagnosis. Failed LX remains
preserved/disabled, all earlier files intact, card safely ejected, no active BIN.
No further hardware trial staged. Next engineering work: review worker guard
ownership and avoid exclusive access to this host-state region; weakCAS alone
is not a demonstrated fix. Any host flash still needs exact review/authorization.

## LX reproduced freeze; preserved/disabled/ejected - November 22, 2026

Owner: immediate matching full freeze/slight dim on LX selection, battery pulled,
card returned. RD10864694 and CLe55eda50 both owner-pass; LXf8f4506f FAIL.
Exact probe image117c..118e: addresssetup, CLREX1182, LDREX1186, CLREX118a, return.
NO STREX, retry, host writes or worker registration required for this symptom.
LDREX-associated access on guard a97000cc leading trigger; cannot distinguish
LDREX from post-load CLREX cleanup without target markers. Exact physical PC,
exception, MMU and automatic recovery in THIS LX run not captured. Result label
unknown due battery pull; current no-card recovery asked asynchronously, pending.
Source-only weakCAS still performs LDREX on guard; NOT an adequate demonstrated
fix. No more store/combined probe repetitions. Read latest WORKER_GUARD_FAILURE_REVIEW.md.
Future fix investigation: avoid exclusive access to this guard; review task
ownership/recursion/native synchronization before changing concurrency contract.
No guessed cached alias/new host image/flash or further hardware trial authorized.

Same Sony card identified, backups/named contents verified, native rename only
Z7APP.BIN -> Z7APP.GUARD-LOAD.disabled.238 existing metadata/catalog unchanged
except rename; all working copies/other payloads/seed intact, no active root BIN.
Safe eject VERIFIED. Private .private/card-backups/20261122-worker-guard-load-freeze-01;
source-safe evidence/20261122-worker-guard-load-hardware-result.json.
Validation this turn: exact frozen disassembly and production caller search,
verified backup/rename/eject; no code edit or new runtime test (hardware result
supersedes emulator clearance). Earlier offline tests remain scoped evidence.

## CL passed; LDREX-only LX control staged/ejected - November 22, 2026

Owner "cl run > Cl run OK no issues" confirms CL control pass. RD and CL both
pass; do not infer exclusive load/store support yet. Result in clear staging
record and evidence/20261122-worker-guard-clear-hardware-result.json.
Next LX control executes CLREX, one LDREX on a97000cc, CLREX cleanup; NO STREX,
worker registration, host-word/code writes, file I/O or firmware change.
Manual Center only, once per boot, same ready/host/busy checks as prior controls.

Exact5664-byte module f8f4506fa30fe5379403f2a8f9ee6d919b2e4d60b31a94efeee8588ae7085a4a
staged on same identified Sony card. Confirmed working CL preserved as
Z7APP.GUARD-CLEAR-WORKING.disabled; RD and every earlier file preserved.
All237 existing metadata unchanged except intended rename, catalog/named hashes
unchanged, configuration presence backed up/verified; flush/full readback pass.
Safe eject VERIFIED, no flash. Private build/review/staging20261122-worker-guard-load-01;
backup .private/card-backups/20261122-before-worker-guard-load-01.

Next owner: normal coldstart NO Update, select Center [LX run] ONCE, reopen
without selecting again, report exact LX label/responsiveness/power-off. If
stalls wait for possible prior~12s recovery and inspect label before battery
removal if feasible. Do not repeat. No store trial staged/physical PC captured.
Read WORKER_GUARD_LOAD_REVIEW.md; evidence20261122-worker-guard-load.json.
Build reproduced twice; four controlled paths and exact HUD smoke pass; read
counts0/1, no repeats/writes/workers/I-O checked. No fresh full battery policy
suite: previous38-check CL evidence reused only after unchanged dependency hash
checks. No full geometry/root suite repeat. Python compile/diff pass, graph
refreshed separately. LX hardware outcome pending.

## RD passed; CLREX-only control staged/ejected - November 22, 2026

Owner: "reports center RD OK with no issues at all". Ordinary guard read and
manual menu path pass; no exclusive support inferred, power-off not itemized.
Result saved in read staging record and evidence/20261122-worker-guard-read-hardware-result.json.
Next control adds CLREX before proven ordinary read; no LDREX/STREX, no worker,
host-word/code writes, file I/O or firmware update. This isolates cleanup before
later pairing with exclusive load. No further exclusive load/store test staged.

Exact5664-byte CL module e55eda505bca7bca749acb52931ae614afd57e2170dd6273528cec29e7e1882f
staged on same verified card. RD preserved as Z7APP.GUARD-READ-WORKING.disabled.
All236 preexisting file metadata preserved except rename; prior payloads/seed/
configuration contents and catalog unchanged. Backups/flush/full readback passed.
Safe eject VERIFIED. Private build/review/staging20261122-worker-guard-clear-01,
backup .private/card-backups/20261122-before-worker-guard-clear-01.
Read WORKER_GUARD_CLEAR_REVIEW.md. One manual test: normal start NO Update,
select Center [CL run] ONCE, reopen menu WITHOUT selecting again, report CL label
and controls/power-off. If stalls, wait for possible prior~12s recovery and inspect
label before battery removal if possible. Do not repeat the probe.

Build reproducible twice; four controlled cases and38 battery checks pass,
manual-only/one-attempt/no host writes/no I-O checks. Python compile/diff passed;
graph refreshed. No root/full geometry repeat for unchanged shared components.
Hardware CL result pending. Source-safe evidence20261122-worker-guard-clear.json.

## Ordinary-read control staged/ejected - November 22, 2026

Owner "ok lets get to it" authorizes read control first. Exact5664-byte module
10864694f04424d479adc4b61cc99dd7e3b512e70129621595f547428f888438 staged as
Z7APP.BIN on same verified Sony card. No host firmware change or flash. All235
existing files metadata/catalog preserved, all prior payloads/seed contents and
configuration presence verified/backed up. Exclusive create/flush/full readback
passed. Safe eject VERIFIED. Private review/build/card-staging20261122-worker-guard-read-01;
backups .private/card-backups/20261122-before-worker-guard-read-01.

Same manual Center trigger and code/API signature validation, no worker. Probe
is ordinary volatile LDR only on a97000cc, no host writes and no LDREX/STREX/CLREX.
Zero guard -> Center [RD OK]; registered worker/nonzero guard -> [RD busy];
signature mismatch -> [RD host]. Initial [RD run], incomplete marker [RD begun].
Runs only once when Center selected; other choices/menu-open/boot do not probe.
Next owner: normal coldstart NO Update, open grid menu, select Center [RD run]
ONCE; reopen WITHOUT selecting again and report label/responsiveness/power-off.
If stalls, wait for previously observed ~12s recovery if it occurs and inspect
label before any battery pull; do not repeat. No further exclusive trial staged.

Build reproduced twice; four controlled cases pass, manual-only read-count0/1,
no retries/host writes/worker/I-O and label checks;38 battery policy checks pass.
Python compile/diff checks pass; graph refreshed (see private graph log). Root
suite/full geometry not repeated for shared unchanged base. Hardware pass pending.
Read WORKER_GUARD_READ_REVIEW.md; source-safe evidence20261122-worker-guard-read.json.

## Probe label unavailable; battery removed - November 22, 2026

Owner clarifies they do not remember seeing any change except camera freezing,
and battery was already removed. No EX begun/OK/fail label was observed or
confirmed. Do not infer callback completion, exception or exact failing opcode.
Volatile marker unavailable; do not repeat withdrawn combined probe for it.
Next useful diagnostic design separates exclusive load and store, with a plain
read control and explicit progress markers; no new trial staged/authorized by
this clarification. Card remains safely ejected with guard-once disabled; all
files preserved, no active root BIN. Prior ~12s recovery remains owner report.

## Stalled manual probe quarantined and ejected - November 22, 2026

Same Sony card identified. All named prior bytes compared to pre-probe backup,
new private backups verified; only Z7APP.BIN renamed to Z7APP.GUARD-ONCE.disabled.
235 existing metadata/catalog unchanged except rename, no active root BIN,
working A and all earlier files intact. Safe eject VERIFIED. Record/backups:
.private/card-backups/20261122-worker-guard-once-freeze-01/quarantine.json.
No firmware flash/new trial. Pending owner label from already recovered session;
do not ask to reboot/repeat to recover that observation. Source-safe result:
evidence/20261122-worker-guard-once-hardware-result.json. Existing emulator audit
still passes but does not reproduce the physical stall; no new code/test run
needed for recording owner result and verified quarantine.

## Manual single attempt stalls; owner reports ~12-second recovery - November 22, 2026

Owner: immediate freeze/slight screen dim on pressing Center probe. Battery pull
is an alternative, but waiting about12s closes menu/restores FULL control with
card still inserted. Do not conflate with proven permanent spin or data abort.
Exact post-recovery label pending; asked owner to reopen menu only WITHOUT
selecting again, and only if already recovered without battery removal. No
repeat diagnostic authorized. Candidate83ab23... WITHDRAWN. Reader currently has
card media; preserve/disable before future boot, record quarantine separately.

Exact compiled exclusive function image1180..119a: address setup, LDREX1186,
conditional STREX118e, CLREX1196, return119a; no back edge. Probe STARTED store
image113c precedes call1148. Result store1158 precedes ordinary native setter
branch1172 to104065b1. Therefore EX begun vs OK/fail after recovery can separate
pre-result path from subsequent native setter/menu behavior; no physical PC or
exception record yet. Current observations do not prove which exclusive op stalled.
No host flash, no further trial prepared. Keep all payloads/files intact.

## Manual one-attempt diagnostic staged/ejected - November 22, 2026

Owner "ready"; same Sony card identity and all preserved hashes verified.
Active Z7APP.BIN now5664 bytes SHA83ab23cadd63e902fb252cbb563f8b262ceac9e2e9ec332c0e0344be4ce2e99c.
Exclusively added only diagnostic, no renames/deletions or firmware flash.234
prior file metadata/catalog unchanged; all prior payloads, working A, seed and
configuration presence preserved. Private backup/readback verified:
.private/card-backups/20261122-before-worker-guard-once-01;
.private/card-staging/20261122-worker-guard-once-01/staging.json.
Safe eject verified by no-media volume check. Await owner test: normal boot, open
native grid menu; Center [EX run], select ONCE, reopen menu and report exact
EX OK/fail/busy/host label and normal power-off. Do not repeat/reboot for more
attempts before reviewing result. If freezes, distinguish boot/menu-open/selection.
No worker is registered and no exclusive runs until Center selection. Candidate
can still fault/freeze during one operation; physical PC remains unobserved.

## SD-only manual guard probe ready; waiting for card - November 22, 2026

Owner requests "lets test it out see if we can find if its one ofthose". Prepared
SD-only one-attempt probe, NO host firmware change. Review WORKER_GUARD_ONCE_REVIEW.md.
Exact5664-byte module83ab23cadd63e902fb252cbb563f8b262ceac9e2e9ec332c0e0344be4ce2e99c.
Private build/review20261122-worker-guard-once-01. User request authorizes this
bounded SD diagnostic; no firmware flash. NOT STAGED: E reader has no media.

No worker registration. Working battery/grid base plus selection/label hooks.
Runtime checks API register-worker pointer11fa66f7 and28 guard-code bytes; mismatch
shows Center [EX host] and refuses probe. Boot/paint/menu entry do not attempt it.
Owner selects Center [EX run] ONCE; registration words must be0; one LDREX on
same guard a97000cc, ifzero one STREX writing samezero, CLREX, return status.
No retries. Subsequent selections do not repeat. Reopen menu for EX OK/fail/busy.
A freeze specifically on selection narrows manual access path but not exact PC.
Execution context/value differ from host worker; EX OK does not clear worker path.
No exception handler; probe can still freeze on access fault/stall.

Build reproduced twice, five controlled paths pass (success/failure/guardbusy/
registeredworker/mismatchedhost), manual-only/one-attempt/resultlabels/guardword
preservation/no-I/O checks;38 battery checks pass. Python compile passed. Root/full
geometry suites not repeated; shared base unchanged. Graph refreshed separately.
Source-safe evidence evidence/20261122-worker-guard-once.json. No card changed.
B remains disabled, A and earlier working files intact. Camera normal without card.

## Matched freeze localized to leading pre-callback suspect - November 22, 2026

Owner confirms camera responds normally without card; asks to find exact origin.
Read WORKER_GUARD_FAILURE_REVIEW.md latest update. New exact A/B trace separates
registration from resident task progress. Successful registration stores only
callback0xa97000c4 and flag0xa97000c8; returns1, no executed exclusive/call.
Installed resident loop6032 supplies delay1000, tick, repeat. Five controlled
cases: A healthy/fault both reach4 delays; B healthy4delays/3callbacks; B fault
1delay/0callbacks/804 failed STREX in4096instructions; same B with two-byte
in-memory branch-to-return4delays/0callbacks/3failures. No I/O in ticks.
Strongest suspect STREX11fa5858/retry585e on guard a97000cc beforecallback5868.
Physical PC/exception/MMU/monitor NOT captured; hardware cause not proven.
Bounded failure is responsiveness hardening, not worker-functionality proof.
No new host image/flash/card write/trial authorized. B remains disabled; A and
other files intact. Recovery confirmed in private quarantine record.
Validation: five controlled resident-loop/registration cases passed; Python
compile and diff checks passed. Root suite not repeated for trace-only additions.
Trace tool tools/trace_z7_worker_dispatch.py, source-safe evidence
 evidence/20261122-worker-dispatch-trace.json; exact firmware remains private.

## Failed B preserved and disabled - November 22, 2026

Same identified card available after B freeze report. Privately backed up all named
payloads/seed/configuration if present, compared earlier preserved contents; native
Move-Item Z7APP.BIN -> Z7APP.WORKER-B.disabled ONLY.234 existing files metadata
preserved except rename; catalog/named contents identical. A and all working copies
intact. No active root BIN, no replacement or flash. Safe eject VERIFIED.
Private record .private/card-backups/20261122-worker-pair-B-freeze-01/quarantine.json.
Current camera recovery not yet owner-confirmed. No further hardware trial approved.

## B froze on camera after A passed - November 22, 2026

Owner reports "yep that froze the camera" for return-only-worker B767ada05...
following working A412dffaf... . Exact matched pair differs only enable flag/CRC.
B WITHDRAWN. Worker registration/execution path now implicated on hardware without
restore/file I/O/GUI-seen wrapper/selection atomics. Actual failure PC and callback
entry remain unproved; current camera recovery NOT yet confirmed.
No further trials or host flashes authorized. Preserve/disable B when card available;
do not automatically restore or stage another payload. Record quarantine separately.
Prior known working A and six-grid baseline are preserved on card and privately.

## Return-only worker B staged and safely ejected - November 22, 2026

After A owner pass, owner explicitly approved B (yes). Same Sony card verified;
B Z7APP.BIN5324 bytes SHA767ada057f52df432aa037c341d300207d1bf436fea9258c5c58b78d4556a158.
Worker ENABLED, callback bx lr; only flag/CRC differ from working A.
A preserved as Z7APP.WORKER-A.disabled; six-grid baseline and all other payloads/
seed intact.233 preexisting metadata/catalog verified, private backups/readback:
.private/card-backups/20261122-before-worker-pair-B-01;
.private/card-staging/20261122-worker-pair-B-01/staging.json.
Safe eject VERIFIED by no-media volume check. No firmware flash or file I/O added.
Await owner normal cold-start result; do not claim B pass or physical cause.
If B freezes, stop, preserve/disable before any further trial; worker path implicated
by A/B but actual camera failure PC remains unproved. No further trial authorized.

## Owner confirmed control A working - November 22, 2026

Owner replied "yep works" to the staged A normal-start/battery/MENU-touch/grids/
ordinary-use/power-off check. General owner-confirmed pass, no itemized timings.
A is SHA412dffaf...99a200f9, worker disabled. This validates the common pair layout
on camera; next B differs only in worker-enable flag and CRC, callback bx lr.
B remains unstaged and requires separate approval. All card files preserved;
card last safely ejected to owner for A. No new firmware flash.

## Control A staged and safely ejected - November 22, 2026

Owner approved A only (yes; try again). Same identified Sony card verified.
Active Z7APP.BIN now5324 bytes SHA412dffaf9a2b5f9aa5cf9e715b66e778e9de1e9f4c67eabc2963df7899a200f9,
worker DISABLED. Exact old53334536... working module preserved as
Z7APP.SIX-GRID-WORKING.disabled, plus existing GRID-MENU-WORKING copy intact.
Private verified backups .private/card-backups/20261122-before-worker-pair-A-01;
record .private/card-staging/20261122-worker-pair-A-01/staging.json.
232 preexisting files verified by metadata, all prior payloads/seed contents and
catalog unchanged, configuration presence preserved. Exclusive create, flush/full
readback passed; Shell eject followed by no-media volume check VERIFIED.
No firmware flash. Await owner's ordinary cold-start A result: battery, MENU/touch,
grids, approximately30 seconds normal use and power-off. No hardware pass claimed.
Do not stage B until A result and separate explicit approval.

## Matched single-step worker controls prepared - November 22, 2026

Owner requested one step at a time until reproduction. Prepared A worker-disabled
and B worker-enabled from working battery/six-grid source; both 5324 bytes, BSS2216,
identical code/entry/relocations. Only image5012 flag and header CRC differ.
A SHA412dffaf...99a200f9; B SHA767ada05...4556a158. Callback begins bx lr.
No restore/file adapters/GUI-seen wrapper/selection atomics. Artifacts private:
.private/builds/20261122-worker-registration-pair-01. Neither staged/authorized.
Review WORKER_REGISTRATION_PAIR_REVIEW.md before asking to stage A ONLY.
A must pass before separately approved B; no automatic next trial or flash.
Card remains previous working53334536... module, restoration not yet owner-tested.

Both exact candidates pass270 grid checks/450 geometry calls and38 battery checks
each against ORIGINAL installed7d7356... host. Healthy worker tick returns for both;
B enters callback once, A never enters. Injected failed STREX: A returns with0
attempts; B stops after805 injected failures before callback, zero file I/O.
Not physical camera reproduction/cause proof. Source weak-CAS host NOT included.
Private audit .private/evidence/20261122-worker-registration-pair-01.json;
source-safe summary evidence/20261122-worker-registration-pair.json.
Build reproduced twice; Python compile/diff checks pass. Graph4151nodes/11443edges,
conditional-C parser limitations remain. Root suite not repeated for diagnostic
pair; existing feature audits exercised both exact files. No live audit process.

## Exact working/frozen comparison completed - November 22, 2026

User requested direct comparison of last working53334536... six-grid module with
frozen0714fe84... read-only restore. Same installed7d7356e7... host confirmed in
both frozen review manifests. Battery/sample source identical. New restore adds
worker registration, post-paint GUI flag, file/decoder, menu entry/label hooks,
and atomic fetch-add in selection handlers. File5260->6628; BSS2216->2260(+44,
accounted for by restore globals/file context/staging). No new native task,
custom settings page/dispatcher/key/mask changes; host source weak-CAS fix NOT
installed and not used in comparison.

Comparison tool executes exact failed binary plus two in-memory same-size controls:
2-byte registration call skip/ack at image2262 vs4-byte worker return stub at2304.
CRC only other change; size/entry/BSS/relocations/rest unchanged. Under injected
host STREX failure, exact working and registration-skip return; original failure
and empty-worker variants stall BEFORE callback and with ZERO file I/O. Normal
exclusive run verifies original worker open/read/close and stub no-I/O. Ten
controlled cases incl menu handlers. No diagnostic packets written/staged.

Important additional delta: failed grid selection handlers contain a second
LDREX/STREX loop from restore_selected's atomic increment. Center STREX image5206
stalls before setter under failure injection; old handler has no exclusive and
returns. This cannot explain boot freeze unless a selection handler ran. GUI-ready
check occurs inside worker callback, AFTER host guard; cannot protect against
host guard spin. Stronger localization, NOT physical cause confirmation.

Read WORKING_VS_FROZEN_COMPARISON.md and evidence/20261122-working-versus-frozen.json.
Card unchanged: restored working six-grid active, all failed payloads/seed intact.
No new flash/trial authorization. Direct comparison and Python compile checks
pass; graph refreshed. No full root tests repeated for comparison-only code/docs.
No live process or new installable artifact.

## Working module restored; worker-guard failure path localized offline - November 22, 2026

Owner authorized "yes and lets try to pin down the failure point". Exact previous
working six-grid/battery5260-byte module SHA53334536...12f226195 exclusively copied
to Z7APP.BIN. Same card/nine prior named hashes verified, private backups/readback,
230 existing file metadata/catalog unchanged; all disabled files/inert seed intact.
Safe eject VERIFIED. No firmware flash or new trial. Private restoration record:
.private/card-staging/20261122-restore-working-grid-menu-01. Owner reply to ordinary
restored-card check: "Not tested yet". Do not claim post-restore hardware test pass.

See WORKER_GUARD_FAILURE_REVIEW.md. Source reproduced installed host blob exactly
(4593bytes SHA6ef05fb5...2566fd3). Installed worker_tick strong CAS retries STREX at
0x11fa5858 via BNE0x11fa585e to LDREX0x11fa5852 on guard0xa97000cc BEFORE module
callback0x11fa5868. Fault injection (not physical proof):805 failed stores within
4096 instructions, zero callback calls, PCstays585e. One-attempt branch and actual
compiled weak-CAS source return after one failure. Healthy/busy/no-worker/recursive/
transient tests pass. Without worker registration the path reaches no STREX, matching working profiles.
Source now weak CAS, SDK documents skipped ticks; OFFLINE ONLY, NOT installed.
Reproduced compiled blob4593bytes SHAc117bbeb...f19fbed; all function addresses
unchanged,52 byte differences confined to worker tick. No EG/full image generated.

Stock assisted-QEMU boot range table classifies guard address in noncached range
0xa9700000..0xac400000 (flag1). Native helper101e3e2a agrees. This is software
classification, not physical MMU/monitor capture. Arm documentation supports
uncached/global-monitor failure mechanism. No guessed alias/address change.
Weak CAS prevents demonstrated spin but cannot make callbacks run if stores
always fail, or cure a data abort. Root physical failure remains unconfirmed.
Next boundary: resolve physical memory binding/execution evidence before any host
flash or more I/O trials. Full release/restore candidate remain withdrawn.
99 root tests pass; guarded fault cases and recursion/register checks pass;
stock QEMU inspected once and closed. Code graph refreshed, private dumps/binaries
remain private. No live process/new hardware authorization.
