"""Check captured h-category pixels against native menu frames (MIT).

Private assisted-QEMU captures only; not physical display verification.
"""
import argparse
import json
from pathlib import Path
from PIL import Image
from prepare_flash_review import require_private_output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--baseline', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); out = require_private_output(a.output)
    result = json.loads((a.capture/'result.json').read_text())
    assert result['passed']
    checks = []

    def check(name, good):
        assert good, name
        checks.append(name)

    def frame(directory, name):
        return Image.open(directory/(name+'.png')).convert('RGB')

    first = frame(a.capture, 'custom-settings-overview')
    original = frame(a.baseline, 'custom-settings-overview')
    check('original-eight-rows-full-rgb-identical', first.tobytes() == original.tobytes())
    for name, color in (('display-settings-entry', (160,0,64)),
                        ('display-settings-unfocused', (255,85,153))):
        im = frame(a.capture, name)
        background = im.getpixel((120,68))
        check(name+'-no-prefix-background-patch', all(im.getpixel(point) == background
              for point in ((78,68),(113,68),(78,103),(113,103))))
        check(name+'-rose-glyph-present', sum(c == color for c in im.crop((78,68,114,104)).getdata()) > 80)
        check(name+'-value-column-blank', len(set(im.crop((630,70,690,102)).getdata())) == 1)
    selected = frame(a.capture, 'display-settings-entry').tobytes()
    check('refocus-restores-full-rgb-frame', frame(a.capture, 'display-settings-refocused').tobytes() == selected)
    check('back-restores-full-rgb-frame', frame(a.capture, 'display-settings-back').tobytes() == selected)
    check('owned-settings-page-full-rgb-identical',
          frame(a.capture, 'display-settings-root').tobytes() == frame(a.baseline, 'display-settings-root').tobytes())
    report = dict(passed=True, checks=checks, count=len(checks), module_sha256=result['module_sha256'],
                  physical_display_verified=False, source_images_private=True)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__ == '__main__':
    main()
