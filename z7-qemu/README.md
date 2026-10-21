# WonderLantern Z7 QEMU

[中文说明](README.zh-CN.md) · [Build](docs/build.md) · [Firmware input](docs/firmware.md) · [Architecture](docs/architecture.md) · [Debugging](docs/debugging.md) · [Research notes](docs/research-notes.md) · [Publication review](docs/publication.md)

A source overlay for QEMU 10.2.4 that provides an experimental Nikon Z7
research machine, a local browser controller, and a functional Bayer → ISP →
LCD pipeline. A part of the **WonderLantern** project.

**You supply the firmware.** This repository contains no Nikon firmware,
decrypted proprietary program, camera dump, key, font, icon bitmap, calibration
data, or screenshot of the original camera UI. It does not download Nikon
firmware. The emulator cannot show the camera menus without your compatible
local firmware input.

This is an independent research and learning project. Nikon is not affiliated
with or endorsing WonderLantern. Nikon and Z7 are used to identify the target.
We respect Nikon's rights and do not publish its private code. See the
[research and rights notice](NOTICE.md).

## What it does

The local Z7 C 3.80 research baseline runs the original menu and shooting UI,
including firmware-rendered ISO, shutter values, outlined text/icons and a red
no-card indicator. A stationary image can reach that UI through experimental
RAW DMA, functional image processing, the guest's output buffers, GPU drawing,
and LCD scanout. MENU transitions keep the same guest instance running.

The public package includes the board and pixel implementation from that
baseline. Packaging changes make the paths portable and replace private image
and icon fixtures with generated test inputs. Public CI uses synthetic tests
and does **not** run proprietary firmware. See [validation and limits](docs/testing.md)
for the difference between that baseline and tests of this export.

| Implemented in the experimental profile | Outside the verified scope |
| --- | --- |
| Two Cortex-A15 CPUs, GIC, inferred RAM windows, selected peripherals | Complete EXPEED hardware specification or natural power-on |
| Original firmware menu/shooting UI with explicit startup assistance | Unassisted boot or an exact camera boot ROM |
| Static RGGB/u16 input and functional NV12 output | Physical CMOS protocol, Nikon ISP algorithms and sensor calibration |
| Selected GPU paths, strokes, bitmap sampling, alpha and LCD composition | Complete GPU/OpenVG implementation |
| RAW drain and stream restart handshakes | AF/PDAF, MVD, real exposure response, mechanical timing |
| Browser keys, pause/resume/restart, guest diagnostics | Physical-camera USB access, installation, flashing, photo/movie recording |

This release supports **Z7 C 3.80 only**. It does not include Z9/ZR firmware or
claim those cameras work with this machine. It is not Magic Lantern, a direct
ML port, or a camera-installable WonderLantern build.

## Quick start

Use Linux with Python 3.12 or newer. On Windows, select your intended WSL
distribution explicitly; this project's local environment is `ubuntu-noble-nikon`.
The unrelated `ubuntu-noble` coursework environment is excluded by the tools.

```sh
git clone https://github.com/WonderLantern/z7-qemu.git
cd z7-qemu
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
    libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/build.py --jobs 4
python tools/make_cmos.py
python tools/interactive.py --firmware /absolute/path/to/your/z7-main-payload.bin \
    --photo-liveview --port 8787
```

Open `http://127.0.0.1:8787/`. The synthetic color bars/ramp are generated
locally; they are not a replacement drawn over the camera UI. To use your own
image, run `python tools/make_cmos.py --image /path/to/your/image.jpg` before
starting the guest. Image conversion requires NumPy and Pillow; the interactive
server itself uses Python's standard library.

Only this **extracted main payload** is accepted:

| Input | Value |
| --- | --- |
| Model / version | Nikon Z7 / C 3.80 |
| Length | 33,052,088 bytes |
| SHA-256 | `e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff` |
| Load address / initial PC | `0x10020000` |

The camera's upgrade container is not this payload. The repository provides
no keys or firmware extraction service. Obtain a compatible input independently
and keep it local. [Firmware setup](docs/firmware.md) explains the checks and
failure messages.

For a menu-only session, use `--profile menu` without `--photo-liveview`.
See [build instructions](docs/build.md) for WSL paths, offline builds and resource
requirements, and [usage](docs/usage.md) for all controls.

## Repository contents

```text
qemu/                 Board, GPU, ISP and upstream integration script
tools/                Build, local browser UI, RSP and synthetic RAW generation
tests/                Synthetic RAW, renderer and ISP contracts
docs/                 Setup, assumptions, debugging, lessons and export review
LICENSES/             Upstream licensing notice
.github/workflows/    Firmware-free source checks and QEMU build smoke test
.local/               Local generated inputs/logs/manifests (ignored)
.build/               Local upstream source and compiled output (ignored)
```

The QEMU source tarball is fetched from the upstream project and checked against
a pinned SHA-256 before building. Upstream QEMU is not vendored into this Git
repository. The build applies a small overlay; [architecture](docs/architecture.md)
documents its three upstream core adjustments.

## Tests

```sh
sh tests/run.sh
python tools/audit_publication.py
```

The test runner uses ASan/UBSan for the C pixel modules. The publication audit
checks the explicit public file inventory, content hashes, UTF-8 text, selected
credential patterns and Git history. It is a maintenance check; it does not
replace source/provenance review or provide a legal certification.

## Contributing and licensing

Start with [CONTRIBUTING.md](CONTRIBUTING.md). Submit synthetic reproduction
cases and code; do not attach firmware, camera dumps, calibration, extracted
fonts/icons, memory traces or private assets to public issues or pull requests.

The WonderLantern overlay, tools, tests and documentation are licensed under
**GPL-2.0-or-later**, unless an individual file states otherwise. The full
license is in [COPYING](COPYING). QEMU retains its own per-file licensing; its
overall emulator is GPLv2. [Upstream QEMU licensing](https://www.qemu.org/docs/master/about/license.html)
and the [retained upstream notice](LICENSES/QEMU-LICENSE.txt) apply. NumPy and
Pillow are separate dependencies installed from their own distributions.

No license here grants rights to Nikon firmware or other third-party private
material. The stated research purpose does not add a field-of-use restriction
to the GPL.
