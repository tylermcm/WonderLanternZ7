# Rose-pink h category — November 23, 2026

The optional **h Display settings** entry continues the Custom Setting Menu's
colored category lettering. It uses the existing native 36-pixel prefix column,
a native text widget, rose-pink `#FF5599` when unfocused, and dark rose `#A00040`
on the yellow selection highlight. The native menu-row theme supplies the
background. The value column stays blank.

This is an emulator-tested SD-module candidate. It has not been staged or
verified on a physical camera. No firmware update is needed or authorized here.

## Exact candidate

| Item | Identity |
| --- | --- |
| Source | `z7-native-modules/plugins/lcd_settings_category_checkpoint.c` |
| Build option | `--settings-category` |
| Module size | 22,384 bytes |
| Module SHA-256 | `e37714672d16def1ba173edfec2ee0feefc0c48bf7a00f1422bc5c3c5641c02f` |
| Existing host MAIN SHA-256 | `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce` |
| Existing host EG SHA-256 | `f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140` |
| Earlier plain-entry module | `c79b6c52639c16072bb306da4e70f3017875d6649c5a329a554edd8a1c0bf2a8` |
| Hardware-tested LCD baseline | `f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e` |

Target: original Z7 C 3.80 without the paid RAW-video upgrade, using that exact
existing host. Installed-host identity remains based on the earlier successful
owner update, not physical firmware readback. The plain entry was previously
staged; its complete hardware test result is still pending. Neither earlier
module changes bytes when rebuilt with this optional styling disabled.

```powershell
.venv\Scripts\python.exe tools/build_z7_lcd_volatile.py --settings-category --output .private/builds/NEW-category
```

## Checks and scope

See [sanitized evidence](evidence/20261123-lcd-settings-category.json).

- Reproducible private build.
- 69 compiled menu/style contracts, including preservation of the native rows,
  activation maps, conflicting-menu rejection, native callback return values,
  no allocation of a missing prefix, font reuse and no styling-related file I/O.
- Assisted QEMU: 21 checks and nine captured frames covering selected/unfocused
  colors, refocus, entering a preset, Back, the grid-only page and re-entry.
- Ten independent pixel checks: all eight original overview rows and the owned
  settings page remain RGB-identical to the earlier plain candidate; the prefix
  background matches the row, both rose colors appear, the value column is blank,
  and refocus/Back restore the complete selected frame.
- All 103 repository tests passed. Both earlier module profiles rebuilt
  byte-for-byte identically.

Selected and unfocused frames were visually inspected. Images, generated BINs
and firmware data remain private. These checks use assisted file/UI boundaries
and do not establish physical controls, touch, shutdown, card durability or
recovery. The existing v3 journal format, persistence worker, rendering features
and host firmware are unchanged. The earlier persistence audits are separate
evidence; they were not rerun as physical tests for this visual refinement.

## Proposed SD-only test and rollback

Before separately authorized staging, identify the exact card, back up its current
module and all four CFG/DSP journal files privately, and preserve all existing
files. The last staged plain module should match the hash above; investigate any
unexpected module identity before writing. Preserve it under a new `.disabled`
name. Retain the verified f848 baseline already preserved as
`Z7APP.LCD-GRID-PERSISTENCE-WORKING.disabled` and in the private backups.

Stage only this exact candidate as `Z7APP.BIN`, verify readback and unchanged
settings/other files, then safely eject. With the camera off, insert the card
and start normally. **Do not run Firmware update.** One short combined check is
enough: inspect **h Display settings**, enter and leave a preset, check Back,
then normal controls and power-off/restart. Do not repeat every setting toggle.

If it freezes, stop testing. Earlier failures recovered after card removal and
sometimes battery removal; that is not guaranteed recovery for a new failure.
With the camera off, return the card to the reader, preserve the failed candidate
and restore the hash-verified f848 module after inspecting any unexpected file
changes. No reinstall or firmware update is part of this rollback. Emergency
recovery remains unverified; see [RISK_NOTICE.md](RISK_NOTICE.md).
