"""Add current device evidence without rewriting the immutable v6 regression bundle."""
import argparse
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle, git

REPORTS = ROOT / 'deliverables/reports/release-v6-2026-11-10'
PACKAGE = OUT / 'LifeTalea-v6-device-review-2026-11-10.zip'
INDEX = OUT / 'release-v6-device-index.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        index = json.loads(INDEX.read_bytes())
        assert sha(PACKAGE.read_bytes()) == index['sha256']
        assert check_bundle(PACKAGE) == index['entriesVerified']
        print(json.dumps(index))
        return
    assert not PACKAGE.exists(), 'Retain existing review archives; choose a new dated package.'
    prior_index = json.loads((OUT / 'release-v6-regression-index.json').read_bytes())
    prior = ROOT / prior_index['path']
    assert sha(prior.read_bytes()) == prior_index['sha256']
    assert check_bundle(prior) == prior_index['entriesVerified']
    checks = json.loads((REPORTS / 'checks.json').read_bytes())
    assert checks['installedAmazonVersionCode'] == checks['amazonPublicDraftVersionCode'] == 6
    assert checks['releaseStatus'] == 'BLOCKED_PENDING_RELEASE_GATES'
    assert json.loads((REPORTS / 'scale-preservation/result.json').read_bytes())['status'] == 'PASS'
    entries = {}

    def add(path):
        assert path.is_file() and not path.is_symlink()
        assert path.resolve().is_relative_to(ROOT)
        entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()

    add(prior)
    add(OUT / 'release-v6-regression-index.json')
    for path in REPORTS.iterdir():
        if path.is_file() and path.suffix in ('.json', '.png', '.jpg', '.log'):
            add(path)
    for path in (REPORTS / 'scale-preservation').iterdir():
        if path.is_file():
            add(path)
    add(REPORTS / 'qa-artifacts/scale-test-harness.apk')
    for name in ('RELEASE_V6_REVIEW_2026-11-10.md', 'AMAZON_V6_REVIEWER_INSTRUCTIONS.txt',
                 'RELEASE_READINESS.md', 'KNOWN_LIMITATIONS.md', 'PRIVACY_DATA_MAP.md'):
        add(ROOT / 'docs' / name)
    for name in ('scripts/package_v6_device_review.py', 'scripts/run_scale_preservation_checks.py',
                 'android/app/src/androidTest/java/com/lifetalea/app/ScalePreservationTest.kt'):
        add(ROOT / name)
    entries['READ-ME-FIRST.txt'] = (
        b'VERSION 6 DEVICE REVIEW; PUBLIC SUBMISSION REMAINS BLOCKED.\n'
        b'Current root reports/docs supersede historical status text in the nested regression archive.\n'
        b'Amazon-distributed v6 installed in place; public draft contains v6 and 14 saved copy locales.\n'
        b'App-lock cancellation/unlock/disable passed through owner interaction and scoped observation.\n'
        b'Two focused scale tests passed; these do not replace the original full 26-test provenance.\n'
        b'Current localized public images, security/privacy and remaining runtime gates are still open.\n'
        b'No new payment, legal attestation or public submission occurred.\n'
        b'Amazon-processed APK, private credentials and real receipts are not redistributed.\n')
    revision = git('rev-parse', 'HEAD')
    entries['manifest.json'] = encoded({'releaseStatus': 'BLOCKED', 'sourceCommit': revision,
        'files': [{'path': p, 'bytes': len(data), 'sha256': sha(data)} for p, data in sorted(entries.items())]})
    with zipfile.ZipFile(PACKAGE, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in sorted(entries.items()):
            archive.writestr(path, data)
    index = {'path': PACKAGE.relative_to(ROOT).as_posix(), 'sha256': sha(PACKAGE.read_bytes()),
        'bytes': PACKAGE.stat().st_size, 'entriesVerified': check_bundle(PACKAGE),
        'sourceCommit': revision, 'releaseStatus': 'BLOCKED', 'candidateVersionCode': 6,
        'installedAmazonVersionCode': 6, 'amazonPublicDraftVersionCode': 6,
        'publicSubmissionMade': False, 'newPayments': 0, 'nestedRegressionSha256': prior_index['sha256']}
    INDEX.write_bytes(encoded(index))
    print(json.dumps(index))


if __name__ == '__main__':
    main()
