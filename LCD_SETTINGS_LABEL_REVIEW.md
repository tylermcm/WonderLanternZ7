# Display settings name repair — November 24, 2026

The owner reports that the rose-pink category module shows only **h** after
about ten seconds powered off. Opening the item and pressing Back restores
**Display settings**. The [old candidate](LCD_SETTINGS_CATEGORY_REVIEW.md) therefore
does not pass hardware acceptance; see the [owner report](evidence/20261123-lcd-settings-category-hardware-label-defect.json).

This optional repair registers missing or stale labels on the GUI task and
refreshes a newly created row's font cache. It has not been staged or tested on
the camera. No firmware update is needed or authorized by this document.

## Exact candidate

| Item | Identity |
| --- | --- |
| Source | `z7-native-modules/plugins/lcd_settings_label_checkpoint.c` |
| Build option | `--settings-label-refresh` |
| Module bytes | 22,712 |
| Candidate SHA-256 | `5e62ce53def1a8de4cf789bb4f3b03fb51791943501a11da6ca4be44b4e77349` |
| Previous defective module SHA-256 | `e37714672d16def1ba173edfec2ee0feefc0c48bf7a00f1422bc5c3c5641c02f` |
| Tested rollback module SHA-256 | `f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e` |
| Existing host MAIN SHA-256 | `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce` |
| Existing host EG SHA-256 | `f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140` |

Original Z7 C 3.80 without the paid RAW-video upgrade, using that exact host.
Installed-host identity is based on the earlier successful owner update, not
physical firmware readback. The earlier category profile still rebuilds
byte-for-byte identically with this optional repair disabled.

## Repair and evidence

Previously the constructor registered the name, but there was no later name
refresh. The repair checks the two owned shared labels before the native
overview callback. A missing or changed label is reseeded. The existing primary
row is rebound once when first encountered, after a label repair, or on re-entry
even if a native widget address is reused. Ordinary paints do not continually
register labels or recreate font caches. No row is allocated by the repair.

The repair runs in GUI callbacks. It makes no label calls during module loading
and performs no file I/O during the refresh. The host, settings format, journal
worker, grid behavior and category colors are unchanged.

[Scoped evidence](evidence/20261124-lcd-settings-label.json) includes:

- A reproducible private build and 76 compiled menu/lifecycle checks, including
  erased-label recovery, one-time cache refresh on re-entry, no cache churn,
  no GUI file I/O and no label registration from the loader.
- An explicit empty-label/cache test on the old module and the repair. The old
  module leaves the recreated row blank despite a reseeded text registry. Under
  the same injected condition the repair displays the complete name. The new
  targeted QEMU run passed eight checks and captured four private frames.
- Three pixel comparisons: the old recreated name is blank; the repaired full
  frame matches its initial frame; and the initial frame remains RGB-identical
  to the earlier category styling. The repaired frame was visually inspected.
- All 103 repository tests passed.

The controlled test demonstrates a label/cache failure mechanism and recovery.
It does not establish the exact physical cold-start ordering that causes the
owner's symptom. Assisted QEMU supplies module/settings filesystem boundaries;
instruction checks supply GUI/font/theme boundaries. Physical cold-start,
controls, shutdown and recovery still require owner verification. Saved settings
were not shown to be lost by the reported name-label defect.

## Proposed SD-only check and rollback

After separate authorization, identify the card and back up its current module,
all four journal files and existing root files privately. The current module
should match the defective e377 hash above; investigate any unexpected identity.
Preserve it under a new disabled name, and retain all previous modules and files.
Keep the tested f848 rollback module intact. Stage only the reviewed candidate
as `Z7APP.BIN`, verify readback and unchanged files, then safely eject.

With the camera off, insert the card and start normally. **Do not run Firmware
update.** Inspect **h Display settings before opening it**. Then power off for
at least 20 seconds, restart and check the full name before opening it again.
Check normal navigation, Back, controls and power-off in that same short pass.
No per-setting test sequence or battery removal is needed.

If it freezes, stop. Earlier failures recovered after card removal and sometimes
battery removal, but this does not guarantee recovery. With the camera off,
return the card to the reader, preserve the failed candidate and restore the
hash-verified f848 module after inspecting any unexpected file changes. Do not
run another firmware update. Emergency recovery remains unverified; see
[RISK_NOTICE.md](RISK_NOTICE.md).
