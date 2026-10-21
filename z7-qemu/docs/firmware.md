# Bring your own firmware

The public repository contains the emulator and host tools. It intentionally
contains no executable Nikon firmware. There is no automatic Nikon download,
bundled decryption key, camera dump, firmware installer or physical-device access.

## Required input

Use your own locally obtained **extracted Z7 C 3.80 MAIN payload**. Its expected
length is 33,052,088 bytes and SHA-256 is:

```text
e6df1764323fb1c287159dd3ce1c84ac93c72b96ba6eb09c070295c093fecbff
```

The normal camera upgrade `.bin` is a container, and is not accepted as this
MAIN payload. A filename match is not proof of compatibility. This repository
does not provide an extraction service or distribute the resulting program;
prepare a compatible input independently from material you are entitled to use.

Check it locally with:

```sh
sha256sum /your/private-inputs/z7-main-payload.bin
wc -c /your/private-inputs/z7-main-payload.bin
```

PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath D:\your-private-inputs\z7-main-payload.bin
(Get-Item -LiteralPath D:\your-private-inputs\z7-main-payload.bin).Length
```

Then pass its absolute Linux path:

```sh
python3 tools/interactive.py --firmware /your/private-inputs/z7-main-payload.bin \
    --photo-liveview
```

No prescribed filename or repository folder is required. Keeping firmware
outside the checkout is recommended. The launcher verifies size and digest;
the board maps it at `0x10020000`, and generic loader devices set both initial PCs.
It reads the input file and does not write it.

## Inputs and generated data

The original Nikon program remains a separate local input with its own rights.
The GPL license of the emulator does not grant firmware redistribution rights.
Do not include that input in a fork, issue attachment, release, container image,
build cache shared with others, or public workflow artifact.

Generated RAW files, references, guest logs and QMP screenshots live under
`.local/`. Logs may include guest memory and paths; screenshots can contain
proprietary UI. They are local research outputs, not public fixtures. The
publication audit excludes local data, and the public CI requires no firmware.

## Compatibility boundary

All startup function addresses, state layouts and input geometry are specific
to this fingerprint. A different Z7 firmware or another Nikon camera needs new
evidence and a new profile. Removing the digest guard does not make it supported.

The assisted launcher modifies guest RAM, including diagnostic controller state,
a small resource-version input and the MVD schedule. It also calls original
firmware routines. It changes no bytes in the original input file and injects
no Nikon program into the repository. See [architecture](architecture.md) for
the implications of assisted boot.
