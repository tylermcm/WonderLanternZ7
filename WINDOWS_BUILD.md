# Native Windows lab

This is an independent modification of the vendored research workspace. The
component licenses and upstream provenance remain in their original locations.
No firmware is downloaded by the helpers and no camera is accessed.

The October 21 native run passed 21 general UI checks, 17 menu checks for each
sound-capable preset, and the host/firmware checks recorded in
[the sanitized validation summary](evidence/20261021-windows-validation.json).

## Start the prepared app

Double-click `Start-Z7.cmd`. It opens the local app at
<http://127.0.0.1:8787/>. Keep its launcher running while using the app.
`Run-Z7.ps1` selects the build recorded in ignored
`.private/lab-environment.json`. The browser Stop button stops the guest;
the local server stays available for Restart and inspection.
Cold assisted boot took about 140 seconds on this laptop; the status text shows
its progress. This emulator is not real-time camera hardware.

MENU, arrows, OK, DISP, Play, Delete and i dispatch native guest inputs.
Keyboard shortcuts are listed below the camera display. To open Shutter sound
from fresh live view: MENU, left twice, down four times, right, up, OK.
The initial display is generated from synthetic Bayer input.

## Reproduce the build

Use Windows x64, Python 3.12+, several GB of available disk space, and network
access for build dependencies. QEMU's Windows build requires permission to
create symlinks, normally supplied by Windows Developer Mode. The setup uses
an isolated MSYS2 tree; it does not update an existing system MSYS2 or install
or reset a WSL distribution. The default is four compiler jobs; use `-Jobs 2`
on a smaller laptop.

Place your own official Nikon Z7 C 3.80 `Z_7_0380.bin` in Downloads, then:

```powershell
.\Setup-Z7.ps1
# Optional explicit interpreter or firmware input:
.\Setup-Z7.ps1 -PythonPath C:\Python312\python.exe -SourceFirmware C:\private\Z_7_0380.bin
```

The first setup creates `.venv/` and `.private/toolchain/msys64/`. Original
firmware stays in `.private/stock/`; candidates receive a new timestamped
directory. Reuse an existing checked QEMU build with `-SkipQemu`. Output
directories must be new. Configuration is saved after candidate checks pass.
Source edits to the QEMU overlay require a new QEMU build; the launcher rejects
a stale binary or source fingerprint.

To build QEMU directly in a prepared native environment:

```powershell
.venv\Scripts\python.exe z7-qemu/tools/build.py --work-dir .private/qemu --msys-root .private/toolchain/msys64 --jobs 4
```

## Validate

Use the recorded build directory in place of `BUILD` and new evidence paths:

```powershell
.\tools\check_windows.ps1
.venv\Scripts\python.exe tools/check_candidate_inputs.py --build BUILD
.venv\Scripts\python.exe tools/probe_sound_menu.py --build BUILD --output .private/evidence/full-menu-NEW --exercise
.venv\Scripts\python.exe tools/probe_sound_menu.py --build BUILD --preset shutter-sound --output .private/evidence/sound-menu-NEW --exercise
# While Run-Z7.ps1 is serving the full preset:
.venv\Scripts\python.exe z7-qemu/tools/verify_ui.py --menu --output .private/evidence/general-ui-NEW
```

The native QEMU executable uses DLLs from the isolated UCRT64 runtime directory
recorded in its local build manifest. The Python controller supplies that path
to the QEMU child process. Standalone QEMU diagnostics need the same directory
on their process PATH. Launcher stdout/stderr logs stay in `.private/`;
guest evidence and screenshots stay in `z7-qemu/.local/` or `.private/`.
`check_windows.ps1` runs Python input/launcher tests, the 668 synthetic renderer
and ISP contracts, and firmware-free QMP realization. The native host contract
runs do not use ASan/UBSan; the earlier Linux sanitizer results remain a separate
validation scope.
The UI verifier keeps the same scene-pixel, continued-ISP and same-session
requirements on every menu return. Its bounded return deadline defaults to
60 seconds per attempt and can be selected with `--menu-return-timeout`.
The earlier fixed 12-second window was too short on this native host.

These are assisted-emulator checks. They do not establish physical-camera
update acceptance, recovery, RAW-video upgrade compatibility, real WAV playback,
sensor operation, autofocus, recording or capture timing. The generated MAIN and
EG files are research payloads, not validated camera-installable containers.

Build references: [QEMU Windows build environment](https://www.qemu.org/docs/master/devel/build-environment.html#windows),
[MSYS2 isolated installer variants](https://www.msys2.org/docs/installer/).
