"""Narrow, reproducible source checks. This is not an independent security audit."""
from pathlib import Path
import json,re,sys,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
def main():
    checks=[]
    def add(name,passed,scope):checks.append({'check':name,'status':'PASS' if passed else 'FAIL','scope':scope})
    manifest=ET.parse(ROOT/'android/app/src/main/AndroidManifest.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
    permissions={x.attrib[ns+'name'] for x in manifest.findall('uses-permission')}
    add('minimal_declared_permissions',permissions=={'android.permission.RECORD_AUDIO','android.permission.INTERNET','android.permission.POST_NOTIFICATIONS','android.permission.RECEIVE_BOOT_COMPLETED'},sorted(permissions))
    reminder = next(x for x in manifest.find('application').findall('receiver') if x.attrib[ns+'name']=='.features.StoryReminderReceiver')
    add('local_reminder_receiver_private',reminder.attrib.get(ns+'exported')=='false','Opt-in inexact local reminder; no exact-alarm permission')
    app=manifest.find('application');add('system_backup_disabled',app.attrib.get(ns+'allowBackup')=='false','Manifest')
    add('cleartext_disabled',app.attrib.get(ns+'usesCleartextTraffic')=='false','App-owned network traffic')
    add('rtl_declared',app.attrib.get(ns+'supportsRtl')=='true','Declaration only; layout review still required')
    gradle=(ROOT/'android/app/build.gradle.kts').read_text()
    add('no_play_billing_or_ad_analytics_dependencies',not re.search(r'billingclient|firebase-analytics|play-services-ads|facebook-android-sdk',gradle),'Direct Gradle dependencies only')
    strings={x.attrib['name'] for x in ET.parse(ROOT/'android/app/src/main/res/values/strings.xml').getroot()}
    keys=set()
    for file in (ROOT/'android/app/src/main/java').rglob('*.kt'):
        text=file.read_text();keys.update(re.findall(r'tr\("([a-z_]+)"\)',text));keys.update(re.findall(r'R\.string\.([a-z_]+)',text))
    add('literal_resource_references_resolve',not keys-strings,{'referenced':len(keys),'missing':sorted(keys-strings),'note':'Dynamic keys are reviewed separately'})
    secrets=[]
    for folder in ['android/app/src','website/src','scripts','localization','server/receipt-verifier/src']:
        for file in (ROOT/folder).rglob('*'):
            if not file.is_file() or file.suffix not in ['.kt','.xml','.ts','.tsx','.py','.json','.mjs']:continue
            if re.search(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',file.read_text(encoding='utf-8')):secrets.append(str(file.relative_to(ROOT)))
    add('no_recognised_embedded_private_keys',not secrets,secrets)
    urls={url for f in (ROOT/'android/app/src/main/java').rglob('*.kt') for url in re.findall(r'https://[^"\s]+',f.read_text())}
    allowed={'https://github.com/lanray07/LifeTalea/blob/main/docs/PRIVACY_POLICY.md'}
    add('literal_public_url_allowlist',not urls-allowed,{'urls':sorted(urls),'note':'Only the owner-provided public privacy notice may be literal. Billing uses BuildConfig. Not a networking/data-flow audit.'})
    result={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,'limitations':'Static source patterns do not prove absence of vulnerabilities or legal compliance.'}
    (ROOT/'deliverables/reports/static-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return result['status']!='PASS'
if __name__=='__main__':sys.exit(main())
