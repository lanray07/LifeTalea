"""Package current LAT evidence with the byte-verified historical review archive."""

import argparse
import json
from pathlib import Path
import zipfile

from prepare_amazon_submission import OUT, ROOT, check_bundle, encoded, read, sha


PACKAGE = OUT / 'LifeTalea-Amazon-review-update-2026-11-05.zip'
INDEX = OUT / 'review-update-index.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        index = json.loads(INDEX.read_bytes())
        assert sha(PACKAGE.read_bytes()) == index['sha256']
        assert check_bundle(PACKAGE) == index['entriesVerified']
        print(f"Verified {index['entriesVerified']} entries")
        return

    entries = {}

    def add(path, expected=None, target=None):
        source = ROOT / path
        assert source.resolve().is_relative_to(ROOT) and not source.is_symlink()
        data = source.read_bytes()
        if expected is not None:
            assert sha(data) == expected, path
        name = target or path
        assert name not in entries, name
        entries[name] = data

    history = read('deliverables/amazon-submission/package-index.json')
    for archive in (history, history['serverPackage']):
        check_bundle(ROOT / archive['path'])
        add(archive['path'], archive['sha256'], 'historical/' + Path(archive['path']).name)

    for name in ('amazon-lat-v2-device-verification.json', 'amazon-lat-v2-fresh-tablet.json'):
        path = f'deliverables/reports/{name}'
        report = read(path)
        assert report['versionCode'] == 2
        add(path)
        for evidence in report['evidence']:
            assert evidence['path'].startswith('deliverables/reports/device-evidence/amazon-lat-v2/')
            add(evidence['path'], evidence['sha256'])

    add('deliverables/amazon-submission/LifeTalea-0.1.0-LAT-v2-unsigned.apk',
        '2b184fe1053edc1cf0158e17ca8a7f8a82e0fceb1f19c87be8de9cc889836ff6',
        'amazon-lat-only/LifeTalea-0.1.0-LAT-v2-unsigned.apk')
    add('deliverables/amazon-submission/LifeTalea-LAT-v2-Fire-debug-QA.zip',
        '33ac57636c6851ebba75e82ed4f535b3658fe58399b5fb1f15864417283a47a1')
    public_report = 'deliverables/reports/amazon-public-v3-apk-inspection.json'
    public = read(public_report)
    assert public['versionCode'] == 3 and public['exportedComponentAllowlist'] == 'PASS'
    add(public_report)
    add('deliverables/amazon-submission/LifeTalea-0.1.0-public-v3-unsigned.apk', public['sha256'],
        'public-draft/LifeTalea-0.1.0-public-v3-unsigned.apk')
    v3_path = 'deliverables/reports/amazon-lat-v3-device-verification.json'
    v3 = read(v3_path)
    assert v3['versionCode'] == 3 and v3['uploadSha256'] == public['sha256']
    add(v3_path)
    for evidence in v3['evidence']:
        assert evidence['path'].startswith('deliverables/reports/device-evidence/amazon-lat-v3/')
        add(evidence['path'], evidence['sha256'])
    for path in ('docs/AMAZON_RELEASE_REVIEW_2026-11-05.md', 'docs/AMAZON_LAT_STATUS.md',
                 'docs/KNOWN_LIMITATIONS.md', 'deliverables/reports/amazon-lat-v2-live.png',
                 'docs/AMAZON_PUBLIC_STORE_COPY_EN_US.md', 'docs/AMAZON_PUBLIC_REVIEWER_INSTRUCTIONS.txt',
                 'deliverables/reports/amazon-public-v3-draft-saved.png',
                 'deliverables/reports/amazon-supabase-deployment.json'):
        add(path)
    entries['READ-ME-FIRST.txt'] = (
        b'PUBLIC SUBMISSION BLOCKED. Read docs/AMAZON_RELEASE_REVIEW_2026-11-05.md.\n'
        b'Version 3 is the public draft candidate and was tested through Amazon Test 1.\n'
        b'Historical archives retain their original evidence.\n'
    )
    entries['manifest.json'] = encoded({'releaseStatus': 'BLOCKED', 'files': [
        {'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(entries.items())
    ]})
    with zipfile.ZipFile(PACKAGE, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)
    index = {'path': PACKAGE.relative_to(ROOT).as_posix(), 'sha256': sha(PACKAGE.read_bytes()),
             'bytes': PACKAGE.stat().st_size, 'entriesVerified': check_bundle(PACKAGE), 'releaseStatus': 'BLOCKED'}
    INDEX.write_bytes(encoded(index))
    print(json.dumps(index))


if __name__ == '__main__':
    main()
