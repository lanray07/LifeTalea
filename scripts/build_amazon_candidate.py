"""Build the next public candidate with public verifier configuration; never uploads."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import argparse

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, default=5)
    parser.add_argument('--report-dir', default='deliverables/reports/product-privacy-2026-11-10')
    parser.add_argument('--with-device-tests', action='store_true')
    options = parser.parse_args()
    folder = (ROOT / options.report_dir).resolve()
    assert folder.is_relative_to(ROOT) and options.version > 4, 'Preserve historical candidate artifacts'
    folder.mkdir(parents=True, exist_ok=True)
    pin = json.loads((ROOT / 'server/receipt-verifier/supabase/public-signing-key.json').read_text())['publicKeySpkiBase64']
    binary = 'java.exe' if os.name == 'nt' else 'java'
    java = str(Path(os.environ['JAVA_HOME']) / 'bin' / binary) if os.environ.get('JAVA_HOME') else shutil.which('java')
    args = [java, '-classpath', str(ROOT / 'android/gradle/wrapper/gradle-wrapper.jar'),
            'org.gradle.wrapper.GradleWrapperMain', '-p', 'android', '--no-daemon', ':app:assembleRelease',
            '-PlifetaleaPurchasesEnabled=true',
            '-PlifetaleaRvsUrl=https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify',
            '-PlifetaleaRvsPublicKey=' + pin]
    if options.with_device_tests: args.extend([':app:assembleDebug', ':app:assembleDebugAndroidTest'])
    with (folder / 'candidate-build.log').open('w', encoding='utf-8') as log:
        subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    apk = ROOT / 'android/app/build/outputs/apk/release/app-release-unsigned.apk'
    output = ROOT / f'deliverables/amazon-submission/LifeTalea-0.1.0-public-v{options.version}-unsigned.apk'
    shutil.copyfile(apk, output)
    subprocess.run([shutil.which('python') or 'python', 'scripts/inspect_amazon_apk.py', '--expected-version', str(options.version),
                    '--report', str(folder / 'candidate-inspection.json')], cwd=ROOT, check=True)
    print(json.dumps({'path': output.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                      'status': 'LOCAL_CANDIDATE_ONLY; not uploaded, Amazon-processed or publicly approved'}))

if __name__ == '__main__':
    main()
