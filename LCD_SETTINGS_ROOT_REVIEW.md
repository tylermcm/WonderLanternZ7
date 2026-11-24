# Separate Display settings entry — November 23, 2026

This optional module moves **Display settings** from Framing grid display to a
separate entry in the **Custom Setting Menu** overview. Scroll past **g Movie**
to reach it. Back returns to that overview. Framing grid display retains only
4x4, 3x3, Golden ratio, Center cross, 6x6 and Off.

This is an offline-tested candidate, not an owner hardware result. The existing
hardware-tested module remains the working baseline. Nothing has been staged
to a card or flashed for this change.

## Exact candidate and compatibility

| Item | Identity |
| --- | --- |
| Module source | `z7-native-modules/plugins/lcd_settings_root_checkpoint.c` |
| Private module size | 22,128 bytes |
| Candidate SHA-256 | `c79b6c52639c16072bb306da4e70f3017875d6649c5a329a554edd8a1c0bf2a8` |
| Existing host MAIN SHA-256 | `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce` |
| Existing host EG SHA-256 | `f479950ea8188f1de337719bda34dc3765f397c97d79759349ec21566d58f140` |
| Retained working module SHA-256 | `f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e` |

Original Nikon Z7 C 3.80, without the paid RAW-video upgrade, with the exact
existing host above. The installed-host identity is based on the previously
approved successful update, not a physical firmware readback. This candidate
requires an SD module replacement only; it introduces no host firmware change.

The build is opt-in:

```powershell
.venv\Scripts\python.exe tools/build_z7_lcd_volatile.py --settings-root --output .private/builds/NEW-settings-root
```

The prior `--grid-persistence` profile still builds byte-for-byte identically
to the retained working module. Generated BINs and camera/emulator images stay
private.

## What changes

The candidate copies the eight existing overview rows and their event-map
pointers without changing them, then appends one row. It keeps the native
eight-row viewport and scrolls to the ninth entry. Existing native callbacks,
layout and geometry remain in use; the overview constructor also registers
the new label. Key activation and the touch activation map open the existing
owned display page. Back uses the native page stack.

Preflight rejects an unexpected overview identity or active widgets before
publishing either menu. The grid page uses its six-choice layout and native
Off callback again. Display rendering, settings fields, v3 journal encoding
and the Z7DSP file paths are unchanged. Legacy Z7CFG files remain read-only
fallback. This change does not address the brief wrong-grid startup transition
after battery removal.

## Validation and limits

The [sanitized evidence](evidence/20261123-lcd-settings-root.json) records the
exact candidate and scoped results. Native-key assisted QEMU covers the new
entry, Standard preset navigation, Back to the overview, the six-choice grid
page and re-entry. Seven private frames were captured; the overview, entry,
display page, return and grid-only frames were visually inspected.

Compiled instruction checks cover original-row preservation, activation maps,
conflicting overview rejection, save/load faults, preset persistence and grid
geometry: 53 menu contracts, 152 journal checks, 277 preset checks, and 262 grid
checks with 450 geometry comparisons passed. The native-key QEMU run passed
14 checks; all 103 repository tests passed. GUI/file/property boundaries are supplied in these checks. Neither
QEMU nor those instruction checks establish physical touch response, startup,
normal shutdown, card durability, camera update acceptance or emergency recovery.

## Proposed hardware check and rollback

No camera test or card write is authorized by this document. Before any staging,
verify the exact reader/card identity, preserve and hash the current module and
all four journal files privately, and compare them with the expected baseline.
Keep all existing card files intact, including disabled modules and updates.

After separate authorization, stage only the reviewed `Z7APP.BIN` and safely
eject. With the camera off, insert the card and start normally; **do not run
Firmware update**. One combined check is sufficient: open the separate Display
settings entry, enter and leave a preset, return to the overview, visit the
grid-only menu, then check normal controls and normal power-off/restart.

If the candidate freezes controls, stop the test. Earlier failures recovered
with the card removed; a battery removal was sometimes needed. That history is
not a guaranteed recovery procedure for a new failure. With the camera off,
return the card to the reader, preserve the failed candidate by renaming it,
and restore the hash-verified working module. Do not activate older failed
diagnostic modules or run another firmware update. The earlier working module
uses the same journals; any other unexpected file change should be inspected
before restoring it. Emergency firmware recovery remains unverified; see
[RISK_NOTICE.md](RISK_NOTICE.md).
