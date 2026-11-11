"""One unlocked-device batch; preserve power state across instrumentation and layout checks."""
from pathlib import Path
import argparse, json, subprocess, sys, os, shutil
from datetime import datetime, timezone
from fire_qa_session import awake_device
from run_device_tests import ADB, ROOT

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset-qa',action='store_true');parser.add_argument('--build',action='store_true');parser.add_argument('--output-dir');args=parser.parse_args()
    default_output = 'deliverables/reports'
    if args.reset_qa:
        default_output += '/qa-runs/' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = (ROOT / (args.output_dir or default_output)).resolve()
    if not output.is_relative_to(ROOT.resolve()):
        parser.error('Evidence must stay inside the workspace')
    batch={};code=1
    try:
        with awake_device(ADB) as batch:
            if args.build:
                java=str(Path(os.environ['JAVA_HOME'])/'bin'/('java.exe' if os.name=='nt' else 'java')) if os.environ.get('JAVA_HOME') else shutil.which('java')
                tasks=['testDebugUnitTest','assembleDebug','assembleRelease','assembleDebugAndroidTest','lintDebug']
                with (ROOT/'deliverables/android/build-logs/amazon-rvs-build.log').open('w',encoding='utf-8') as log:
                    subprocess.run([java,'-classpath',str(ROOT/'android/gradle/wrapper/gradle-wrapper.jar'),'org.gradle.wrapper.GradleWrapperMain','-p','android','--no-daemon',*tasks],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
            subprocess.run([sys.executable,str(ROOT/'scripts/inspect_amazon_apk.py')],cwd=ROOT,check=True)
            command=[sys.executable,str(ROOT/'scripts/run_device_tests.py'),'--output-dir',str(output)]
            if args.reset_qa:command.append('--reset-qa')
            subprocess.run(command,cwd=ROOT,check=True)
            subprocess.run([sys.executable,str(ROOT/'scripts/check_fire_layouts.py')],cwd=ROOT,check=True)
            code=0
    finally:
        for path in [output/'device-test-run.json',ROOT/'deliverables/reports/device-evidence/layout-smoke/result.json']:
            if path.exists() and batch:
                report=json.loads(path.read_text(encoding='utf-8'));report['qaBatchPowerSettings']=batch
                if not batch.get('restored'):report['status']='FAIL'
                path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return code

if __name__=='__main__':sys.exit(main())
