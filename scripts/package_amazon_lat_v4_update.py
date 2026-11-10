"""Add current LAT distribution evidence without rewriting historical review bytes."""
import argparse
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle

PACKAGE = OUT / 'LifeTalea-Amazon-LAT-v4-update-2026-11-10.zip'
INDEX = OUT / 'review-update-index.json'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        index = json.loads(INDEX.read_bytes())
        assert index['path'] == PACKAGE.relative_to(ROOT).as_posix()
        assert sha(PACKAGE.read_bytes()) == index['sha256']
        assert check_bundle(PACKAGE) == index['entriesVerified']
        print(f"Verified {index['entriesVerified']} entries")
        return
    previous = OUT / 'LifeTalea-Amazon-review-transcription-2026-11-07.zip'
    assert sha(previous.read_bytes()) == 'a2d8d873bb37d905ce55cdddd19f267cb210abb60d0a8f668bcd883ccc4363da'
    assert check_bundle(previous) == 58
    entries = {'historical/' + previous.name: previous.read_bytes()}
    for file in sorted((ROOT / 'deliverables/reports/release-2026-11-10').iterdir()):
        if file.is_file() and file.suffix in ('.json', '.png', '.lta'):
            assert not file.is_symlink() and file.resolve().is_relative_to(ROOT)
            entries[file.relative_to(ROOT).as_posix()] = file.read_bytes()
    for path in ('docs/AMAZON_RELEASE_REVIEW_2026-11-10.md', 'docs/AMAZON_LAT_STATUS.md',
                 'docs/MASTER_PROMPT_RELEASE_REVIEW.md', 'docs/KNOWN_LIMITATIONS.md',
                 'docs/RELEASE_READINESS.md', 'docs/TEST_REPORT.md',
                 'docs/AMAZON_V4_REVIEWER_INSTRUCTIONS.txt', 'docs/AMAZON_V4_STORE_COPY_EN_US.md',
                 'deliverables/reports/ACCEPTANCE_CRITERIA.md',
                 'deliverables/reports/ACCEPTANCE_TEST_RESULTS.csv',
                 'deliverables/localization/coverage.json',
                 'deliverables/localization/collateral-validation.json',
                 'deliverables/DELIVERABLES_MANIFEST.csv'):
        entries[path] = (ROOT / path).read_bytes()
    status = json.loads(entries['deliverables/reports/release-2026-11-10/amazon-v4-lat-status.json'])
    assert status['amazonStatus'] == 'TEST_IN_PROGRESS' and status['uploadVersionCode'] == 4
    assert status['installedVersionCode'] == 4 and status['v4DistributedBinaryInspected']
    for proof in status['evidence']:
        assert sha(entries[proof['path']]) == proof['sha256']
    session = json.loads(entries['deliverables/reports/release-2026-11-10/device-session.json'])
    assert session['power']['restored'] and session['sdkModeUnchanged']
    session = json.loads(entries['deliverables/reports/release-2026-11-10/device-session-v4-tests.json'])
    assert session['power']['restored'] and session['sdkModeUnchanged']
    entries['READ-ME-FIRST.txt'] = (
        b'VERSION 4 IS LIVE ON AMAZON TEST 1. PUBLIC SUBMISSION REMAINS BLOCKED.\n'
        b'Amazon v4 is installed: binary identity, fictional transcription and unpaid billing checks passed.\n'
        b'Only the three owner-approved QA apps were removed; the regular app was updated in place.\n'
        b'No payment was made. Remaining mandatory release gates are open.\n'
        b'Read docs/AMAZON_RELEASE_REVIEW_2026-11-10.md first.\n'
        b'The nested 7 November archive is historical and retains its original bytes.\n'
    )
    entries['manifest.json'] = encoded({'releaseStatus': 'BLOCKED', 'files': [
        {'path': path, 'bytes': len(data), 'sha256': sha(data)} for path, data in sorted(entries.items())]})
    with zipfile.ZipFile(PACKAGE, 'w') as archive:
        for path, data in sorted(entries.items()):
            archive.writestr(path, data, compress_type=zipfile.ZIP_STORED if path.startswith('historical/') else zipfile.ZIP_DEFLATED)
    index = {'path': PACKAGE.relative_to(ROOT).as_posix(), 'sha256': sha(PACKAGE.read_bytes()),
             'bytes': PACKAGE.stat().st_size, 'entriesVerified': check_bundle(PACKAGE),
             'releaseStatus': 'BLOCKED', 'amazonTestStatus': 'V4_TEST_IN_PROGRESS',
             'deviceStatus': 'V4_SCOPED_CHECKS_PASSED', 'publicDraftVersionCode': status['publicDraftVersionCode']}
    INDEX.write_bytes(encoded(index))
    print(json.dumps(index))

if __name__ == '__main__':
    main()
