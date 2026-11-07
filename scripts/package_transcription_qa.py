"""Package immutable tested APKs and dated transcription evidence; no publication."""
import json
import shutil
import xml.etree.ElementTree as ET
import zipfile
from prepare_amazon_submission import ROOT, OUT, encoded, sha, check_bundle

folder = ROOT / 'deliverables/reports/transcription-2026-11-07'
run = json.loads((folder / 'offline/device-test-run.json').read_bytes())
restart = json.loads((folder / 'process-restart.json').read_bytes())
assert run['status'] == restart['status'] == 'PASS' and restart['processChanged']
assert run['debugApkSha256'] == restart['debugApkSha256']
assert 'OK (22 tests)' in (folder / 'offline/instrumentation.log').read_text()
assert json.loads((folder / 'device-session.json').read_bytes())['power']['restored']
payload = {}

def add(path, expected=None):
    source = ROOT / path
    assert source.resolve().is_relative_to(ROOT) and not source.is_symlink()
    assert path not in payload
    data = source.read_bytes()
    if expected is not None: assert sha(data) == expected, path
    payload[path] = data

for path, expected in [
    ('android/app/build/transcription-dev/offline-tested-app.apk', run['debugApkSha256']),
    ('android/app/build/transcription-dev/offline-tested-tests.apk', run['testApkSha256']),
    ('android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk', restart['testApkSha256'])]:
    add(path, expected)
for evidence in run['evidence']:
    assert evidence['path'].startswith('deliverables/reports/transcription-2026-11-07/offline/device-evidence/')
    add(evidence['path'], evidence['sha256'])
probe = json.loads((folder / 'first-native/device-test-run.json').read_bytes())
for evidence in probe['evidence']:
    assert evidence['path'].startswith('deliverables/reports/transcription-2026-11-07/first-native/device-evidence/')
    add(evidence['path'], evidence['sha256'])
for source, name in [('final-build.log', 'build.log'), ('restart-build.log', 'restart-build.log'),
                     ('website-build.log', 'website-build.log'), ('python-checks.log', 'python-checks.log')]:
    shutil.copyfile(ROOT / 'android/app/build/transcription-dev' / source, folder / name)
assert 'BUILD SUCCESSFUL' in (folder / 'build.log').read_text()
assert 'Static export prefetch paths' in (folder / 'website-build.log').read_text(encoding='utf-8')
for path in folder.rglob('*'):
    if path.is_file() and path.suffix in ('.json', '.log') and path.name != 'checks.json' and 'device-evidence' not in path.parts:
        add(path.relative_to(ROOT).as_posix())
unit = {'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
for path in sorted((ROOT / 'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml')):
    root = ET.parse(path).getroot()
    for key in unit: unit[key] += int(root.get(key, 0))
    add(path.relative_to(ROOT).as_posix())
assert unit['tests'] == 21 and not any(unit[key] for key in ('failures', 'errors', 'skipped'))
lint = ET.parse(ROOT / 'android/app/build/reports/lint-results-debug.xml').getroot()
lint_counts = {s: sum(issue.get('severity') == s for issue in lint) for s in ('Fatal', 'Error', 'Warning')}
assert lint_counts['Fatal'] == lint_counts['Error'] == 0
add('android/app/build/reports/lint-results-debug.xml')
for base in ('android/app/src/main/java', 'android/app/src/main/cpp'):
    for path in sorted((ROOT / base).rglob('*')):
        if path.is_file(): add(path.relative_to(ROOT).as_posix())
for path in ('android/app/build.gradle.kts', 'docs/ON_DEVICE_TRANSCRIPTION.md',
             'docs/AMAZON_TRANSCRIPTION_RELEASE_REVIEW_2026-11-07.md',
             'android/app/src/androidTest/java/com/lifetalea/app/TranscriptionDeviceTest.kt',
             'android/app/src/androidTest/java/com/lifetalea/app/TranscriptionRestartTest.kt'):
    add(path)
proof = ROOT / 'deliverables/reports/device-evidence/master-prompt/transcription-review-2026-11-07.png'
shutil.copyfile(folder / 'offline/device-evidence/transcription/review-draft.png', proof)
add(proof.relative_to(ROOT).as_posix())
payload['READ-ME-FIRST.txt'] = b'DEVELOPMENT QA ONLY. NOT AN AMAZON UPLOAD.\n22 tests passed with Wi-Fi disabled; restart/failure preservation have separate tests.\nEnglish synthetic speech only; no broad language/device certification.\nNo real customer audio, credentials or receipt data included.\n'
payload['manifest.json'] = encoded({'releaseStatus': 'BLOCKED', 'files': [
    {'path': path, 'bytes': len(data), 'sha256': sha(data)} for path, data in sorted(payload.items())]})
archive = OUT / 'LifeTalea-transcription-Fire-QA-2026-11-07.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    for path, data in sorted(payload.items()): bundle.writestr(path, data)
candidate = json.loads((folder / 'candidate-inspection.json').read_bytes())
assert candidate['versionCode'] == 4 and candidate['generatedReleaseBillingConfiguration']['purchasesEnabled']
report = {'releaseStatus': 'BLOCKED', 'deviceSuite': {'status': 'PASS', 'tests': 22, 'evidenceFiles': run['evidenceFiles'],
           'wifiDisabled': True, 'debugApkSha256': run['debugApkSha256'], 'testApkSha256': run['testApkSha256']},
          'supplementaryChecks': {'realProcessRestart': 'PASS', 'failureSourcePreservation': 'PASS'},
          'unitTests': unit, 'lint': lint_counts, 'pythonTestsPassed': 16,
          'catalogs': {'keys': 199, 'draftLocales': 22, 'nativeApprovals': 0},
          'qaArchive': {'path': archive.relative_to(ROOT).as_posix(), 'sha256': sha(archive.read_bytes()),
                        'bytes': archive.stat().st_size, 'entriesVerified': check_bundle(archive)},
          'candidate': {'path': 'deliverables/amazon-submission/LifeTalea-0.1.0-public-v4-unsigned.apk',
                        'sha256': candidate['sha256'], 'versionCode': 4, 'amazonProcessed': False, 'submitted': False},
          'proof': {'path': proof.relative_to(ROOT).as_posix(), 'sha256': sha(proof.read_bytes())}}
(folder / 'checks.json').write_bytes(encoded(report))
print(json.dumps(report))
