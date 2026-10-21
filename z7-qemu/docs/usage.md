# Running and controlling the guest

Generate local inputs once, then start one guest:

```sh
python3 tools/make_cmos.py
python3 tools/interactive.py --firmware /path/to/z7-main-payload.bin \
    --photo-liveview --port 8787
```

The UI is deliberately small: camera image, native keys and run controls, with
square corners and no Nikon branding assets. Browser pixels come from QMP
`screendump`; the host adds no ISO, shutter, icon or viewfinder overlays.
The controls and status text are Chinese in this first export.

## Keys

| Browser control | Keyboard |
| --- | --- |
| Direction pad | Arrow keys |
| OK | Enter |
| Left / return | Escape |
| MENU | M |
| Playback | P |
| i | I |
| Delete | Delete |

Keys invoke the guest's original AutoOperation interface using logged diagnostic
calls. This is not a physical electrical switch protocol. Playback and capture
behavior are incomplete; button presence is not evidence of implemented media.

MENU opens the guest menu and returns within the same running instance. A
press can first change focus to its sidebar; another may be needed to close it.
The separate menu/shooting **profile switch restarts** the guest. Pause/resume
keeps it; restart discards the guest and loads local inputs again. Stop closes
the QEMU process while keeping the browser server available. Ctrl+C exits the
server and closes its guest.

## Replace the scene

```sh
python3 tools/make_cmos.py --image /path/to/your/own/photo.jpg
```

The complete image is stretched to each experimental geometry. Conversion is
inverse sRGB transfer → bicubic resizing in linear RGB → RGGB mosaic → 12-bit
quantization with black64/white4095 → padded row storage. The generated manifest
contains checksums and a packing roundtrip check. Original photo bytes are not
copied into the public tree. This is a stationary source; changing the file
during a running session is not a supported live video input.

| Generated input | Geometry | Storage / stride |
| --- | --- | --- |
| Unpacked boundary test | 640×480 | u16LE /1280 |
| Ingress experiment | 1380×918 | two 12-bit samples per3 bytes /2080 |
| Functional ISP input | 2780×932 | u16LE /5568 |

None of these implies a full-resolution physical CMOS wire format. The browser
reports RAW and ISP batches plus observed LCD reads. A batch count is a device
transaction count, not proof of physical sensor timing or a movie frame rate.

## Other launch options

Use `--profile menu` without `--photo-liveview` for assisted menu boot without
a RAW stimulus. `--build-manifest PATH` selects a build manifest explicitly.
`--one-insn-per-tb` enables the slower diagnostic translation mode.
`--isp-disable-cache` recomputes pixels for comparison. `--no-current` avoids
updating the local current-session pointer. See `--help` for earlier diagnostic
options; they are experimental and are not interchangeable acceptance profiles.

## Local files and access

Each session writes `.local/sessions/<timestamp-random>/actions.jsonl`.
`.local/sessions/current.json` identifies the primary current session. Live QEMU
logs and temporary PPMs are spooled on the Linux temporary filesystem: reading
a continuously appended log on a WSL Windows share caused ENODATA in export
testing. On guest close the log is copied into the session directory; the
temporary files are removed. A host crash can therefore leave a live log in
that temporary directory. PNGs are returned from memory to the browser.

HTTP, QMP and GDB RSP bind to localhost. The HTTP action queue is bounded and
requires a per-session token. Local code with access to the server can operate
it; this is a local development UI, not an internet service. Do not publish
tokens, session logs, dumps or UI screenshots as repository artifacts.
