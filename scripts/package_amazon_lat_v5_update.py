"""Preserve the v5 local QA archive and add current Amazon distribution evidence."""
import argparse
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle

PACKAGE = OUT / 'LifeTalea-Amazon-LAT-v5-update-2026-11-10.zip'
INDEX = OUT / 'review-update-index.json'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    if options.check:
        index = json.loads(INDEX.read_bytes())
        assert index['path'] == PACKAGE.relative_to(ROOT).as_posix()
        assert sha(PACKAGE.read_bytes()) == index['sha256']
        assert check_bundle(PACKAGE) == index['entriesVerified']
        print(f"Verified {index['entriesVerified']} entries")
        return
    base = OUT / 'LifeTalea-product-privacy-v5-2026-11-10.zip'
    assert sha(base.read_bytes()) == '7921b0ff3f3c7e58e249e6a39de2df0461a0a823b4c959eb7c3623b3922b20ad'
    assert check_bundle(base) == 438
    entries = {'historical/' + base.name:base.read_bytes()}
    folder = ROOT / 'deliverables/reports/amazon-v5-2026-11-10'
    for file in sorted(folder.iterdir()):
        if file.is_file() and file.suffix in ('.json','.png','.lta'):
            assert not file.is_symlink() and file.resolve().is_relative_to(ROOT)
            entries[file.relative_to(ROOT).as_posix()] = file.read_bytes()
    for path in ('docs/AMAZON_V5_LAT_RELEASE_REVIEW_2026-11-10.md','docs/AMAZON_LAT_STATUS.md',
                 'docs/PRIVACY_POLICY.md','docs/PRIVACY_DATA_MAP.md','docs/KNOWN_LIMITATIONS.md',
                 'docs/RELEASE_READINESS.md','docs/TEST_REPORT.md','docs/AMAZON_OWNER_ACTIONS.md',
                 'docs/AMAZON_V5_REVIEWER_INSTRUCTIONS.txt',
                 'docs/AMAZON_V5_STORE_COPY_EN_US.md','scripts/inspect_installed_amazon.py',
                 'deliverables/DELIVERABLES_MANIFEST.csv'):
        entries[path] = (ROOT/path).read_bytes()
    status = json.loads(entries['deliverables/reports/amazon-v5-2026-11-10/lat-status.json'])
    assert status['amazonStatus'] == 'TEST_IN_PROGRESS' and status['uploadVersionCode'] == 5
    assert status['uploadSha256'] == '6d0f548a91642de13d92a58e5e59de9b5ac61a950d6795187381fabc493ed582'
    entries['READ-ME-FIRST.txt'] = (
        b'VERSION 5 IS LIVE ON AMAZON TEST 1. PUBLIC SUBMISSION REMAINS BLOCKED.\n'
        b'Amazon-installed version 5 passed the scoped device checks recorded in device-checks.json.\n'
        b'Read docs/AMAZON_V5_LAT_RELEASE_REVIEW_2026-11-10.md first.\n'
        b'The nested local-QA archive retains its original bytes and historical evidence.\n'
        b'No new purchase or public app submission was performed.\n'
    )
    entries['manifest.json'] = encoded({'releaseStatus':'BLOCKED','files':[
        {'path':path,'bytes':len(data),'sha256':sha(data)} for path,data in sorted(entries.items())]})
    with zipfile.ZipFile(PACKAGE,'w') as archive:
        for path,data in sorted(entries.items()):
            archive.writestr(path,data,compress_type=zipfile.ZIP_STORED if path.startswith('historical/') else zipfile.ZIP_DEFLATED)
    index = {'path':PACKAGE.relative_to(ROOT).as_posix(),'sha256':sha(PACKAGE.read_bytes()),
             'bytes':PACKAGE.stat().st_size,'entriesVerified':check_bundle(PACKAGE),'releaseStatus':'BLOCKED',
             'amazonTestStatus':'V5_TEST_IN_PROGRESS','deviceStatus':status['deviceVerification'],
             'installedVersionCode':status['installedVersionCode'],'publicDraftVersionCode':status['publicDraftVersionCode']}
    INDEX.write_bytes(encoded(index))
    print(json.dumps(index))

if __name__ == '__main__': main()
