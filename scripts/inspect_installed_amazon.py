"""Read and compare an Appstore-installed APK; never installs or clears app data."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_HOME', str(Path.home()/'AppData/Local/Android/Sdk')))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', type=int, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    options = parser.parse_args()
    candidate = options.candidate.resolve()
    report = options.report.resolve()
    assert candidate.is_relative_to(ROOT) and report.is_relative_to(ROOT)
    adb = str(SDK/'platform-tools/adb.exe')
    def run(*args): return subprocess.check_output([adb,*args],text=True,encoding='utf-8',timeout=60).strip()
    metadata = run('shell','dumpsys','package','com.lifetalea.app')
    version = int(re.search(r'versionCode=(\d+)',metadata)[1])
    assert version == options.version, f'Installed version is {version}'
    assert 'installerPackageName=com.amazon.venezia' in metadata
    path = run('shell','pm','path','com.lifetalea.app')
    assert path.startswith('package:/data/app/') and path.endswith('/base.apk') and '\n' not in path
    target = ROOT/f'android/app/build/localLatQa/amazon-distributed-v{version}.apk'
    subprocess.run([adb,'pull',path.removeprefix('package:'),str(target)],check=True,capture_output=True,timeout=90)
    signer = str(SDK/'build-tools/35.0.0/apksigner.bat')
    signed = subprocess.run([signer,'verify','--print-certs',str(target)],capture_output=True,text=True,timeout=60)
    assert signed.returncode == 0, 'Distributed APK signature did not verify'
    certificate = re.search(r'certificate SHA-256 digest: ([a-fA-F0-9]+)',signed.stdout)[1].lower()
    expected = '8e35b165d5a1dc14c10820cee25ed2c24e9c543ceb2f059b9f5bc93baa672297'
    assert certificate == expected, 'Amazon update signing identity changed'
    def sha(value): return hashlib.sha256(value).hexdigest()
    with zipfile.ZipFile(candidate) as original, zipfile.ZipFile(target) as actual:
        names = [n for n in original.namelist() if n.endswith('.dex') or n.endswith('/liblifetalea_whisper.so') or n=='assets/transcription/ggml-tiny.bin']
        assert len([n for n in names if n.endswith('.dex')]) >= 1
        assert len([n for n in names if n.endswith('.so')]) == 2
        matches = {n:original.read(n)==actual.read(n) for n in names}
        assert all(matches.values()), 'Amazon payload differs from the upload'
        model = sha(actual.read('assets/transcription/ggml-tiny.bin'))
    result = {'date':'2026-11-10','versionCode':version,'installer':'com.amazon.venezia',
              'uploadSha256':sha(candidate.read_bytes()),'distributedApkSha256':sha(target.read_bytes()),
              'certificateSha256':certificate,'matchesPreviousAmazonCertificate':True,
              'contentMatchesUpload':matches,'allContentMatches':True,'modelSha256':model,
              'scope':'Actual Appstore update; regular package was not uninstalled. Runtime checks recorded separately.'}
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__': main()
