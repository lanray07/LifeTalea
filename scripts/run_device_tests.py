"""Run installed QA APK instrumentation and retain its own private test evidence.
Gradle connected tests uninstall APKs after running; this separate QA run intentionally
leaves only the .debug app installed so screenshots/PDF diagnostics can be retrieved.
No raw microphone recording is copied.
"""
from pathlib import Path,PurePosixPath
import argparse
import subprocess,os,sys,tarfile,io,json,re,hashlib
from datetime import datetime,timezone
from fire_qa_session import awake_device, landscape_device
ROOT=Path(__file__).resolve().parents[1]
SDK=Path(os.environ.get('ANDROID_HOME',str(Path.home()/'AppData/Local/Android/Sdk')))
ADB=SDK/'platform-tools'/('adb.exe' if os.name=='nt' else 'adb')
LOG=ROOT/'deliverables/android/build-logs/instrumentation.log'
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset-qa',action='store_true',help='Delete only the dedicated .debug QA app data before testing. Never targets production.');args=parser.parse_args()
    (ROOT/'deliverables/reports/device-test-run.json').write_text(json.dumps({'status':'RUNNING','startedAt':datetime.now(timezone.utc).isoformat()}),encoding='utf-8')
    with awake_device(ADB) as qa_power, landscape_device(ADB) as qa_rotation, LOG.open('w',encoding='utf-8') as log:
        for apk in ['android/app/build/outputs/apk/debug/app-debug.apk','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']:
            result=subprocess.run([str(ADB),'install','-r',str(ROOT/apk)],capture_output=True,text=True)
            log.write(result.stdout+result.stderr);log.flush()
            if result.returncode:raise RuntimeError('QA install failed; see instrumentation.log')
        if args.reset_qa:
            reset=subprocess.run([str(ADB),'shell','pm','clear','com.lifetalea.app.debug'],capture_output=True,text=True)
            log.write('Reset dedicated debug QA fixtures only:\n'+reset.stdout+reset.stderr);log.flush()
            if reset.returncode:raise RuntimeError('QA fixture reset failed')
        result=subprocess.run([str(ADB),'shell','am','instrument','-w','-r','com.lifetalea.app.debug.test/androidx.test.runner.AndroidJUnitRunner'],capture_output=True,text=True,encoding='utf-8',errors='replace')
        log.write(result.stdout+result.stderr);log.flush()
        passed=bool(re.search(r'OK \(\d+ tests?\)',result.stdout)) and 'FAILURES!!!' not in result.stdout
    archive=subprocess.run([str(ADB),'exec-out','run-as','com.lifetalea.app.debug','tar','cf','-','files/test-evidence'],capture_output=True)
    count=0; evidence=[]
    if archive.returncode==0:
        destination=ROOT/'deliverables/reports/device-evidence';destination.mkdir(exist_ok=True,parents=True)
        with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
            for member in tar.getmembers():
                name=PurePosixPath(member.name)
                if not member.isfile() or name.is_absolute() or '..' in name.parts:continue
                if tuple(name.parts[:2])!=('files','test-evidence'):continue
                target=destination.joinpath(*name.parts[2:]);target.parent.mkdir(exist_ok=True,parents=True)
                if target.suffix not in ['.png','.pdf','.json']:continue
                if member.size>20*1024*1024:raise RuntimeError('Unexpected diagnostic size')
                target.write_bytes(tar.extractfile(member).read());count+=1
                evidence.append({'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    provenance={'executedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS' if passed else 'FAIL','debugApkSha256':hashlib.sha256((ROOT/'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes()).hexdigest(),'testApkSha256':hashlib.sha256((ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk').read_bytes()).hexdigest(),'evidenceFiles':count,'qaPowerSettings':qa_power,'qaRotationSettings':qa_rotation}
    provenance['evidence']=evidence
    (ROOT/'deliverables/reports/device-test-run.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps({'deviceSuite':'PASS' if passed else 'FAIL','evidenceFiles':count,'log':str(LOG.relative_to(ROOT))}))
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
