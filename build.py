"""Builds the Kodi repository files in zips/ and docs/.

Run this after changing an add-on and raising its version in addon.xml.
"""
import hashlib
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ADDONS = ['service.qualitycheck', 'plugin.video.mylists', 'repository.gorggogi']
ZIPS = ROOT / 'zips'
DOCS = ROOT / 'docs'


def build_zip(addon_id):
    source = ROOT / addon_id
    version = ET.parse(source / 'addon.xml').getroot().get('version')
    target = ZIPS / addon_id
    target.mkdir(parents=True)
    path = target / ('%s-%s.zip' % (addon_id, version))
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(source.rglob('*')):
            if item.is_file() and '__pycache__' not in item.parts:
                archive.write(item, Path(addon_id) / item.relative_to(source))
    return path


def addon_entry(addon_id):
    text = (ROOT / addon_id / 'addon.xml').read_text(encoding='utf-8')
    return re.sub(r'^<\?xml.*?\?>\s*', '', text, flags=re.S).strip()


def main():
    shutil.rmtree(ZIPS, ignore_errors=True)
    shutil.rmtree(DOCS, ignore_errors=True)
    ZIPS.mkdir()
    DOCS.mkdir()

    built = {addon_id: build_zip(addon_id) for addon_id in ADDONS}

    entries = '\n'.join(addon_entry(addon_id) for addon_id in ADDONS)
    listing = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n%s\n</addons>\n' % entries
    (ZIPS / 'addons.xml').write_bytes(listing.encode('utf-8'))
    digest = hashlib.md5(listing.encode('utf-8')).hexdigest()
    (ZIPS / 'addons.xml.md5').write_text(digest, encoding='ascii')

    # Kodi reads this page as a file source, so the repository zip can be
    # installed on a TV without copying it over by hand.
    installer = built['repository.gorggogi']
    shutil.copy(installer, DOCS / installer.name)
    page = '<!doctype html>\n<html><body>\n<a href="%s">%s</a>\n</body></html>\n' % (installer.name, installer.name)
    (DOCS / 'index.html').write_text(page, encoding='utf-8')
    (DOCS / '.nojekyll').write_text('', encoding='utf-8')

    for path in built.values():
        print(path.relative_to(ROOT))


if __name__ == '__main__':
    main()
