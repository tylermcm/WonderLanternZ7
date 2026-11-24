"""Compare old/fixed recreated-name frames, without exporting images (MIT)."""
import argparse
import json
from pathlib import Path
from PIL import Image
from prepare_flash_review import require_private_output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('old', 'fixed', 'style', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); out = require_private_output(a.output)
    checks = []

    def frame(path):
        return Image.open(path).convert('RGB')

    def check(name, good):
        assert good, name
        checks.append(name)

    old = frame(a.old/'name-after-open-back.png').crop((114,68,560,104))
    initial = frame(a.fixed/'name-before-fault.png')
    repaired = frame(a.fixed/'name-after-open-back.png')
    check('old-recreated-name-region-is-blank',len(set(old.getdata())) == 1)
    check('fixed-recreated-frame-restores-complete-rgb',initial.tobytes() == repaired.tobytes())
    check('fixed-first-frame-preserves-category-styling',initial.tobytes() == frame(a.style/'display-settings-entry.png').tobytes())
    q = json.loads((a.fixed/'result.json').read_text())
    assert q['passed']
    report = dict(passed=True, module_sha256=q['module_sha256'], count=len(checks),
        checks=checks, explicit_label_cache_fault=True,
        physical_cold_start_cause_established=False, screenshots_private=True)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__ == '__main__':
    main()
