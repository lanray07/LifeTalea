"""Build the next public candidate with public verifier configuration; never uploads."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def main():
    folder = ROOT / 'deliverables/reports/transcription-2026-11-07'
    folder.mkdir(parents=True, exist_ok=True)
    pin = json.loads((ROOT / 'server/receipt-verifier/supabase/public-signing-key.json').read_text())['publicKeySpkiBase64']
    binary = 'java.exe' if os.name == 'nt' else 'java'
    java = str(Path(os.environ['JAVA_HOME']) / 'bin' / binary) if os.environ.get('JAVA_HOME') else shutil.which('java')
    args = [java, '-classpath', str(ROOT / 'android/gradle/wrapper/gradle-wrapper.jar'),
            'org.gradle.wrapper.GradleWrapperMain', '-p', 'android', '--no-daemon', ':app:assembleRelease',
            '-PlifetaleaPurchasesEnabled=true',
            '-PlifetaleaRvsUrl=https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify',
            '-PlifetaleaRvsPublicKey=' + pin]
    with (folder / 'candidate-build.log').open('w', encoding='utf-8') as log:
        subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    apk = ROOT / 'android/app/build/outputs/apk/release/app-release-unsigned.apk'
    output = ROOT / 'deliverables/amazon-submission/LifeTalea-0.1.0-public-v4-unsigned.apk'
    shutil.copyfile(apk, output)
    subprocess.run([shutil.which('python') or 'python', 'scripts/inspect_amazon_apk.py', '--expected-version', '4',
                    '--report', str(folder / 'candidate-inspection.json')], cwd=ROOT, check=True)
    print(json.dumps({'path': output.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                      'status': 'LOCAL_CANDIDATE_ONLY; not uploaded, Amazon-processed or publicly approved'}))

if __name__ == '__main__':
    main()
