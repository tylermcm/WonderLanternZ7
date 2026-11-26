# LCD module with shutter sound and a volume setting: camera test

Status: **works on the camera, November 25, 2026.** Staged with the owner's
approval; the owner reports the row, previews, photo clicks at the chosen level
and the saved level after restart all work as intended
([evidence](evidence/20261125-lcd-shutter-sound-hardware-result.json)). It stays
installed; the previous module is kept as `Z7APP.LCD-LABEL-5E62.disabled`.

Original status: This is your installed LCD module (`5e62ce53`)
with the shutter sound built in and a volume row on its settings page. It
follows the [shutter-sound camera tests](SHUTTER_SOUND_ON_PHOTO_TEST.md) of
November 25, 2026: the click played on time on every photo and burst frame in
Silent photography (22 of 22 in the louder-click run), but was a little quiet
at full volume. No firmware update; the installed module host stays as is.

## What changes

- **Display features: none.** The module is built from the same source and
  configuration as `5e62ce53`; with the sound option left out it still rebuilds
  to exactly `5e62ce53`. Your display settings file and its format are not
  touched.
- **New row** at the bottom of **Display settings**: **Shutter sound**, value
  `OFF`, `1`–`7`, default `5`. Press **OK** on the row to step to the next level;
  each level plays a preview. After `7` it goes to `OFF`. `1`–`5` match the
  test module's levels; `6` and `7` are louder than anything you have heard so
  far (about +3 dB and +6 dB).
- The level is saved in its own small file `Z7SND.DAT` a few seconds after you
  stop changing it, and restored at power-on.
- The sound plays on each photo, including every burst frame, only while
  **Silent photography is on**, using `SHUTTER1.WAV` (the louder click already
  on the card).

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | LCD module with shutter sound, SHA-256 `92602a4a…` |
| `Z7APP.LCD-LABEL-5E62.disabled` | Your current LCD module, kept unchanged |
| `SHUTTER1.WAV` | The louder click, already on the card |
| `Z7SND.DAT` | Created when you first change the level |

## Steps (about 3 minutes)

1. Power on. The display works as usual.
2. **MENU → Custom settings → h Display settings**, then scroll to the bottom
   row, **Shutter sound 5**.
3. Press **OK** a few times. Each press should play the click at the new level.
   Pick the level you like (for example 6 or 7).
4. Leave the menu and wait about 10 seconds.
5. Turn **Silent photography on** and take a few photos. The click should play
   at your level.
6. Power off and on, open Display settings again, and check the level was kept.

## What to report

- Did each OK press play a preview, and which level sounds right?
- Did photos click at that level?
- Was the level still there after power-off?
- Anything unusual in the menu or the display.

If anything goes wrong, rename `Z7APP.LCD-LABEL-5E62.disabled` back to
`Z7APP.BIN` (or ask me to restore it). Removing the card returns the camera to
stock behavior.

## Verified before the camera

- `5e62ce53` rebuilds byte for byte from the changed sources.
- Offline (Unicorn): the full 277-check LCD preset-persistence suite passes
  unchanged against the new module, plus 28 sound checks: the row reads
  "Shutter sound 5" below Battery percentage with the other rows unchanged; OK
  steps 6, 7, OFF, 1… with a preview and no display-journal change; the worker
  writes `Z7SND.DAT` only after the level is stable, never rewrites without a
  change, and a reload restores it; a damaged file keeps level 5; the capture
  event plays at the chosen level only in Silent photography, never when OFF,
  counts a busy service without retrying, and always runs Nikon's handler;
  no WAV leaves Nikon's slots untouched; levels 5, 6 and 7 produce the exact
  expected samples, with 6 and 7 clipping at full scale.
- Assisted QEMU, 25 checks on Nikon's real menus: the Display settings entry,
  root page and preset pages work as before; the new row shows `5` and OK steps
  it to `6` and `7` (screenshots). The emulator has no card or sound output, so
  it cannot play the preview.

Credit: design follows JKWTCN's MIT Z7II shutter-sound feature (volume 1–5,
preview, Silent photography only); original-Z7 bindings are independent work.
