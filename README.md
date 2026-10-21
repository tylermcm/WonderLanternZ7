# WonderLantern Z7 lab

Independent, modified research workspace for **Nikon Z7 C 3.80** firmware
extensions and assisted QEMU execution. Start with [HANDOFF.md](HANDOFF.md)
when continuing on another computer.

The corrected full firmware passes 21 general UI checks and 17 sound-submenu
checks. The sound-only preset also passes the same 17 submenu checks. This
establishes selected emulator behavior. Camera installation, real WAV playback,
capture, recording and recovery remain unverified.

## Contents

- `z7-qemu/`: complete source overlay and tools, with local changes included.
- `z7-firmware-extensions/`: complete patcher source, including all sound fixes.
- `tools/`: local build, validation, setup and launch helpers.
- [HANDOFF.md](HANDOFF.md): laptop setup, results, next steps and known gaps.
- [SOUND_MENU_FIX.md](SOUND_MENU_FIX.md): fault analysis and corrected addresses.
- [LAB_REPORT.md](LAB_REPORT.md): complete lab history.
- [UPSTREAMS.json](UPSTREAMS.json): original repository and commit provenance.
- `evidence/`: source-only validation summary; no firmware or camera screenshots.

The two component directories are vendored source snapshots, **not submodules**.
Their upstream licenses and notices remain in place. This repository is a modified
research workspace and does not claim to be an official WonderLantern release.

## Quick setup

Use Linux or WSL with Python 3.12+. In an already installed Ubuntu environment:

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
  libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 tools/setup_lab.py --jobs 4
```

Obtain your own official Nikon `Z_7_0380.bin` and place it at
`.private/stock/Z_7_0380.bin`. Check its SHA-256 against the handoff, then:

```sh
LAB_PY="$HOME/.local/share/wonderlantern-z7/venv/bin/python"
"$LAB_PY" tools/build_firmware.py --output .private/builds/20261020-09
"$LAB_PY" tools/check_candidate_inputs.py --build .private/builds/20261020-09
"$LAB_PY" tools/launch_z7.py
```

Open <http://127.0.0.1:8787/>. On Windows, after the Linux setup/build above,
`Run-Z7.ps1 -WslDistro Ubuntu` uses the locally recorded Linux interpreter.
Windows needs a Python launcher (`py` or `python`); no Windows Python packages
are needed just to start the WSL server.

## Inputs and distribution

No Nikon firmware, modified firmware binary, dump, key, camera screenshot,
private media, virtual environment or compiled QEMU binary is included. These
stay in ignored local directories. Generated CMOS color bars are recreated from
source. No camera-installable update package or flash writer is supplied.

See `z7-qemu/NOTICE.md`, `z7-qemu/COPYING`, and the license/notices inside
`z7-firmware-extensions/`. Their respective licenses apply to their components;
no license here grants rights over Nikon firmware.
