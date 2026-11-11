"""Run installed QA APK instrumentation and retain its own private test evidence.
Gradle connected tests uninstall APKs after running; this separate QA run intentionally
leaves only the .debug app installed so screenshots/PDF diagnostics can be retrieved.
No raw microphone recording is copied.
"""
from pathlib import Path,PurePosixPath,PureWindowsPath
import argparse
import subprocess,os,sys,tarfile,io,json,re,hashlib
from threading import Timer
from datetime import datetime,timezone
from fire_qa_session import awake_device, landscape_device
ROOT=Path(__file__).resolve().parents[1]
SDK=Path(os.environ.get('ANDROID_HOME',str(Path.home()/'AppData/Local/Android/Sdk')))
ADB=SDK/'platform-tools'/('adb.exe' if os.name=='nt' else 'adb')
LOG=ROOT/'deliverables/android/build-logs/instrumentation.log'
MAX_EVIDENCE = 128 * 1024 * 1024

def read_device_evidence():
    command = [str(ADB),'exec-out','run-as','com.lifetalea.app.debug','tar','cf','-','files/test-evidence']
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
        watchdog = Timer(60, proc.kill)
        watchdog.start()
        try:
            data = proc.stdout.read(MAX_EVIDENCE + 1)
            if len(data) > MAX_EVIDENCE:
                proc.kill()
                raise RuntimeError('Evidence archive exceeds size limit')
            return data if proc.wait(timeout=5) == 0 else None
        finally:
            watchdog.cancel()

def extract_evidence(data, destination):
    destination.mkdir()
    evidence = []
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r|') as archive:
        for count, member in enumerate(archive, 1):
            if count > 2000:
                raise RuntimeError('Too many evidence entries')
            name = PurePosixPath(member.name)
            if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE) or tuple(name.parts[:2]) != ('files','test-evidence'):
                continue
            if member.issparse():
                raise RuntimeError('Sparse evidence files are not supported')
            parts = name.parts[2:]
            if not parts or any(
                not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9._-]{0,119}', part)
                or part.endswith('.') or PureWindowsPath(part).is_reserved()
                for part in parts
            ):
                raise RuntimeError('Invalid evidence path')
            target = destination.joinpath(*parts)
            if target.suffix not in ('.png','.pdf','.json'):
                continue
            total += member.size
            if (not target.resolve().is_relative_to(destination.resolve())
                or not 0 <= member.size <= 20 * 1024 * 1024 or total > MAX_EVIDENCE):
                raise RuntimeError('Evidence destination or size rejected')
            target.parent.mkdir(exist_ok=True,parents=True)
            with target.open('xb') as output, archive.extractfile(member) as source:
                content = source.read()
                output.write(content)
            evidence.append({'path':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(content).hexdigest()})
    return evidence

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset-qa',action='store_true',help='Delete only the dedicated .debug QA app data before testing. Never targets production.')
    parser.add_argument('--test-class', help='Optional instrumentation class or class#method')
    parser.add_argument('--output-dir', help='Separate workspace evidence directory; preserves historical release reports')
    parser.add_argument('--app-apk', default='android/app/build/outputs/apk/debug/app-debug.apk')
    parser.add_argument('--test-apk', default='android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')
    args=parser.parse_args()
    if args.test_class and not re.fullmatch(r'[A-Za-z0-9_.]+(?:#[A-Za-z0-9_]+)?',args.test_class):parser.error('Invalid test class')
    default_output = ROOT/'deliverables/reports'
    if args.reset_qa:
        default_output /= 'qa-runs/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=(ROOT/args.output_dir).resolve() if args.output_dir else default_output
    if not output.is_relative_to(ROOT.resolve()):parser.error('Evidence must stay inside the workspace')
    output.mkdir(parents=True,exist_ok=True)
    destination = output/'device-evidence'
    if args.reset_qa and os.path.lexists(destination):parser.error('Choose a fresh output directory for this run')
    report=output/'device-test-run.json'
    log_path=output/'instrumentation.log' if args.output_dir or args.reset_qa else LOG
    report.write_text(json.dumps({'status':'RUNNING','startedAt':datetime.now(timezone.utc).isoformat()}),encoding='utf-8')
    apks=[(ROOT/path).resolve() for path in (args.app_apk,args.test_apk)]
    for apk,package in zip(apks,('com.lifetalea.app.debug','com.lifetalea.app.debug.test')):
        if not apk.is_relative_to(ROOT.resolve()):parser.error('QA APK must stay inside workspace')
        aapt=SDK/'build-tools/35.0.0'/('aapt.exe' if os.name=='nt' else 'aapt')
        badging=subprocess.check_output([str(aapt),'dump','badging',str(apk)],text=True,encoding='utf-8')
        if re.search(r"package: name='([^']+)'",badging)[1]!=package:parser.error('Refusing to install an APK outside the dedicated debug QA packages')
    with awake_device(ADB) as qa_power, landscape_device(ADB) as qa_rotation, log_path.open('w',encoding='utf-8') as log:
        for apk in apks:
            result=subprocess.run([str(ADB),'install','-r','-t',str(apk)],capture_output=True,text=True,timeout=120)
            log.write(result.stdout+result.stderr);log.flush()
            if result.returncode:
                report.write_text(json.dumps({'status':'SETUP_FAILED','reason':'QA install failed','apk':apk.relative_to(ROOT).as_posix()}),encoding='utf-8')
                raise RuntimeError('QA install failed; see instrumentation.log')
        if args.reset_qa:
            reset=subprocess.run([str(ADB),'shell','pm','clear','com.lifetalea.app.debug'],capture_output=True,text=True)
            log.write('Reset dedicated debug QA fixtures only:\n'+reset.stdout+reset.stderr);log.flush()
            if reset.returncode or reset.stdout.strip() != 'Success':
                raise RuntimeError('QA fixture reset failed')
        selected=['-e','class',args.test_class] if args.test_class else []
        result=subprocess.run([str(ADB),'shell','am','instrument','-w','-r',*selected,'com.lifetalea.app.debug.test/androidx.test.runner.AndroidJUnitRunner'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
        log.write(result.stdout+result.stderr);log.flush()
        passed=result.returncode == 0 and bool(re.search(r'OK \(\d+ tests?\)',result.stdout)) and 'FAILURES!!!' not in result.stdout
    # Only export captures from a test batch that started in a freshly reset QA sandbox.
    capture_status = 'SKIPPED'
    evidence = []
    if args.reset_qa and passed:
        try:
            archive = read_device_evidence()
            if archive is None:
                raise RuntimeError('Device evidence could not be read')
            evidence = extract_evidence(archive, destination)
            if not args.test_class and not evidence:
                raise RuntimeError('Full QA run did not produce evidence')
            capture_status = 'PASS'
        except (OSError, RuntimeError, tarfile.TarError, subprocess.TimeoutExpired):
            passed = False
            capture_status = 'FAIL'
    count = len(evidence)
    provenance={'executedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS' if passed else 'FAIL','debugApkSha256':hashlib.sha256(apks[0].read_bytes()).hexdigest(),'testApkSha256':hashlib.sha256(apks[1].read_bytes()).hexdigest(),'evidenceFiles':count,'qaPowerSettings':qa_power,'qaRotationSettings':qa_rotation}
    provenance['apkSources']=[path.relative_to(ROOT).as_posix() for path in apks]
    provenance['evidence']=evidence
    provenance['syntheticQaProfile']=args.reset_qa and passed
    provenance['captureStatus']=capture_status
    provenance['testSelection']=args.test_class or 'all'
    report.write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps({'deviceSuite':'PASS' if passed else 'FAIL','evidenceFiles':count,'log':str(log_path.relative_to(ROOT))}))
    return 0 if passed else 1
if __name__=='__main__':sys.exit(main())
