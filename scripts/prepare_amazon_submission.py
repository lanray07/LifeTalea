"""Package current local evidence without regenerating metadata or approving release gates.

Run only after build, device/capture and validator checks. --check verifies the existing
bundle independently. No console writes, secrets, signing or publication occur here.
"""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import argparse, hashlib, json, re, subprocess, zipfile
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/amazon-submission'
NAME = 'LifeTalea-0.1.0-Amazon-RVS-review-2026-11-03.zip'
BUILD = 'deliverables/android/build-logs/amazon-rvs-build.log'
SERVER_FILES = ['package.json','Dockerfile','.dockerignore','.env.example','README.md','src/main.mjs','src/http.mjs','src/verifier.mjs','scripts/generate-signing-key.mjs','test/verifier.test.mjs','test/export-contract-fixture.mjs']
SERVER_NAME = 'LifeTalea-Amazon-RVS-server-2026-11-03.zip'

def sha(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
def encoded(value): return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
def git(*args):
    return subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}', *args], cwd=ROOT, text=True).strip()

def check_bundle(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate ZIP paths'
        for name in names:
            parts = PurePosixPath(name)
            assert not parts.is_absolute() and '..' not in parts.parts and '\\' not in name, name
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['releaseStatus'] == 'BLOCKED'
        assert set(names) == {row['path'] for row in manifest['files']} | {'manifest.json'}
        for row in manifest['files']:
            data = archive.read(row['path'])
            assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
    return len(names)

def server_package():
    payload = {}
    for name in SERVER_FILES:
        path = ROOT / f'server/receipt-verifier/{name}'
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT)
        payload[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    template = payload['server/receipt-verifier/.env.example'].decode('utf-8')
    for key in ['AMAZON_SHARED_SECRET','RVS_SIGNING_PRIVATE_KEY_FILE','RVS_SIGNING_PRIVATE_KEY_PEM_B64']:
        assert re.search(rf'^{key}=\s*$',template,re.M), 'Never fill the tracked env template with secrets'
    payload['android/app/src/androidTest/assets/rvs-contract.json'] = (ROOT/'android/app/src/androidTest/assets/rvs-contract.json').read_bytes()
    payload['READ-ME-FIRST.txt'] = b'LOCAL DEPLOYMENT CANDIDATE; NOT DEPLOYED OR LIVE-AMAZON-VERIFIED.\nRead server/receipt-verifier/README.md. Node 24, private server secrets and trusted HTTPS are required.\nRun: node --test server/receipt-verifier/test/verifier.test.mjs\nNo production private keys or real purchase receipts are included.\n'
    payload['manifest.json'] = encoded({'releaseStatus':'BLOCKED','files':[{'path':name,'bytes':len(data),'sha256':sha(data)} for name,data in sorted(payload.items())]})
    archive_path = OUT/SERVER_NAME
    with zipfile.ZipFile(archive_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(payload.items()): archive.writestr(name,data)
    count=check_bundle(archive_path)
    # Extract only our path/byte-verified archive. Verify the temporary cleanup target first.
    with tempfile.TemporaryDirectory(prefix='server-bundle-check-',dir=OUT) as temporary:
        assert Path(temporary).resolve().parent == OUT.resolve()
        with zipfile.ZipFile(archive_path) as archive: archive.extractall(temporary)
        result=subprocess.run(['node','--test','--test-reporter=tap','server/receipt-verifier/test/verifier.test.mjs'],cwd=temporary,capture_output=True,timeout=60)
        (ROOT/'deliverables/android/build-logs/amazon-rvs-deployment-smoke.log').write_bytes(result.stdout+result.stderr)
        assert result.returncode == 0, 'Standalone deployment ZIP self-test failed'
    return {'path':archive_path.relative_to(ROOT).as_posix(),'sha256':sha(archive_path.read_bytes()),'bytes':archive_path.stat().st_size,'entriesVerified':count,'extractedSelfTests':'PASS','deployed':False}

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); parser.add_argument('--allow-incomplete-ui', action='store_true'); args = parser.parse_args()
    package = OUT / NAME
    if args.check:
        index = read('deliverables/amazon-submission/package-index.json')
        assert sha(package.read_bytes()) == index['sha256'], 'Package checksum mismatch'
        if index.get('serverPackage'):
            server=ROOT/index['serverPackage']['path'];assert sha(server.read_bytes())==index['serverPackage']['sha256'];check_bundle(server)
        print(f'{check_bundle(package)} bundle entries verified; release remains BLOCKED'); return
    build = (ROOT / BUILD).read_text(encoding='utf-8', errors='replace')
    assert 'BUILD SUCCESSFUL' in build and 'BUILD FAILED' not in build, 'Complete the current Android build first'
    apk = ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk'
    test_apk = ROOT / 'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
    release = ROOT / 'android/app/build/outputs/apk/release/app-release-unsigned.apk'
    run = read('deliverables/reports/device-test-run.json')
    assert run['debugApkSha256'] == sha(apk.read_bytes()), 'Device evidence must match the current app'
    ui_complete = run['status'] == 'PASS' and run['testApkSha256'] == sha(test_apk.read_bytes())
    assert ui_complete or args.allow_incomplete_ui, 'Rerun physical QA on the current APKs'
    native = (ROOT / 'deliverables/android/build-logs/instrumentation.log').read_text(encoding='utf-8')
    device_count = re.search(r'OK \((\d+) tests?\)', native)
    assert (device_count and 'FAILURES!!!' not in native) or args.allow_incomplete_ui
    device_passed = int(device_count.group(1)) if ui_complete else len(re.findall(r'^INSTRUMENTATION_STATUS_CODE: 0$',native,re.M))
    units = [ET.parse(path).getroot() for path in sorted((ROOT / 'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml'))]
    assert units and all(int(s.get('failures', 0)) == int(s.get('errors', 0)) == int(s.get('skipped', 0)) == 0 for s in units)
    unit_count = sum(int(s.get('tests', 0)) for s in units)
    coverage = read('deliverables/localization/coverage.json')
    assert len(coverage) == 22 and all(row['coverage'] == 100 and not row['issues'] for row in coverage)
    for report in ['deliverables/localization/collateral-validation.json', 'deliverables/reports/static-checks.json', 'deliverables/reports/website-checks.json']:
        assert read(report)['status'] == 'PASS', report
    captures = read('deliverables/store-assets/screenshots/localized-drafts/provenance.json') if ui_complete else {'assets':[]}
    if ui_complete: assert captures['debugApkSha256'] == run['debugApkSha256'] and len(captures['assets']) == 176, 'Refresh screenshot compositions on this APK'
    for row in captures['assets']:
        assert sha((ROOT / row['asset']).read_bytes()) == row['sha256']
        assert sha((ROOT / row['actualCapture']).read_bytes()) == row['captureSha256']
    inspection = read('deliverables/reports/amazon-release-apk-inspection.json')
    assert inspection['sha256'] == sha(release.read_bytes()) and inspection['package'] == 'com.lifetalea.app'
    assert inspection['debuggable'] is False and inspection['minSdk'] == 26 and inspection['targetSdk'] == 35
    assert inspection['publicAuthenticationPemBundled'] is True
    assert inspection['publicAuthenticationPemSha256'] == sha((ROOT / 'android/app/src/main/assets/AppstoreAuthenticationKey.pem').read_bytes()), 'APK public key does not match the verified source'
    console = read('deliverables/reports/amazon-console-review.json')
    local_checks = read('deliverables/reports/amazon-local-checks.json')
    assert local_checks['status'] == 'PASS' and all(row['exitCode'] == 0 for row in local_checks['checks'])
    assert any(row['check'] == 'amazon-rvs-server' and row['exitCode'] == 0 for row in local_checks['checks'])
    rvs = read('deliverables/reports/amazon-rvs-verification.json')
    assert rvs['debugApkSha256'] == run['debugApkSha256'] and rvs['serverTests']['status'] == 'PASS'
    assert rvs['testApkSha256'] == sha(test_apk.read_bytes()) and rvs['uiChecksComplete'] == ui_complete
    assert console['appId'] == 'amzn1.devportal.mobileapp.035a0c55782f4cd68dd2453e79fd420e'
    assert inspection['publicAuthenticationPemSha256'] == console['publicKeySha256'], 'Public key provenance changed'
    assert len((ROOT / 'docs/AMAZON_TESTING_INSTRUCTIONS.txt').read_text(encoding='utf-8')) <= 4000
    layout = read('deliverables/reports/device-evidence/layout-smoke/result.json')
    layout_current = layout.get('status') == 'PASS' and layout.get('debugApkSha256') == run['debugApkSha256'] and layout.get('originalSettingsRestored') is True
    assert layout_current or args.allow_incomplete_ui, 'Complete the current device layout smoke and restore its settings'
    assert not ui_complete or layout_current, 'Complete the full batch before generating a passing UI package'
    audit = {
        'releaseStatus': 'BLOCKED', 'packagePurpose': 'LOCAL_REVIEW_ONLY_NOT_FOR_SUBMISSION',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'baseCommit': git('rev-parse', 'HEAD'), 'workingTreeDirty': bool(git('status', '--porcelain')),
        'publisher': 'O.Bankole', 'supportEmail': 'banksmi@mail.com',
        'package': 'com.lifetalea.app', 'versionName': '0.1.0', 'versionCode': 1,
        'candidateSha256': sha(release.read_bytes()), 'signing': 'UNSIGNED; Amazon distribution signing/update identity unverified',
        'kotlinUnitTestsPassed': unit_count, 'physicalDeviceTestsPassed': device_passed,
        'uiChecksComplete': ui_complete,
        'currentTestApkSha256': sha(test_apk.read_bytes()),
        'currentTestApkExecuted': run['testApkSha256'] == sha(test_apk.read_bytes()),
        'deviceRun': run, 'deviceScope': 'KFTRWI / Fire HD 10 (2021) / Fire OS 7 / API 28 / landscape',
        'appDraftLocales': 22, 'appKeysPerLocale': 191, 'nativeReleaseApprovals': 0,
        'screenshotDrafts': len(captures['assets']), 'screenshotSource': 'Current debug APK, one physical tablet; release screenshot approval pending' if ui_complete else 'OMITTED: fresh full locale run and capture validation required',
        'productionBilling': 'IMPLEMENTED_LOCALLY_NOT_CONFIGURED: signed server RVS and Android client; endpoint/pin unset and purchases off in default build. Deployment, real credentials, IAP product/prices and live Amazon transaction tests remain required.',
        'receiptVerification': rvs,
        'transcription': 'UNCONFIGURED; manual editing only',
        'formalSecurityScan': 'STARTUP_FAILED; no independent scan completed; static pattern checks are narrower evidence',
        'console': console,
        'layoutSmoke': layout if layout_current else {'status':'NOT_VERIFIED_ON_CURRENT_APP'},
        'localChecks': local_checks,
        'fullAcceptanceChecklist': 'Historical 258-statement report retained; no updated verified percentage claimed',
        'remainingGates': 'See docs/AMAZON_OWNER_ACTIONS.md; account configuration alone will not clear engineering/QA gates',
    }
    source_paths = sorted(path for path in (ROOT / 'android/app/src').rglob('*') if path.is_file()) + [ROOT / p for p in ['android/app/build.gradle.kts', 'android/build.gradle.kts', 'android/settings.gradle.kts', 'android/gradle.properties', 'android/gradle/wrapper/gradle-wrapper.properties']]
    source_hashes = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in source_paths}
    audit['androidSourceFingerprint'] = sha(encoded(source_hashes))
    audit['androidSourceFingerprintMethod'] = 'SHA-256 of the encoded per-file working-tree byte hashes, including local line endings; not a cross-platform reproducible-build claim.'
    server_hashes = {f'server/receipt-verifier/{name}': sha((ROOT/f'server/receipt-verifier/{name}').read_bytes()) for name in SERVER_FILES}
    audit['serverSourceFingerprint'] = sha(encoded(server_hashes))
    OUT.mkdir(parents=True, exist_ok=True)
    deployment = server_package()
    audit['serverDeploymentPackage'] = deployment
    (OUT / 'audit.json').write_bytes(encoded(audit))
    entries = {}
    def add(source, target=None):
        path = ROOT / source
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT), source
        name = target or source
        assert name not in entries and not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
        assert path.suffix.lower() not in {'.pem', '.jks', '.keystore'} and (not path.name.startswith('.env') or source == 'server/receipt-verifier/.env.example'), source
        entries[name] = path.read_bytes()
    add(str(release.relative_to(ROOT)).replace('\\', '/'), 'candidate-binary/LifeTalea-0.1.0-release-unsigned.apk')
    add(str(apk.relative_to(ROOT)).replace('\\', '/'), 'qa-only/LifeTalea-0.1.0-debug.apk')
    for filename in ['AMAZON_RELEASE_AUDIT.md', 'AMAZON_OWNER_ACTIONS.md', 'AMAZON_PUBLIC_KEY.md', 'AMAZON_TESTING_INSTRUCTIONS.txt', 'AMAZON_DRAFT_STATUS.md', 'AMAZON_SUBMISSION.md', 'RELEASE_READINESS.md', 'TEST_REPORT.md', 'KNOWN_LIMITATIONS.md', 'BUILD_AND_RELEASE.md', 'BACKUP_AND_RESTORE.md', 'MONETIZATION.md', 'PRIVACY_POLICY.md', 'PRIVACY_AND_SECURITY.md', 'SUPPORT.md', 'TRANSCRIPTION.md', 'TRANSLATION_POLISH.md', 'VOICE_COMPATIBILITY.md', 'LOCALIZATION.md', 'ARCHITECTURE.md']:
        add(f'docs/{filename}')
    add('deliverables/amazon-submission/audit.json', 'audit.json')
    for name in SERVER_FILES: add(f'server/receipt-verifier/{name}')
    add(deployment['path'], 'server-deployment/'+SERVER_NAME)
    add('android/app/src/androidTest/assets/rvs-contract.json')
    add('docs/AMAZON_RVS_IMPLEMENTATION.md')
    for filename in ['app-icon-114.png', 'app-icon-512.png']:
        add(f'deliverables/brand-assets/{filename}', f'listing-assets/icons/{filename}')
    for locale in [row['locale'] for row in coverage]:
        add(f'deliverables/store-assets/metadata/{locale}/listing.json', f'listing-drafts/{locale}/listing.json')
    add('deliverables/store-assets/metadata/REQUIREMENTS.json', 'listing-drafts/REQUIREMENTS.json')
    add('deliverables/store-assets/metadata/en-GB/screenshot-headlines.json', 'listing-drafts/en-GB/screenshot-headlines.json')
    add('deliverables/store-assets/metadata/iap-product-draft.json', 'listing-drafts/iap-product-draft.json')
    package_captures = json.loads(json.dumps(captures))
    for row in package_captures['assets']:
        source_asset, source_capture = row['asset'], row['actualCapture']
        row['asset'] = f'screenshot-drafts/{row["locale"]}/{row["shot"]}.jpg'
        row['actualCapture'] = f'evidence/original-captures/{row["locale"]}-{row["shot"]}.png'
        row['repositoryAsset'], row['repositoryCapture'] = source_asset, source_capture
        add(source_asset, row['asset']); add(source_capture, row['actualCapture'])
    if ui_complete: entries['screenshot-drafts/provenance.json'] = encoded(package_captures)
    for path in sorted((ROOT / 'deliverables/reports/device-evidence/layout-smoke').glob('*')) if layout_current else []:
        if path.suffix in {'.png', '.xml', '.json'}:
            add(path.relative_to(ROOT).as_posix(), f'evidence/layout-smoke/{path.name}')
    if not ui_complete:
        for path in sorted((ROOT/'deliverables/reports/device-evidence/rvs-failed-localization').glob('*')):
            if path.suffix in {'.png','.json'}: add(path.relative_to(ROOT).as_posix(),f'evidence/failed-locale-run/{path.name}')
    for report in ['device-test-run.json', 'amazon-release-apk-inspection.json', 'amazon-console-review.json', 'amazon-local-checks.json', 'amazon-rvs-verification.json', 'static-checks.json', 'website-checks.json']:
        add(f'deliverables/reports/{report}', f'evidence/{report}')
    for report in ['coverage.json', 'collateral-validation.json']:
        add(f'deliverables/localization/{report}', f'evidence/localization/{report}')
    for path in sorted((ROOT / 'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml')):
        add(path.relative_to(ROOT).as_posix(), f'evidence/junit/{path.name}')
    for log in [BUILD, 'deliverables/android/build-logs/amazon-rvs-test-readiness-build.log', 'deliverables/android/build-logs/amazon-rvs-device-first-failed.log', 'deliverables/android/build-logs/amazon-rvs-device-navigation-failed.log', 'deliverables/android/build-logs/amazon-rvs-corrected-device-batch.log', 'deliverables/android/build-logs/amazon-rvs-screenshot-provenance-check.log', 'deliverables/android/build-logs/instrumentation.log', 'deliverables/android/build-logs/amazon-audit-python-tests.log', 'deliverables/android/build-logs/amazon-audit-device-first-failed.log', 'deliverables/android/build-logs/amazon-audit-journey-isolated.log']:
        add(log, f'evidence/logs/{Path(log).name}')
    for row in local_checks['checks']:
        name = f'evidence/logs/{Path(row["log"]).name}'
        if name not in entries: add(row['log'], name)
    entries['READ-ME-FIRST.txt'] = b'BLOCKED - LOCAL REVIEW PACKAGE ONLY\nDo not upload QA APK or draft screenshots.\nRead audit.json and docs/AMAZON_OWNER_ACTIONS.md.\nEnglish candidate binary is unsigned; 22-locale screenshots are debug drafts, not approved release assets.\nNo Amazon console changes or submission were made.\n'
    if not ui_complete:
        entries['READ-ME-FIRST.txt'] = b'BLOCKED - PARTIAL LOCAL REVIEW PACKAGE; UI QA INCOMPLETE\nRead audit.json and docs/RELEASE_READINESS.md. The last device run failed a locale UI test.\nThe subsequent test-only fix has not been executed; current screenshots and layout certification are omitted.\nThe candidate is unsigned and billing is not configured. No deployment or Amazon submission occurred.\n'
    entries['evidence/android-source-hashes.json'] = encoded(source_hashes)
    entries['evidence/server-source-hashes.json'] = encoded(server_hashes)
    add('deliverables/android/build-logs/amazon-rvs-deployment-smoke.log','evidence/logs/amazon-rvs-deployment-smoke.log')
    manifest = {'releaseStatus': 'BLOCKED', 'files': [{'path': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(entries.items())]}
    entries['manifest.json'] = encoded(manifest)
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 3, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    count = check_bundle(package)
    index = {'path': package.relative_to(ROOT).as_posix(), 'sha256': sha(package.read_bytes()), 'bytes': package.stat().st_size, 'entriesVerified': count, 'releaseStatus': 'BLOCKED','serverPackage':deployment}
    (OUT / 'package-index.json').write_bytes(encoded(index))
    print(json.dumps(index))

if __name__ == '__main__': main()
