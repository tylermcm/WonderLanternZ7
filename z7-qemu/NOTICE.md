# Research, rights and distribution notice

WonderLantern is an independent research and learning project. Its purpose is
to understand camera software behavior and build reusable emulation tools.
It is not affiliated with, sponsored by, or endorsed by Nikon Corporation.

Nikon retains its rights in its software, firmware, trademarks and other
materials. This public distribution includes no Nikon private source code,
original or decrypted proprietary firmware, boot image, ROM/RAM/flash dump,
encryption key, calibration dataset, extracted font/icon asset or camera UI
screenshot. Users obtain and retain any required firmware input themselves.

The board implementation and its interface constants describe experimental
behavior observed during independent research. Interface addresses, masks,
geometries, version checks and hashes identify interoperability conditions;
they are not a publication of Nikon's program code. The host tools read an
explicit local firmware path and never download Nikon firmware.

The public tools operate on a local QEMU guest. No physical-camera USB access,
firmware installer, signing material, privileged-camera payload or flash writer
is included. Do not mistake simulated boot success for a camera installation
method.

The research-purpose statement describes the project and does not restrict
rights granted by its GPL license. Third-party materials retain their own
licenses and rights. No WonderLantern license grants permission to redistribute
Nikon firmware or other material you do not have the right to publish.

## Source licenses

WonderLantern overlay, tools, tests and documentation: GPL-2.0-or-later,
unless a file states otherwise. See COPYING.

The integration script modifies locally obtained QEMU source. QEMU is released
overall under GPLv2 with specific licenses on some components. The retained
upstream LICENSE notice is in LICENSES/QEMU-LICENSE.txt; the verified upstream
archive retains its full notices. QEMU is a trademark of Fabrice Bellard.

No Magic Lantern source is bundled. Magic Lantern was an architectural
reference for emulator-assisted camera research. NumPy, Pillow, GLib and other
build/runtime dependencies are installed separately and retain their licenses.
