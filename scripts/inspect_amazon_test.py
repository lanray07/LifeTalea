"""Inspect the separate unsigned LAT candidate; never certifies a purchase or launch."""
from pathlib import Path
import hashlib,json,os,re,subprocess,zipfile
from inspect_amazon_apk import ROOT,SDK

def main():
    apk=ROOT/'android/app/build/outputs/apk/amazonTest/app-amazonTest-unsigned.apk'
    tool=SDK/'build-tools/35.0.0'
    badging=subprocess.check_output([str(tool/'aapt.exe'),'dump','badging',str(apk)],text=True,encoding='utf-8')
    assert "name='com.lifetalea.app'" in badging and 'application-debuggable' not in badging
    config=(ROOT/'android/app/build/generated/source/buildConfig/amazonTest/com/lifetalea/app/BuildConfig.java').read_text()
    pin=json.loads((ROOT/'server/receipt-verifier/supabase/public-signing-key.json').read_text())['publicKeySpkiBase64']
    assert 'AMAZON_PURCHASES_ENABLED = true;' in config and 'RVS_ENVIRONMENT = "production";' in config
    assert pin in config and 'https://guigiqacxpvcxrnajvlz.supabase.co/functions/v1/lifetalea-receipts/v1/verify' in config
    with zipfile.ZipFile(apk) as archive:
        names=archive.namelist()
        assert not any('rvs-contract.json' in n or 'local_billing_qa_ca' in n or 'local_billing_network_security' in n for n in names)
        assert hashlib.sha256(archive.read('assets/AppstoreAuthenticationKey.pem')).hexdigest()==hashlib.sha256((ROOT/'android/app/src/main/assets/AppstoreAuthenticationKey.pem').read_bytes()).hexdigest()
    signing=subprocess.run([str(tool/'apksigner.bat'),'verify',str(apk)],capture_output=True,text=True)
    assert signing.returncode and 'DOES NOT VERIFY' in signing.stderr
    report={'status':'INSPECTION_PASS_LAT_EXECUTION_PENDING','path':apk.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'package':'com.lifetalea.app','debuggable':False,'signing':'UNSIGNED_AMAZON_UPLOAD_CANDIDATE','endpointConfigured':True,'publicPinMatchesDeployedIdentity':True,'purchasesEnabled':True,'environment':'production','sandboxTrustOrFixturesBundled':False,'realPurchaseTested':False}
    (ROOT/'deliverables/reports/amazon-lat-apk-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
