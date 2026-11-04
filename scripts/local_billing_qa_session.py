"""Bounded App Tester device session; restores its catalogue, SDK mode and power.

Run only after the owner unlocks the tablet. This installs only .billingqa, keeps
existing App Tester transactions/data, and never changes production app storage.
Touch STOP under ignored build output to finish and restore the original settings.
"""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from fire_qa_session import awake_device
from run_device_tests import ADB,ROOT

OUT=ROOT/'deliverables/reports/amazon-app-tester-session.json'
WORK=ROOT/'android/app/build/localBillingQa'
STOP=WORK/'STOP'

def adb(*args):
    return subprocess.run([str(ADB),*args],capture_output=True,timeout=45)

def require(*args):
    r=adb(*args)
    if r.returncode:raise RuntimeError('QA ADB operation failed: '+str(args[:3]))
    return r.stdout

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--timeout-minutes',type=int,choices=[15,30],default=30);args=parser.parse_args()
    context=json.loads((WORK/'context.json').read_text())
    private=Path(context['privateDirectory'])
    report={'startedAt':datetime.now(timezone.utc).isoformat(),'status':'RUNNING','environment':'sandbox','productionStorageTouched':False}
    mode=require('shell','getprop','debug.amazon.sandboxmode').decode().strip()
    if b'tcp:8443' in require('reverse','--list'):raise RuntimeError('Port 8443 already has an ADB reverse mapping; refusing to overwrite it')
    if b'allow' not in require('shell','appops','get','com.amazon.sdktestclient','SYSTEM_ALERT_WINDOW'):
        raise RuntimeError('App Tester overlay permission is not already enabled')
    original=adb('exec-out','cat','/sdcard/amazon.sdktester.json')
    present=original.returncode==0
    if not present and b'No such file' not in original.stderr and b'No such file' not in original.stdout:raise RuntimeError('Cannot safely determine the original App Tester catalogue')
    catalogue=json.loads(original.stdout) if present else {}
    if not isinstance(catalogue,dict):raise RuntimeError('Unexpected existing App Tester catalogue')
    if present:(private/'original-app-tester.json').write_bytes(original.stdout)
    catalogue['com.lifetalea.premium']={'itemType':'ENTITLED','price':4.99,'title':'LifeTalea Premium — SANDBOX TEST','description':'Fictional App Tester price. No real payment. Unlimited albums, longer recordings, PDF and encrypted backups.'}
    (WORK/'amazon.sdktester.json').write_text(json.dumps(catalogue),encoding='utf-8')
    if STOP.exists():STOP.unlink()
    changed=False;reverse=False
    try:
        with awake_device(ADB) as power:
            report['qaPowerSettings']=power
            require('install','-r',str(ROOT/'android/app/build/outputs/apk/billingQa/app-billingQa.apk'))
            changed=True
            require('push',str(WORK/'amazon.sdktester.json'),'/sdcard/amazon.sdktester.json')
            require('shell','setprop','debug.amazon.sandboxmode','debug')
            require('reverse','tcp:8443','tcp:8443');reverse=True
            report['billingQaApkSha256']=hashlib.sha256((ROOT/'android/app/build/outputs/apk/billingQa/app-billingQa.apk').read_bytes()).hexdigest()
            report['originalSdkMode']=mode;report['originalCataloguePresent']=present
            OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(f'READY: localhost TLS forwarding and sandbox SDK enabled; STOP file ends this {args.timeout_minutes}-minute test session',flush=True)
            until=time.monotonic()+args.timeout_minutes*60
            while time.monotonic()<until and not STOP.exists():time.sleep(1)
            report['stopReason']='operator' if STOP.exists() else 'watchdog'
    finally:
        if reverse:require('reverse','--remove','tcp:8443')
        if changed:
            if present:require('push',str(private/'original-app-tester.json'),'/sdcard/amazon.sdktester.json')
            else:require('shell','rm','-f','/sdcard/amazon.sdktester.json')
            require('shell','setprop','debug.amazon.sandboxmode',mode or '""')
            restored=adb('exec-out','cat','/sdcard/amazon.sdktester.json')
            assert (restored.returncode==0 and restored.stdout==original.stdout) if present else restored.returncode!=0
            assert require('shell','getprop','debug.amazon.sandboxmode').decode().strip()==mode
        report['catalogueAndSdkModeRestored']=changed
        report['finishedAt']=datetime.now(timezone.utc).isoformat();report['status']='SESSION_CLOSED_TEST_RESULTS_RECORDED_SEPARATELY' if changed else 'PREFLIGHT_BLOCKED_NO_DEVICE_CHANGES'
        OUT.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print('Original App Tester catalogue, SDK mode and power restored' if changed else 'QA preflight stopped before changing the device',flush=True)

if __name__=='__main__':main()
