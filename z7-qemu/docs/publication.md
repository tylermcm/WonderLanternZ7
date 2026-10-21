# Source-only publication review

## Export boundary

This release is assembled in an independent checkout with a new Git root commit.
It is not a public mirror of the private research repository. Only individually
selected emulator sources, host tools, synthetic tests, licenses and rewritten
documentation are imported. Private Git history, release assets and cold backups
are not imported.

The reviewed file inventory and SHA-256 values are in
`publication-manifest.json`. `tools/audit_publication.py` checks that inventory,
UTF-8 text, source license headers, oversized/binary content, selected credential
patterns and every reachable Git history blob. An unexpected public path fails
the check even if its suffix looks like source code.

## Content review decisions

| Material | Publication decision |
| --- | --- |
| Independently authored C board/GPU/functional ISP | Included as source |
| Register addresses, masks, protocol fields, dimensions and firmware fingerprint | Included as interoperability facts/experimental parameters |
| Original Nikon executable/source/disassembly | Excluded |
| Firmware containers and extracted MAIN/auxiliary images | Excluded; supplied locally by users |
| ROM/RAM/flash captures, keys and stream material | Excluded |
| Camera fonts, icon bitmaps, calibration and UI screenshots | Excluded |
| User-supplied bird photograph and its RAW/reference artifacts | Excluded |
| Native captured icon regression files | Replaced with synthetic geometric tests |
| Native RAW/output regression oracle | Replaced with synthetic level/cache tests |
| MVD initialization table bytes in the launcher | Replaced by an expected RAM fingerprint |
| Private logs, test results, snapshots, absolute input paths and backup tooling | Excluded |
| Upstream QEMU source | Downloaded separately from verified upstream; retained licensing notice included |

Source review covers initialized arrays as well as filenames. Runtime buffers
are allocations populated by the local guest, not embedded program dumps.
The large address/mask lists describe modeled interfaces; they contain no Nikon
instruction image, font, bitmap or cryptographic material. Algorithmic ISP and
rasterizer code is the independent functional implementation, not Nikon source.

## Repeating the check

```sh
python3 tools/audit_publication.py
git diff --check
git ls-files
git log --oneline --all
```

Maintainers may run `--refresh-manifest` **after** reviewing source and provenance
of changes. That command updates hashes only for the explicit allowlist. It does
not make arbitrary files redistributable or prove absence of all secrets. Review
new contributions and imported dependencies separately.

`.gitignore` is a convenience, not a publication audit. A force-add, historical
commit, release upload, issue attachment or CI artifact can bypass it. Public CI
never receives local firmware and does not upload local runtime outputs.

## Licensing and limitations

The overlay/tools/tests/documentation use GPL-2.0-or-later. Upstream notices are
preserved and QEMU's own source remains separately retrievable. This release
ships source, not a prebuilt QEMU binary or a firmware-containing disk image.

The review documents concrete exclusions and the inspected inventory. It is
not a legal opinion or a guarantee against all conceivable copyright/trademark
questions. Nikon material stays a separate user input; this repository grants
no new rights over it. See NOTICE.md and COPYING.
