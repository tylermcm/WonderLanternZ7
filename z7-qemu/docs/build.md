# Build and environment

## Requirements

The supported host workflow is Linux x86-64, Python 3.12+, a C compiler,
Ninja, pkg-config, GLib, Pixman and zlib development files. Ubuntu 24.04 with
GCC 13 is the local tested environment. Other platforms are not validated.
ARM guest execution uses TCG; KVM does not accelerate this ARM guest on x86.

Allow several GB for source/build files and at least a few GB of available host
memory. The board maps large experimental RAM pools: mapped capacity, resident
RAM and host commit pressure are different quantities. Avoid running several
camera guests or a large model server while building. `--jobs 4` is the default;
reduce it on constrained hosts. There is no fixed boot-time guarantee.

```sh
sudo apt-get update
sudo apt-get install build-essential ninja-build pkg-config python3-venv \
    libglib2.0-dev libpixman-1-dev zlib1g-dev libfdt-dev
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/build.py --jobs 4
```

QEMU configure may install its pinned Meson/pycotap Python build dependencies.
A cold build therefore needs network access even if the QEMU archive is local.
For an offline build, prepare those dependencies and the archive beforehand;
do not interpret `--archive` as a guarantee of fully offline configuration.

## Verified upstream source

The builder obtains `https://download.qemu.org/qemu-10.2.4.tar.xz` and requires:

```text
821b545b92f165e57dddccac5077d76d4d436a226595b8813ad59306bbfd0746
```

You can pre-download that original upstream archive and pass
`--archive /path/to/qemu-10.2.4.tar.xz`. Nikon firmware is never fetched by this
step. The tar extraction uses Python's data filter. Upstream EDK2 links to
external host headers are omitted; this build does not build those ROMs.
A completion marker distinguishes a complete extraction from an interrupted one.

`qemu/prepare_source.py` copies four emulator sources into `hw/arm`, adds the
machine's Kconfig/Meson entries and applies three narrow ARM core adjustments.
It checks the upstream version and expected source text instead of silently
patching unknown code. Re-running the builder is incremental. A new QEMU version
requires a deliberate port and retest.

Output defaults to `.build/`; `--work-dir` can point to a Linux filesystem for
better WSL performance. The binary is `WORK/build/qemu-system-arm`.
`.local/build-manifest.json` records its SHA-256, overlay hashes, upstream archive
hash, configure flags and hashes of changed core sources. The launcher checks
the binary and overlay fingerprints before using that build.

## Windows / WSL

Always specify the intended distribution. The local research environment is
`ubuntu-noble-nikon`; tools refuse the unrelated coursework `ubuntu-noble`.
They do not create, clone or change a WSL distribution.

For a checkout at `D:\CodexWork\WonderLantern-Z7`, an already provisioned Nikon
distribution can build with:

```powershell
wsl -d ubuntu-noble-nikon --exec python3 /mnt/d/CodexWork/WonderLantern-Z7/tools/build.py --work-dir /root/nikon-z7-lab/wonderlantern --jobs 4
wsl -d ubuntu-noble-nikon --exec python3 /mnt/d/CodexWork/WonderLantern-Z7/tools/make_cmos.py
wsl -d ubuntu-noble-nikon --exec python3 /mnt/d/CodexWork/WonderLantern-Z7/tools/interactive.py --firmware /mnt/d/your-private-inputs/z7-main-payload.bin --photo-liveview
```

Install NumPy/Pillow inside that distribution or use its virtual environment's
Python. Windows `D:\...` paths become `/mnt/d/...` inside WSL. A virtual
environment activated in one shell is not automatically active in another
`wsl --exec` call; use its Python path explicitly when needed.

The browser URL is `http://127.0.0.1:8787/`. Localhost forwarding normally exposes
the WSL server on Windows. If it does not, first verify the server inside the
selected distribution; do not change the server to a public bind address.

## Troubleshooting

| Failure | Meaning / next action |
| --- | --- |
| Archive SHA mismatch | Wrong/incomplete archive; obtain the pinned upstream file again |
| Unexpected QEMU source | Integration assumptions do not match; use a fresh pinned source tree |
| Missing development dependency | Read configure's named error and install that dependency |
| Source/binary changed | Rebuild the overlay and regenerate its manifest |
| Firmware hash/size error | Check the extracted MAIN, not the camera upgrade container |
| Active CMOS missing | Run `tools/make_cmos.py`, or use a menu-only session |
| Address already in use | Stop the existing owned server or choose `--port` |
| Host allocation failure | Free host commit/RAM and lower build parallelism |

See [debugging](debugging.md) for guest failures. Build completion by itself
does not prove camera boot or image-pipeline completion.
