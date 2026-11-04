"""Current billing evidence only; never upgrades live/deployment/native/legal gates from fixtures."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, re, shutil, xml.etree.ElementTree as ET
from prepare_amazon_submission import SERVER_FILES

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'deliverables/reports'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-incomplete-ui',action='store_true');args=parser.parse_args()
    run=read('deliverables/reports/device-test-run.json')
    debug=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    test=ROOT/'android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'
    if run.get('debugApkSha256')!=sha(debug):raise SystemExit('Current app has no matching physical evidence')
    complete=run.get('status')=='PASS' and run.get('testApkSha256')==sha(test)
    if not complete and not args.allow_incomplete_ui:raise SystemExit('Current physical device suite is not verified')
    if not run.get('qaBatchPowerSettings',{}).get('restored') or not run.get('qaRotationSettings',{}).get('restored'):raise SystemExit('Restore and verify QA device settings first')
    checks=read('deliverables/reports/amazon-local-checks.json')
    if checks['status']!='PASS':raise SystemExit('Local checks incomplete')
    row=next(row for row in checks['checks'] if row['check']=='amazon-rvs-server')
    node=(ROOT/row['log']).read_text(encoding='utf-8')
    node_count=int(re.search(r'^# tests (\d+)$',node,re.M)[1]);node_pass=int(re.search(r'^# pass (\d+)$',node,re.M)[1])
    if node_count!=node_pass or not re.search(r'^# fail 0$',node,re.M):raise SystemExit('Server tests failed')
    edge_row=next(row for row in checks['checks'] if row['check']=='amazon-rvs-edge')
    edge_log=(ROOT/edge_row['log']).read_text(encoding='utf-8')
    if not all(re.search(pattern,edge_log,re.M) for pattern in [r'^# tests 3$',r'^# pass 3$',r'^# fail 0$']):raise SystemExit('Edge adapter tests incomplete')
    native=(ROOT/'deliverables/android/build-logs/instrumentation.log').read_text(encoding='utf-8')
    total=int(re.search(r'OK \((\d+) tests?\)',native)[1]) if complete else int(re.search(r'Tests run: (\d+)',native)[1])
    device_count=total if complete else len(re.findall(r'^INSTRUMENTATION_STATUS_CODE: 0$',native,re.M))
    seconds=re.search(r'Time: ([0-9.]+)',native)[1]
    current={};contract=set()
    for line in native.splitlines():
        if line.startswith('INSTRUMENTATION_STATUS: class='):current['class']=line.split('class=',1)[1]
        if line.startswith('INSTRUMENTATION_STATUS: test='):current['test']=line.split('test=',1)[1]
        if line=='INSTRUMENTATION_STATUS_CODE: 0' and current.get('class')=='com.lifetalea.app.ReceiptVerificationTest':contract.add(current['test'])
    expected=set(re.findall(r'@Test\s+fun\s+(\w+)',(ROOT/'android/app/src/androidTest/java/com/lifetalea/app/ReceiptVerificationTest.kt').read_text()))
    if contract!=expected:raise SystemExit('Not all Android receipt contract tests passed')
    suites=list((ROOT/'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml'))
    counts=[ET.parse(p).getroot() for p in suites]
    if not counts or any(int(s.get('failures',0))+int(s.get('errors',0))+int(s.get('skipped',0)) for s in counts):raise SystemExit('Unit tests incomplete')
    units=sum(int(s.get('tests')) for s in counts)
    for path in suites:shutil.copy2(path,REPORTS/'junit'/path.name)
    issues=ET.parse(ROOT/'android/app/build/reports/lint-results-debug.xml').getroot().findall('issue')
    lint={level:sum(issue.get('severity')==level for issue in issues) for level in ['Error','Warning']}
    layout=read('deliverables/reports/device-evidence/layout-smoke/result.json')
    layout_current=layout.get('status')=='PASS' and layout.get('debugApkSha256')==run['debugApkSha256'] and (layout.get('qaBatchPowerSettings',{}).get('restored') or layout.get('qaPowerSettings',{}).get('restored'))
    if not layout_current and not args.allow_incomplete_ui:raise SystemExit('Current layout/offline smoke incomplete')
    captures=read('deliverables/store-assets/screenshots/localized-drafts/provenance.json')
    captures_current=captures.get('debugApkSha256')==run['debugApkSha256'] and len(captures.get('assets',[]))==176 and all(sha(ROOT/row['asset'])==row['sha256'] and sha(ROOT/row['actualCapture'])==row['captureSha256'] for row in captures['assets'])
    screenshot_note='All 176 current-APK screenshot compositions were refreshed and byte-validated; they remain drafts with zero native approvals.' if captures_current and complete else 'Refresh and validate the 176 screenshot compositions against this APK before packaging; the package builder enforces the hashes.'
    inspection=read('deliverables/reports/amazon-release-apk-inspection.json')
    result={'executedAt':datetime.now(timezone.utc).isoformat(),'status':'LOCAL_CHECKS_PASS_RELEASE_BLOCKED' if complete and layout_current else 'BILLING_EVIDENCE_PRESENT_UI_QA_INCOMPLETE_RELEASE_BLOCKED','uiChecksComplete':complete and layout_current,'debugApkSha256':run['debugApkSha256'],'testApkSha256':sha(test),'lastExecutedTestApkSha256':run['testApkSha256'],'currentTestApkExecuted':run['testApkSha256']==sha(test),'releaseApkSha256':inspection['sha256'],
        'serverTests':{'status':'PASS','tests':node_count,'passed':node_pass,'log':row['log'],'scope':'Fictional Amazon responses; real crypto/local HTTP/executable/key-helper tests; not live Amazon RVS'},
        'androidReceiptContractTests':{'status':'PASS','passed':len(contract),'tests':sorted(contract),'scope':'Node-signed offline fixtures and actual Fire RSA/JSON/config behavior, not real SDK payment callbacks'},
        'kotlinUnitTestsPassed':units,'physicalDeviceTestsPassed':device_count,'physicalDeviceTestsRun':total,'physicalDeviceSuiteStatus':run['status'],'deviceSeconds':float(seconds),'lint':lint,'layoutSmokeStatus':layout['status'] if layout.get('debugApkSha256')==run['debugApkSha256'] else 'NOT_VERIFIED_ON_CURRENT_APP','currentScreenshotDraftsValidated':176 if captures_current and complete else 0,
        'serverDeployed':True,'liveAmazonRvsTested':'PRODUCTION_NEGATIVE_RECEIPT_ONLY','livePurchaseTestsPassed':False,'dockerImageBuilt':False,'productionSigningIdentityCreated':True,
        'productionDeployment':read('deliverables/reports/amazon-supabase-deployment.json'),
        'appTesterSandbox':read('deliverables/reports/amazon-billing-sandbox-tests.json'),
        'amazonLat':read('deliverables/reports/amazon-console-review.json').get('latDraft'),
        'latPurchaseTests':read('deliverables/reports/amazon-lat-purchase-tests.json'),
        'defaultReleaseConfiguration':inspection['generatedReleaseBillingConfiguration'],
        'serverSourceSha256':{name:sha(ROOT/f'server/receipt-verifier/{name}') for name in SERVER_FILES},
        'remaining':'Execute configured Amazon LAT purchases against deployed verifier; complete independent security/privacy/legal/native and remaining product/device gates.'}
    (REPORTS/'amazon-rvs-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    deployment=result['productionDeployment']
    assert deployment['status']==200 and deployment['signatureValid'] and deployment['payload']['active'] is False
    assert result['appTesterSandbox']['catalogueSdkModeAndPowerRestored']
    state='Current device and collateral checks passed.' if complete and layout_current else 'Current UI QA is incomplete.'
    readiness=f'''# Release readiness — BLOCKED

Updated 4 November 2026. {state} The original acceptance requirements remain in scope.

The Supabase production verifier is deployed with server-only credentials and its own RSA signing identity. HTTPS health and a signed rejection of synthetic invalid receipt identifiers passed. This does not verify an actual production purchase. See AMAZON_SUPABASE_DEPLOYMENT.md and amazon-supabase-deployment.json.

Amazon Premium was submitted to the TEST channel and is Approved, with the owner's £4.99 UK one-time price and Amazon-calculated marketplace prices. The public app and paid upgrade have not been published. The connected LAT candidate was uploaded and Amazon now reports Test in-progress and the tester invitation Delivered. Invitation redemption/installation and actual purchase verification remain pending. The standard release remains purchases-disabled; the separate LAT candidate uses the deployed URL and public pin.

Real App Tester sandbox tests exposed a canceled-receipt bug. The fixed QA build passed cancellation, purchase-dialog cancellation, fresh purchase, restore and cancellation of the new fulfilled receipt. SDK cancellations now revoke a receipt and prevent a late active response from reinstating it. The account-switch observation belongs to the earlier QA APK and is labelled accordingly. See amazon-billing-sandbox-tests.json.

Current local evidence: {node_pass} Node core tests, three edge adapter tests, {units} Kotlin unit tests and {device_count}/{total} physical Fire tests. Lint: {lint['Error']} errors, {lint['Warning']} warnings. Layout/offline status: {layout['status']}. All original device settings, App Tester catalogue and SDK mode were restored. {screenshot_note}

Remaining: deployed-server LAT purchase/restore/cancellation/account/offline tests;  recorded-file transcription; native approval and matching release assets; outstanding product, backup/crash recovery, accessibility/performance/device checks; independent server/client security and final privacy/legal/signing review. No public release readiness or Amazon public approval is claimed. See AMAZON_OWNER_ACTIONS.md.
'''
    (ROOT/'docs/RELEASE_READINESS.md').write_text(readiness,encoding='utf-8')
    text=readiness+f'''\nExecuted evidence:

- Core Node contract/crypto/HTTP/startup/rate/timeout/key-helper tests: {node_pass}/{node_count}. These use fictional upstream responses; actual Amazon tests are reported separately.
- Edge adapter tests: three passed (secrets fail closed, request bounds, quota, receipt delegation and error redaction).
- Kotlin: {units} passed, including SDK revocation identity/epoch binding and rejection of late active responses after cancellation. The retained red regression log demonstrates the original bug.
- Physical KFTRWI, Fire HD 10 (2021), Fire OS 7/API 28: {device_count}/{total} passed in {seconds} seconds, including {len(contract)} signed-receipt fixture tests, core writing/media/backup/PDF/short recording flows and the 22-locale capture matrix. This suite uses the standard debug APK; SDK App Tester uses a separate QA APK with its own hash.
- Three home-screen layout checks: portrait/landscape at 1.3× text and Wi-Fi-disabled reopen. Scope excludes full-screen accessibility and prolonged offline Premium behavior.
- All {len(checks['checks'])} collateral groups passed: Python, locale resources/isolation, editorial regression, metadata, browser locale/review/static-export, TypeScript, website structure and narrow source patterns.
- {176 if captures_current else 0} current-APK screenshot drafts byte-validated. Native approvals: zero. Five fresh visual samples were reviewed and their exact hashes recorded; this is not a complete visual or native-language review.
- Supabase service-role-only quota RPC access verified; anon/authenticated execute denied; private quota RLS enabled. No customer identifiers are stored in that table. Security-advisor no-policy notice is intentional deny-all for normal roles. Existing project password warning was not changed.

Earlier failed locale/layout runs are retained as historical evidence. Their later success does not establish reliability on every device. Docker execution, an independent security audit, native-language review, legal certification and real LAT purchases remain unverified.
'''
    (ROOT/'docs/TEST_REPORT.md').write_text(text,encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['status','kotlinUnitTestsPassed','physicalDeviceTestsPassed','lint']}))

if __name__=='__main__':main()
