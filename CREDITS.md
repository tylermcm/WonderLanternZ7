# Credits and provenance

WonderLanternZ7 is an independent, modified research workspace for the original
Nikon Z7. It builds on the projects below. Their authors' copyright notices and
licenses remain in the component directories; this repository does not replace
them with a single blanket license or claim endorsement by their maintainers.

## JKWTCN — Z7II extensions

**[JKWTCN/z7ii-extensions](https://github.com/JKWTCN/z7ii-extensions)** is the
foundation for the SD-loaded module architecture and several display-feature
concepts used in this port. The inspected source is pinned at
[`50a22b24c50619cffa646dac386e8334659f475a`](https://github.com/JKWTCN/z7ii-extensions/tree/50a22b24c50619cffa646dac386e8334659f475a).

The original module format, CRC/relocation approach, linker layout and LLVM
build approach derive from that work. Custom-DISP page/component concepts and
specific adapted drawing/geometry approaches are credited in the component's
[NOTICE.md](z7-native-modules/NOTICE.md). Copyright (c) 2026 JKWTCN; the
[MIT license](z7-native-modules/LICENSE) is preserved.

The original-Z7 host bindings, camera addresses, ownership/scheduling changes,
test tooling and incremental hardware trials are independent modifications.
Z7II binaries and native addresses cannot be substituted for the original-Z7
port. Upstream hardware claims describe their own target and are not evidence
that this port is verified on the original Z7.

## WonderLantern — Z7 QEMU lab

[WonderLantern/z7-qemu](https://github.com/WonderLantern/z7-qemu), pinned at
`97abf0b81cd3211f8374a38987a0beaf4549b90f`, supplies the emulator-lab foundation.
Its [GPL-2.0-or-later license and component notices](z7-qemu/COPYING) remain in
place. Local emulator changes and assisted tests do not establish physical
camera behavior.

## totwoto02 — Z7 firmware extensions

[totwoto02/z7-firmware-extensions](https://github.com/totwoto02/z7-firmware-extensions),
pinned at `96d03002220ecb0da9e387f88361632b9c3daa54`, supplies the earlier
extension/research foundation. Its [LICENSE](z7-firmware-extensions/LICENSE)
covers original project code/documentation under MIT, except four sound
implementation files identified in
[THIRD_PARTY_NOTICES.md](z7-firmware-extensions/THIRD_PARTY_NOTICES.md). Those use
the retained [Wonder Lantern Community License](z7-firmware-extensions/licenses/Wonder-Lantern.txt).
Keep those scopes separate from the MIT native-module and GPL emulator components.

All three source snapshots are vendored directories, not Git submodules.
[UPSTREAMS.json](UPSTREAMS.json) records their provenance and local changes.
Nikon firmware and other proprietary camera assets are not redistributed by
these project licenses. This is not an official Nikon, Wonder Lantern or
JKWTCN release.
