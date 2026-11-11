"""Package the verified v7 binary and explicitly selected release evidence."""
import json
import zipfile
from prepare_amazon_submission import ROOT, OUT, check_bundle, encoded, git, sha

REPORTS = ROOT / 'deliverables/reports/release-v7-2026-11-11'
APK = OUT / 'LifeTalea-0.1.0-public-v7-unsigned.apk'
PACKAGE = OUT / 'LifeTalea-v7-security-review-2026-11-11.zip'
INDEX = OUT / 'release-v7-security-index.json'


def main():
    if PACKAGE.exists() or INDEX.exists():
        raise FileExistsError('Version 7 review archive already exists')
    inspection = json.loads((REPORTS / 'final-candidate-inspection.json').read_bytes())
    if inspection['versionCode'] != 7 or sha(APK.read_bytes()) != inspection['sha256']:
        raise ValueError('Candidate APK does not match version 7 inspection')
    files = [
        APK, ROOT / 'docs/AMAZON_V7_REVIEWER_INSTRUCTIONS.txt',
        ROOT / 'docs/PRIVACY_POLICY.md', ROOT / 'docs/AMAZON_SUPABASE_DEPLOYMENT.md',
        REPORTS / 'final-candidate-inspection.json', REPORTS / 'final-build.log',
        REPORTS / 'final-backup-tests.log', REPORTS / 'final-qa-apk-hashes.json',
        REPORTS / 'receipt-verifier-smoke.json', REPORTS / 'release-status.json',
    ]
    entries = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in files}
    entries['README.txt'] = (
        b'LifeTalea version 7 security review package\n'
        b'See release-status.json for verified checks and the remaining release work.\n'
        b'The APK is unsigned for Amazon processing. Public submission remains pending.\n'
    )
    revision = git('rev-parse', 'HEAD')
    entries['manifest.json'] = encoded({
        'releaseStatus': 'BLOCKED', 'sourceCommit': revision,
        'files': [
            {'path': name, 'bytes': len(data), 'sha256': sha(data)}
            for name, data in sorted(entries.items())
        ],
    })
    with zipfile.ZipFile(PACKAGE, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            archive.writestr(name, data)
    index = {
        'path': PACKAGE.relative_to(ROOT).as_posix(), 'sha256': sha(PACKAGE.read_bytes()),
        'bytes': PACKAGE.stat().st_size, 'entriesVerified': check_bundle(PACKAGE),
        'sourceCommit': revision, 'candidateVersionCode': 7, 'publicSubmissionMade': False,
    }
    INDEX.write_bytes(encoded(index))
    print(json.dumps(index))


if __name__ == '__main__':
    main()
