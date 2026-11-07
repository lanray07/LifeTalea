"""Non-UI process restart test, restricted to the dedicated debug QA package."""
import json
import hashlib
import re
import subprocess
from run_device_tests import ADB, ROOT

folder = ROOT / 'deliverables/reports/transcription-2026-11-07'
apk = ROOT / 'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
installed = subprocess.check_output([str(ADB), 'shell', 'pm', 'path', 'com.lifetalea.app.debug'], text=True, timeout=30).strip()
assert installed.startswith('package:/data/app/') and installed.endswith('/base.apk') and '\n' not in installed
binary = subprocess.check_output([str(ADB), 'exec-out', 'cat', installed.removeprefix('package:')], timeout=60)
app_hash = hashlib.sha256(binary).hexdigest()
expected = json.loads((folder / 'offline/device-test-run.json').read_bytes())['debugApkSha256']
assert app_hash == expected, 'Restart test must target the same installed app as the offline suite'
install = subprocess.run([str(ADB), 'install', '-r', '-t', str(apk)], capture_output=True, text=True, timeout=120)
assert install.returncode == 0, 'QA test APK install failed'
log = install.stdout + install.stderr
for phase in ('prepare', 'verify', 'errors'):
    if phase == 'verify':
        subprocess.run([str(ADB), 'shell', 'am', 'force-stop', 'com.lifetalea.app.debug'], check=True, timeout=30)
    selected = 'com.lifetalea.app.TranscriptionDeviceTest#silenceBadAudioLimitsAndMissingConsentNeverProduceInventedWords' if phase == 'errors' else 'com.lifetalea.app.TranscriptionRestartTest'
    result = subprocess.run([str(ADB), 'shell', 'am', 'instrument', '-w', '-r',
        '-e', 'class', selected, '-e', 'transcriptionRestartPhase', phase,
        'com.lifetalea.app.debug.test/androidx.test.runner.AndroidJUnitRunner'], capture_output=True, text=True, timeout=240)
    log += '\nPHASE ' + phase + '\n' + result.stdout + result.stderr
    (folder / 'restart.log').write_text(log, encoding='utf-8')
    assert re.search(r'OK \(1 test\)', result.stdout), f'Restart {phase} phase failed; see restart.log'
output = subprocess.check_output([str(ADB), 'exec-out', 'run-as', 'com.lifetalea.app.debug',
    'cat', 'files/test-evidence/transcription/process-restart.json'], timeout=30)
report = json.loads(output)
assert report['status'] == 'PASS' and report['processChanged']
report['debugApkSha256'] = app_hash
report['testApkSha256'] = hashlib.sha256(apk.read_bytes()).hexdigest()
(folder / 'process-restart.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
failures = subprocess.check_output([str(ADB), 'exec-out', 'run-as', 'com.lifetalea.app.debug',
    'cat', 'files/test-evidence/transcription/failure-fallbacks.json'], timeout=30)
assert json.loads(failures)['originalFilesUnchanged']
(folder / 'failure-preservation.json').write_bytes(failures)
print(json.dumps(report))
