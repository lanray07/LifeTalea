"""Package the candidate and scoped QA; never promotes an unverified Amazon release."""
import argparse
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle

PACKAGE = OUT / 'LifeTalea-product-privacy-v5-2026-11-10.zip'
INDEX = OUT / 'product-privacy-v5-index.json'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    if options.check:
        index = json.loads(INDEX.read_bytes())
        assert sha(PACKAGE.read_bytes()) == index['sha256']
        assert check_bundle(PACKAGE) == index['entriesVerified']
        print(f"Verified {index['entriesVerified']} entries")
        return
    entries = {}
    def add(file):
        assert file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(ROOT)
        entries[file.relative_to(ROOT).as_posix()] = file.read_bytes()
    folder = ROOT / 'deliverables/reports/product-privacy-2026-11-10'
    for file in folder.rglob('*'):
        if file.is_file() and file.suffix in ('.json','.png','.log','.xml','.pdf','.apk'): add(file)
    for path in ('deliverables/amazon-submission/LifeTalea-0.1.0-public-v5-unsigned.apk',
                 'android/app/build/outputs/apk/debug/app-debug.apk',
                 'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk',
                 'docs/PRIVACY_POLICY.md', 'docs/PRIVACY_DATA_MAP.md',
                 'docs/PRODUCT_PRIVACY_RELEASE_REVIEW_2026-11-10.md',
                 'docs/KNOWN_LIMITATIONS.md', 'docs/RELEASE_READINESS.md', 'docs/TEST_REPORT.md',
                 'docs/AMAZON_V5_REVIEWER_INSTRUCTIONS.txt', 'docs/AMAZON_V5_STORE_COPY_EN_US.md',
                 'deliverables/DELIVERABLES_MANIFEST.csv',
                 'deliverables/reports/ACCEPTANCE_TEST_RESULTS.csv',
                 'deliverables/localization/coverage.json', 'deliverables/localization/collateral-validation.json'):
        add(ROOT / path)
    summary = json.loads(entries['deliverables/reports/product-privacy-2026-11-10/checks.json'])
    assert summary['releaseStatus'] == 'BLOCKED' and summary['candidateVersionCode'] == 5
    assert summary['combinedDeviceCasesCleared']
    session = json.loads(entries['deliverables/reports/product-privacy-2026-11-10/device-session.json'])
    assert session['power']['restored'] and session['sdkModeUnchanged']
    assert sha(entries['deliverables/amazon-submission/LifeTalea-0.1.0-public-v5-unsigned.apk']) == summary['candidateSha256']
    entries['READ-ME-FIRST.txt'] = (
        b'PUBLIC SUBMISSION BLOCKED. VERSION 5 IS A LOCAL UNSIGNED CANDIDATE ONLY.\n'
        b'Amazon Test 1 and the public draft remain version 4.\n'
        b'Read docs/PRODUCT_PRIVACY_RELEASE_REVIEW_2026-11-10.md for exact test scope and remaining gates.\n'
        b'The initial failed device batch is retained alongside the corrected test results.\n'
        b'No production secrets, payment or public submission are included.\n'
    )
    entries['manifest.json'] = encoded({'releaseStatus':'BLOCKED','files':[
        {'path':path,'bytes':len(data),'sha256':sha(data)} for path,data in sorted(entries.items())]})
    with zipfile.ZipFile(PACKAGE,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,data in sorted(entries.items()): archive.writestr(path,data)
    index = {'path':PACKAGE.relative_to(ROOT).as_posix(),'sha256':sha(PACKAGE.read_bytes()),
             'bytes':PACKAGE.stat().st_size,'entriesVerified':check_bundle(PACKAGE),
             'releaseStatus':'BLOCKED','candidateVersionCode':5,'amazonDraftVersionCode':4}
    INDEX.write_bytes(encoded(index))
    (OUT / 'review-update-index.json').write_bytes(encoded(index))
    print(json.dumps(index))

if __name__ == '__main__': main()
