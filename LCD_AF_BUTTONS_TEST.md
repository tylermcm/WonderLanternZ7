# AF-area buttons: camera test

Status: **prepared, not staged.** This is your everyday module (`8dcee0e0`:
display features, shutter sound, upside-down EXIF fix and playback) plus
**AF-area buttons**. You can give Fn1, Fn2, AF-ON, the sub-selector centre or
the movie-record button an AF-area mode. One press, in photo mode, switches to
that mode and it stays. This follows JKWTCN's Z7II
[AF-area shortcut](https://github.com/JKWTCN/z7ii-extensions/blob/f298964fdf6b0d20df0d3c6cad48a74aa5f5c339/docs/af-area-shortcut.md).
The research is in [AF_SHORTCUT_RESEARCH.md](AF_SHORTCUT_RESEARCH.md).

## What changes

- The module's last menu row, formerly **Shutter sound**, is now **Extras**.
  It opens: Shutter volume, Shutter sound (both as before), **AF-area
  buttons**, Back. The display pages (DISP) are unchanged.
- **AF-area buttons** lists Fn1, Fn2, AF-ON, Sub-selector center and
  Movie-record. OK on a row steps through OFF, Pinpt (Pinpoint), Single,
  Dynamic, Wide-S, Wide-L and Auto.
- A button only acts if its Nikon assignment (**Custom settings > f2 Custom
  control assignment**) is **None**. Nikon's own functions always win. The
  movie button is None out of the box. The others need to be set to None in
  f2 first.
- It only acts in **photo mode**, on the shooting screen. It respects the
  same rules as Nikon's AF-area menu: Pinpoint only in AF-S, Dynamic only in
  AF-C, and nothing in manual focus. It writes Nikon's AF-area setting and
  reads it back.
- Choices are saved in their own small file, `A:\Z7AFB.DAT`, only when you
  change them. The display settings and shutter-sound files are untouched.

| Card file | What it is |
| --- | --- |
| `Z7APP.BIN` | Everyday module + AF-area buttons, SHA-256 `e33474d1…` |
| `Z7APP.LCD-EVERYDAY-8DCE.disabled` | Your current module, kept unchanged |
| `Z7AFB.DAT` | Created when you first change a button |

## Steps (about 5 minutes)

1. Power on in photo mode, **AF-S**. Open the module's page, then **Extras**,
   then **AF-area buttons**. Set **Movie-record button** to **Wide-L**, and
   **Fn1 button** to **Single**.
2. In Nikon's **f2 Custom control assignment**, set **Fn1** to **None**.
3. On the shooting screen, press the **movie button**: the AF-area icon should
   show Wide-area (L). Press **Fn1**: it should show Single-point. Do it a few
   times, including quick taps.
4. Switch to **AF-C** and give a button **Pinpt**: pressing it should do
   nothing (Pinpoint is AF-S only). Give it **Dynamic** instead: it should
   work in AF-C.
5. Turn the photo/movie switch to **movie**: the movie button should start
   recording as usual and not change the photo AF-area.
6. Power off and on. Check the page still shows your choices and the buttons
   still work.
7. Optional: put Fn1 back to its old assignment in f2. Your choice on our page
   stays, but Nikon's function wins again.

Tell me if a quick tap is ever missed, if the AF-area icon only updates after a
half-press (the emulator did not show the icon refresh), if anything acts in a menu or in
playback, or if the shutter-sound rows behave differently from before.

## Verified before the camera

- `8dcee0e0` still rebuilds byte for byte; AF-area buttons are behind their
  own switch.
- Offline: the 277-check display suite runs first, unchanged. The AF checks
  use the module's real menu handlers, Nikon's real property getter for
  AF-area, focus mode and the five f2 assignments, and a recorded Nikon
  setter. They cover:
  - pages, labels, wrap-around, Back;
  - saving only after a change, and restoring at power-on;
  - a corrupt file means everything OFF;
  - each press acts once, not on hold, and skips the write when already
    selected;
  - Pinpoint refused in AF-C;
  - Nikon's f2 assignment wins;
  - nothing in movie mode, menus or playback;
  - a firmware mismatch turns the feature off and shows "--".
- Emulator: the module boots, Nikon's menus work. Extras and AF-area buttons
  open, Fn1 steps to Pinpt and Back returns (30 checks, screenshots).
- On the camera, the Nov 25 field test already switched AF-area with the movie
  button through the same runtime.

Credit: design follows JKWTCN's MIT z7ii-extensions AF-area shortcut;
original-Z7 bindings are independent work.
