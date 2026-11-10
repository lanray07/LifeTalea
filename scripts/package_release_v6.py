"""Package the v6 test candidate and dated evidence without claiming public readiness."""
import argparse
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle, git

PACKAGE=OUT/'LifeTalea-v6-review-2026-11-10.zip'
INDEX=OUT/'release-v6-index.json'
REPORTS=ROOT/'deliverables/reports/release-v6-2026-11-10'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true')
    parser.add_argument('--final-regression',action='store_true',help='Create a separate package after the final full QA run and screenshot validation.')
    args=parser.parse_args()
    package=OUT/'LifeTalea-v6-regression-review-2026-11-10.zip' if args.final_regression else PACKAGE
    index_file=OUT/'release-v6-regression-index.json' if args.final_regression else INDEX
    if args.check:
        index=json.loads(index_file.read_bytes())
        assert sha(package.read_bytes())==index['sha256']
        assert check_bundle(package)==index['entriesVerified']
        print(json.dumps(index));return
    if not args.final_regression:
        raise RuntimeError('The original v6 review archive is retained unchanged. Use --final-regression for updated evidence.')
    checks=json.loads((REPORTS/'checks.json').read_bytes())
    assert checks['candidateVersionCode']==6 and checks['releaseStatus']=='BLOCKED_PENDING_RELEASE_GATES'
    assert json.loads((REPORTS/'local-checks.json').read_bytes())['status']=='PASS'
    candidate=OUT/'LifeTalea-0.1.0-public-v6-unsigned.apk'
    assert sha(candidate.read_bytes())==checks['amazonCandidate']['sha256']
    entries={}
    def add(file):
        assert file.is_file() and not file.is_symlink() and file.resolve().is_relative_to(ROOT)
        entries[file.relative_to(ROOT).as_posix()]=file.read_bytes()
    add(candidate)
    for file in sorted(REPORTS.rglob('*')):
        if file.is_file() and file.suffix in ('.json','.png','.jpg','.log','.pdf','.xml','.apk'):add(file)
    for folder in ('localization','website/localization','website/src/dictionaries','deliverables/store-assets/metadata'):
        for file in sorted((ROOT/folder).glob('*.json') if folder!='deliverables/store-assets/metadata' else (ROOT/folder).glob('*/*.json')):
            if file.name not in ('local-cache.json','collateral-cache.json','cache.json'):add(file)
    for name in ('RELEASE_V6_REVIEW_2026-11-10.md','AMAZON_V6_REVIEWER_INSTRUCTIONS.txt','AMAZON_V6_STORE_COPY_EN_US.md',
                 'LOCALIZATION.md','PRIVACY_POLICY.md','PRIVACY_DATA_MAP.md','RELEASE_READINESS.md','KNOWN_LIMITATIONS.md','TEST_REPORT.md'):
        add(ROOT/'docs'/name)
    for name in ('coverage.json','collateral-validation.json','linguistic-flags.json'):
        add(ROOT/'deliverables/localization'/name)
    for name in ('product-v6-local.log','product-v6-website.log'):
        add(ROOT/'deliverables/android/build-logs'/name)
    add(ROOT/'deliverables/DELIVERABLES_MANIFEST.csv')
    add(ROOT/'scripts/package_release_v6.py')
    entries['READ-ME-FIRST.txt']=(
        b'VERSION 6 TEST CANDIDATE; PUBLIC SUBMISSION BLOCKED.\n'
        b'Read docs/RELEASE_V6_REVIEW_2026-11-10.md and the dated checks.json first.\n'
        b'AI editorial language approval is not native certification, device verification or legal approval.\n'
        b'Initial QA device suite passed 26 tests. The final English debug-overlay rebuild needs its own device retest.\n'
        b'Initial and rebuilt QA APKs have separate names and hashes; do not relabel their evidence.\n'
        b'The regular Amazon-distributed version 5 and public draft remain unchanged.\n'
        b'No new payment or public app submission occurred. Earlier v5 archives remain separate and unchanged.\n')
    if args.final_regression:
        run=json.loads((REPORTS/'device-final/device-test-run.json').read_bytes())
        assert run['status']=='PASS' and run['testSelection']=='all'
        assert run['debugApkSha256']==checks['finalDebugApkSha256']
        assets=ROOT/'deliverables/store-assets/screenshots/localized-v6'
        provenance=json.loads((assets/'provenance.json').read_bytes())
        assert provenance['debugApkSha256']==run['debugApkSha256'] and provenance['count']==176
        for file in sorted(assets.rglob('*')):
            if file.is_file() and file.suffix in ('.json','.csv','.html','.jpg'):add(file)
        entries['READ-ME-FIRST.txt']=(
            b'VERSION 6 QA REGRESSION REVIEW; PUBLIC SUBMISSION REMAINS BLOCKED.\n'
            b'The final QA APK passed the full 26-test physical batch. Locale screenshots are bound to that run.\n'
            b'This is not a successful app-lock authentication test or Amazon-distribution verification.\n'
            b'AI copy approval and automated screenshot validation do not establish complete visual/device/legal approval.\n'
            b'Read docs/RELEASE_V6_REVIEW_2026-11-10.md and current checks.json for remaining gates.\n'
            b'Amazon LAT version 6 is live; installed-Amazon verification is recorded separately. The public draft remains version 5.\n'
            b'No new payment or public app submission occurred. Earlier review archives remain unchanged.\n')
    revision=git('rev-parse','HEAD')
    entries['manifest.json']=encoded({'releaseStatus':'BLOCKED','sourceCommit':revision,'files':[{'path':p,'bytes':len(data),'sha256':sha(data)} for p,data in sorted(entries.items())]})
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for path,data in sorted(entries.items()):archive.writestr(path,data)
    index={'path':package.relative_to(ROOT).as_posix(),'sha256':sha(package.read_bytes()),'bytes':package.stat().st_size,
           'entriesVerified':check_bundle(package),'releaseStatus':'BLOCKED','candidateVersionCode':6,
           'amazonPublicDraftVersionCode':checks['amazonPublicDraftVersionCode'],'amazonLiveLatVersionCode':checks['amazonLatVersionCode'],
           'amazonLatDraftVersionCode':checks['amazonLatDraftVersionCode'],'amazonLatDraftSubmitted':checks['amazonLatDraftSubmitted'],
           'installedAmazonVersionCode':checks.get('installedAmazonVersionCode'),'sourceCommit':revision}
    index_file.write_bytes(encoded(index));print(json.dumps(index))

if __name__=='__main__':main()
