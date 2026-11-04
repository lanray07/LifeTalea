"""Inspect the actual release APK with Android SDK tools; no signing or uploading."""
from pathlib import Path
import hashlib, json, os, re, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'AppData/Local/Android/Sdk')))
APK = ROOT / 'android/app/build/outputs/apk/release/app-release-unsigned.apk'

def main():
    tools = SDK / 'build-tools/35.0.0'
    badging = subprocess.check_output([str(tools / ('aapt.exe' if os.name == 'nt' else 'aapt')), 'dump', 'badging', str(APK)], text=True, encoding='utf-8')
    identity = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", badging)
    assert identity, 'APK identity unavailable'
    signer = tools / ('apksigner.bat' if os.name == 'nt' else 'apksigner')
    signing = subprocess.run([str(signer), 'verify', str(APK)], capture_output=True, text=True)
    assert signing.returncode != 0 and 'DOES NOT VERIFY' in signing.stderr, 'Candidate signing state changed: review update identity'
    with zipfile.ZipFile(APK) as archive:
        test_fixture = any('rvs-contract.json' in name for name in archive.namelist())
        test_trust = any('local_billing_qa_ca' in name or 'local_billing_network_security' in name for name in archive.namelist())
        key_present = any(name.endswith('/AppstoreAuthenticationKey.pem') for name in archive.namelist())
        key_hash = hashlib.sha256(archive.read('assets/AppstoreAuthenticationKey.pem')).hexdigest() if key_present else None
    assert not test_fixture, 'Test-only receipt fixtures must never enter the release APK'
    assert not test_trust, 'Local sandbox TLS trust must never enter the release APK'
    manifest = subprocess.check_output([str(tools / ('aapt.exe' if os.name == 'nt' else 'aapt')), 'dump', 'xmltree', str(APK), 'AndroidManifest.xml'], text=True, encoding='utf-8')
    visibility = {name: name in manifest for name in ['com.amazon.venezia','com.amazon.sdktestclient']}
    assert all(visibility.values()), 'Amazon package visibility missing in the actual release manifest'
    config = (ROOT/'android/app/build/generated/source/buildConfig/release/com/lifetalea/app/BuildConfig.java').read_text(encoding='utf-8')
    def field(name): return re.search(rf'\b{name} = "([^"]*)";',config)[1]
    billing = {'endpointConfigured': bool(field('RVS_URL')), 'signingPublicKeyConfigured': bool(field('RVS_PUBLIC_KEY')), 'environment': field('RVS_ENVIRONMENT'), 'purchasesEnabled': bool(re.search(r'AMAZON_PURCHASES_ENABLED = true;',config))}
    report = {
        'sha256': hashlib.sha256(APK.read_bytes()).hexdigest(), 'package': identity[1], 'versionCode': int(identity[2]), 'versionName': identity[3],
        'minSdk': int(re.search(r"sdkVersion:'(\d+)'", badging)[1]), 'targetSdk': int(re.search(r"targetSdkVersion:'(\d+)'", badging)[1]),
        'debuggable': 'application-debuggable' in badging, 'publicAuthenticationPemBundled': key_present, 'publicAuthenticationPemSha256': key_hash,
        'signing': 'UNSIGNED / apksigner verify rejected the candidate as expected',
        'testReceiptFixtureBundled': test_fixture, 'amazonVisibilityNamesInApkManifest': visibility,
        'localSandboxTrustBundled': test_trust,
        'generatedReleaseBillingConfiguration': billing,
        'limitations': 'Badging and signing inspection do not verify runtime compatibility, Amazon DRM transformation or release approval.'
    }
    assert report['package'] == 'com.lifetalea.app' and report['versionCode'] == 1 and report['versionName'] == '0.1.0' and not report['debuggable']
    destination = ROOT / 'deliverables/reports/amazon-release-apk-inspection.json'
    destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__': main()
