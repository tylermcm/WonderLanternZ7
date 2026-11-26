# Shutter sound folder: choose from up to ten sounds

Status: **prepared, not staged.** Module `8b2b30b1`. Your everyday module with the shutter sound
(OFF/1–9, working on the camera) plus a choice of sounds from a folder on the
card. Design follows JKWTCN's MIT Z7II sound choice (`SHUTTER1`–`SHUTTER5`);
the folder, ten slots and loading only the chosen file are this port's own.

## How to use it

1. Make a folder **`SHUTTER`** in the card's root.
2. Put up to ten sounds in it named **`SOUND01.WAV`** … **`SOUND10.WAV`**
   (gaps are fine). Each must be a 48 kHz, 16-bit PCM WAV of at most 1 second,
   mono or stereo, the same rule as before. To convert any clip:

   ```powershell
   ffmpeg -i input.wav -t 1 -ar 48000 -ac 1 -c:a pcm_s16le SOUND01.WAV
   ```

   The original `A:\SHUTTER1.WAV` still works and shows as **Card**.
3. Power the camera off and on (the folder is checked at power-on).
4. **MENU → Custom settings → h Display settings → Shutter sound** now opens a
   page:
   - **Volume**: OFF, 1–9, as before (OK steps and previews).
   - **Sound**: OK steps through the sounds that exist (`Card`, `1`…`10`); the
     new sound loads in about a second and plays as a preview.
   - **Back**.

The choice and the volume are saved together in `Z7SND.DAT` and restored at
power-on. If the saved sound is no longer on the card, the first available one
is used. Only the chosen sound is kept in memory.

## Verified before the camera

- Your installed modules rebuild byte for byte; the folder code is behind its
  own build switch.
- Offline: the full display suite and every earlier sound, EXIF and playback
  check still pass, plus the folder checks (see the audit) for scanning, the
  page, stepping only through existing files, loading only when no sound is
  playing, previews and photos using the chosen file, saving and restoring the
  choice, a missing file, an older settings file, a folder-only card and a card
  with no sounds.
- Emulator: Nikon's real menu opens the new page titled "Shutter sound",
  steps Volume and returns with Back (26 checks, screenshots); the emulator has
  no card, so it shows `None` for the sound.

## Staging

Staging (with your approval) keeps your current module as
`Z7APP.LCD-SOUND-EXIF.disabled` and creates `A:\SHUTTER\` with three sample
sounds so you can try the choice at once: `SOUND01.WAV` the louder click,
`SOUND02.WAV` the softer click, `SOUND03.WAV` the field-test chime. Replace or
add your own afterwards. This build does not include the experimental
upside-down playback.
