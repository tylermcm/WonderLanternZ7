# LCD preset persistence validation — November 23, 2026

The existing grid-persistence module passes an additional **277 instruction-fixture
checks** covering all four compact DISP presets. No firmware/module code changed,
no new candidate was generated, and no camera/card was accessed for this audit.

Exact module: 21,560 bytes, SHA-256
`f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e`.
Host MAIN: `24b2074559ca6089432011d98a72193f81e112c2621aee2aa0ed1359febfa7ce`.
The frozen grid checkpoint and its installation/recovery scope remain in
[LCD_GRID_PERSISTENCE_REVIEW.md](LCD_GRID_PERSISTENCE_REVIEW.md).

## Executed checks

- Actual compact native menu callbacks open Standard, Minimal, Composition and
  Exposure, edit page enable, grid and horizon, and toggle all eight information
  bits through the information/More submenus.
- Each preset's complete edited model is saved and cold-reloaded. Independent
  v3 record encoding checks the exact bytes, CRCs and generation values.
- Ten saves alternate the new journal slots, preserve the other slot, and leave
  the legacy `Z7CFG` record unchanged. GUI actions perform no file I/O; workers
  perform no native label writes and acknowledge the complete revision.
- Sixteen native DISP admission/cycle checks skip the disabled page after
  reload. These use supplied incoming GUI/property context.
- Resetting every preset restores its supported defaults while retaining page
  enables, master/battery flags and the saved Center cross shape. A later
  Custom pages OFF save/reload also retains that shape.

Runner: [tools/audit_z7_lcd_preset_persistence.py](tools/audit_z7_lcd_preset_persistence.py).
Results: [evidence/20261123-lcd-preset-persistence-01.json](evidence/20261123-lcd-preset-persistence-01.json).

The fixture supplies filesystem, native GUI and property boundaries. It does
not establish physical menu pixels, focal telemetry, all output/capture/sleep
lifecycles, shutdown durability or camera recovery. These checks supplement
the earlier grid/codec/storage tests; they do not expand the owner hardware
verification scope in the [public hardware report](DEVELOPMENT_UPDATE_2026-11-23.md).

## Remaining hardware gates

The owner has already reported Center cross restoration after shutdown and
battery removal, with a valid physical v3 slot0 readback and unchanged older
settings files. A brief wrong-grid transition after battery removal remains open.

The owner has now confirmed 6x6 retention after at least 20 seconds off with
normal controls. Read-only second-slot and prior-slot/legacy preservation checks
now pass: valid
6x6 generation1 in slot1, with the original Center cross generation0 and both
legacy files unchanged. See the [physical second-slot report](evidence/20261123-lcd-grid-second-journal-readback.json).
Broader preset-setting hardware checks and capture/lifecycle validation remain
separate steps. No new flash or automatic card replacement is needed for them.
