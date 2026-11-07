"""Retain this dated development QA run without replacing Amazon APK provenance."""
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone

from prepare_amazon_submission import ROOT, OUT, sha, encoded, check_bundle


def main():
    folder = ROOT / 'deliverables/reports/release-2026-11-07'
    report = json.loads((folder / 'green/device-test-run.json').read_bytes())
    assert report['status'] == 'PASS' and report['testSelection'] == 'all'
    instrument = (folder / 'green/instrumentation.log').read_text()
    tests = int(re.search(r'OK \((\d+) tests\)', instrument)[1])
    assert tests >= 18
    build = ROOT / 'android/app/build/localLatQa/release-checks-2026-11-07.log'
    assert 'BUILD SUCCESSFUL' in build.read_text()
    shutil.copyfile(build, folder / 'build.log')
    payload = {}

    def add(path):
        source = ROOT / path
        assert source.resolve().is_relative_to(ROOT) and not source.is_symlink()
        assert path not in payload
        payload[path] = source.read_bytes()

    for variant, expected in [('debug/app-debug.apk', report['debugApkSha256']),
                              ('androidTest/debug/app-debug-androidTest.apk', report['testApkSha256'])]:
        path = f'android/app/build/outputs/apk/{variant}'
        add(path)
        assert sha(payload[path]) == expected
    for evidence in report['evidence']:
        assert evidence['path'].startswith('deliverables/reports/release-2026-11-07/green/device-evidence/')
        add(evidence['path'])
        assert sha(payload[evidence['path']]) == evidence['sha256']
    for name in ('green/device-test-run.json', 'green/instrumentation.log', 'build.log',
                 'red-confirmed/device-test-run.json', 'red-confirmed/instrumentation.log',
                 'development-apk-inspection.json', 'device-session.json'):
        add(f'deliverables/reports/release-2026-11-07/{name}')
    session = json.loads((folder / 'device-session.json').read_bytes())
    assert session['power']['originalStayAwakeWhilePluggedIn'] == '0'
    assert session['power']['restored'] and session['sdkModeUnchanged']
    unit = {'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
    for xml in sorted((ROOT / 'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml')):
        root = ET.parse(xml).getroot()
        for key in unit:
            unit[key] += int(root.attrib.get(key, 0))
        add(xml.relative_to(ROOT).as_posix())
    assert unit['tests'] >= 21 and not any(unit[key] for key in ('failures', 'errors', 'skipped'))
    lint_path = 'android/app/build/reports/lint-results-debug.xml'
    lint = ET.parse(ROOT / lint_path).getroot()
    lint_counts = {severity: sum(issue.attrib.get('severity') == severity for issue in lint)
                   for severity in ('Fatal', 'Error', 'Warning', 'Information')}
    assert lint_counts['Fatal'] == lint_counts['Error'] == 0
    add(lint_path)
    for name in ('LifeApp.kt',):
        add(f'android/app/src/main/java/com/lifetalea/app/ui/{name}')
    add('android/app/src/androidTest/java/com/lifetalea/app/JourneyTest.kt')
    proof = ROOT / 'deliverables/reports/device-evidence/master-prompt'
    for name in ('prompt-cancel-search-preserved', 'prompt-navigation-search-preserved'):
        source = folder / f'green/device-evidence/screenshots/en-GB/{name}.png'
        shutil.copyfile(source, proof / f'{name}-2026-11-07.png')
    walkthrough = []
    for image in sorted(proof.glob('*.png')):
        path = image.relative_to(ROOT).as_posix()
        add(path)
        walkthrough.append({'path': path, 'sha256': sha(payload[path]),
                            'capturedDate': '2026-11-07' if '2026-11-07' in image.name else '2026-11-05'})
    payload['READ-ME-FIRST.txt'] = (
        b'DEVELOPMENT DEBUG QA ONLY. NOT AN AMAZON UPLOAD.\n'
        b'The public version 3 artifact and its Amazon test evidence are separate.\n'
        b'Full physical instrumentation passed after a reproduced search-state defect.\n'
        b'No raw microphone audio, real receipts, account credentials or server secrets included.\n'
    )
    payload['manifest.json'] = encoded({'releaseStatus': 'BLOCKED', 'files': [
        {'path': path, 'bytes': len(data), 'sha256': sha(data)} for path, data in sorted(payload.items())]})
    archive = OUT / 'LifeTalea-development-Fire-QA-2026-11-07.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path, data in sorted(payload.items()):
            bundle.writestr(path, data)
    checks = {
        'recordedAt': datetime.now(timezone.utc).isoformat(), 'releaseStatus': 'BLOCKED',
        'scope': 'Development source checks; public Amazon version 3 remains unchanged',
        'deviceSuite': {'status': 'PASS', 'tests': tests, 'device': 'Fire HD 10 (2021), API 28',
                        'report': 'deliverables/reports/release-2026-11-07/green/device-test-run.json'},
        'unitTests': unit, 'lint': lint_counts, 'verifierTests': {'passed': 23, 'failed': 0},
        'collateralChecks': {'localeKeys': 191, 'completeDraftLocales': 22, 'releaseApprovedLocales': 0,
                             'websiteReviewGateCasesPassed': 6, 'staticExportRegression': 'PASS'},
        'regression': {'beforeFix': 'FAIL: prompted draft replaced orchard search', 'afterFix': 'PASS',
                       'coverage': ['Cancel', 'direct navigation to Memories', 'next blank draft']},
        'debugApkSha256': report['debugApkSha256'], 'testApkSha256': report['testApkSha256'],
        'qaArchive': {'path': archive.relative_to(ROOT).as_posix(), 'sha256': sha(archive.read_bytes()),
                      'bytes': archive.stat().st_size, 'entriesVerified': check_bundle(archive)},
        'walkthroughEvidence': walkthrough,
        'amazonConsoleObserved': {'date': '2026-11-07', 'test1': 'v3 Test in-progress',
                                  'publicDraft': 'v3 Ready to Submit; not submitted'},
        'limitations': ['No new Amazon purchase or public-channel test', 'No automatic transcription engine',
                       'No native locale approvals', 'Remaining master-prompt product, security, privacy and device gates'],
    }
    (folder / 'checks.json').write_bytes(encoded(checks))
    print(json.dumps({'deviceTests': tests, 'unitTests': unit, 'lint': lint_counts, 'qaArchive': checks['qaArchive']}))


if __name__ == '__main__':
    main()
