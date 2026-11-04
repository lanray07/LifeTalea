"""Bounded production-channel device session; never changes Amazon SDK sandbox mode."""
from datetime import datetime, timezone
import json, subprocess, time
from fire_qa_session import awake_device
from run_device_tests import ADB, ROOT

def main():
    work=ROOT/'android/app/build/localLatQa';work.mkdir(parents=True,exist_ok=True)
    stop=work/'STOP'
    if stop.exists():stop.unlink()
    def mode():return subprocess.check_output([str(ADB),'shell','getprop','debug.amazon.sandboxmode'],text=True,timeout=20).strip()
    original=mode()
    if original not in ('','none'):raise RuntimeError('Exit App Tester sandbox before LAT; no settings changed')
    report={'startedAt':datetime.now(timezone.utc).isoformat(),'status':'RUNNING','sdkMode':original,'sandboxModeChanged':False}
    try:
        with awake_device(ADB) as power:
            report['power']=power
            path=ROOT/'deliverables/reports/amazon-lat-device-session.json'
            path.write_text(json.dumps(report,indent=2)+'\n')
            print('READY: bounded 30-minute LAT session; STOP file restores original power',flush=True)
            until=time.monotonic()+1800
            while time.monotonic()<until and not stop.exists():time.sleep(1)
            report['stopReason']='operator' if stop.exists() else 'watchdog'
    finally:
        report['finishedAt']=datetime.now(timezone.utc).isoformat()
        report['sdkModeUnchanged']=mode()==original
        report['status']='CLOSED_RESULTS_RECORDED_SEPARATELY'
        (ROOT/'deliverables/reports/amazon-lat-device-session.json').write_text(json.dumps(report,indent=2)+'\n')
        print('LAT session closed; original power restored',flush=True)

if __name__=='__main__':main()
