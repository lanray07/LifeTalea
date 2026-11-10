"""Run only headless preservation cases in separate QA packages, without rotating the tablet."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from run_device_tests import ROOT, SDK, ADB

def main():
    folder=ROOT/'deliverables/reports/release-v6-2026-11-10/scale-preservation'
    folder.mkdir(parents=True,exist_ok=True)
    apks=[ROOT/'android/app/build/outputs/apk/debug/app-debug.apk',ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk']
    aapt=SDK/'build-tools/35.0.0/aapt.exe'
    output=[]
    for apk,package in zip(apks,('com.lifetalea.app.debug','com.lifetalea.app.debug.test')):
        badging=subprocess.check_output([str(aapt),'dump','badging',str(apk)],text=True,encoding='utf-8')
        assert re.search(r"package: name='([^']+)'",badging)[1]==package
        result=subprocess.run([str(ADB),'install','-r','-t',str(apk)],capture_output=True,text=True,timeout=120)
        output.append(result.stdout+result.stderr)
        assert result.returncode==0,'Dedicated QA install failed'
    selection='com.lifetalea.app.ScalePreservationTest'
    result=subprocess.run([str(ADB),'shell','am','instrument','-w','-r','-e','class',selection,
        'com.lifetalea.app.debug.test/androidx.test.runner.AndroidJUnitRunner'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
    output.append(result.stdout+result.stderr)
    (folder/'instrumentation.log').write_text('\n'.join(output),encoding='utf-8',newline='\n')
    passed=result.returncode==0 and 'OK (2 tests)' in result.stdout and 'FAILURES!!!' not in result.stdout
    report={'executedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS' if passed else 'FAIL','tests':2,
        'testSelection':selection,'headless':True,'debugApkSha256':hashlib.sha256(apks[0].read_bytes()).hexdigest(),
        'testApkSha256':hashlib.sha256(apks[1].read_bytes()).hexdigest(),'rotationChanged':False,'powerSettingsChanged':False,
        'scope':'Separate QA package, isolated fictional databases and media; no activity launched, regular app data or device credentials accessed. Not a complete device regression or process-death test.'}
    if passed:
        evidence=subprocess.check_output([str(ADB),'exec-out','run-as','com.lifetalea.app.debug','cat','files/test-evidence/scale-preservation.json'],timeout=30)
        details=json.loads(evidence);assert details['status']=='PASS' and details['memories']==1000
        (folder/'scale-preservation.json').write_bytes(evidence)
        report['evidenceSha256']=hashlib.sha256(evidence).hexdigest()
    (folder/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report))
    return 0 if passed else 1

if __name__=='__main__':raise SystemExit(main())
