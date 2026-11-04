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
        'serverDeployed':False,'liveAmazonRvsTested':False,'livePurchaseTestsPassed':False,'dockerImageBuilt':False,'productionSigningIdentityCreated':False,
        'defaultReleaseConfiguration':inspection['generatedReleaseBillingConfiguration'],
        'serverSourceSha256':{name:sha(ROOT/f'server/receipt-verifier/{name}') for name in SERVER_FILES},
        'remaining':'Deploy/configure a private HTTPS verifier and public app pin; create/approve IAP/prices; real Amazon transaction tests; independent security/privacy/legal/native and remaining product/device gates.'}
    (REPORTS/'amazon-rvs-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    readiness=f'''# Release readiness — BLOCKED

Updated 4 November 2026. [Current billing implementation](AMAZON_RVS_IMPLEMENTATION.md) and [remaining gates](AMAZON_OWNER_ACTIONS.md). The original 258-statement acceptance checklist remains in scope; no new completion percentage is inferred from test counts.

Server RVS and the signed Android client are implemented and tested locally. The default release still has no verifier endpoint/public pin and purchases are off. The server has not been deployed, no real Amazon secret/deployment signing identity was configured, and no real purchase/refund/restore/LAT result is claimed. The last console inspection found zero IAP products; no account fields, prices or uploads were changed during this local phase.

Current evidence: **{node_pass} server tests, {units} Kotlin unit tests, {device_count} physical Fire tests** passed; the Fire suite includes {len(contract)} receipt/signature/config tests. Lint: {lint['Error']} errors, {lint['Warning']} warnings. Portrait/landscape at 1.3× text and Wi-Fi-disabled home reopen passed, with all original QA settings restored. Resource/catalogue, website/type and metadata/editorial checks passed; native approvals remain zero. {screenshot_note}

Two RVS physical attempts passed the new receipt tests but failed the locale test with a detached Compose hierarchy, first at capture and then after opening a story. Both failed logs are retained. The corrected test adds bounded waits after destination navigation as well as before capture, and fixes the test orientation. These changes address observed readiness preconditions; broader device/test reliability remains open.

Remaining gates: real backend/credential/TLS/public-pin and Amazon product/price configuration plus actual purchase/refund/account/offline tests; real recorded-file transcription; native review/matching release assets; remaining product/streaming/crash recovery, device/accessibility/performance work; independent server/client security assessment and privacy/legal/export/signing approval. Docker image execution is not verified because no Docker CLI was available. The new identifier-processing flow also needs final questionnaire/legal review. No Amazon submission occurred.
'''
    (ROOT/'docs/RELEASE_READINESS.md').write_text(readiness,encoding='utf-8')
    text=f'''# Actual test report — Amazon RVS follow-up, 4 November 2026

- Server: **{node_pass}/{node_count} passing** local contract/crypto/HTTP/startup/rate/timeout/key-helper tests. Actual TAP log: {row['log']}. No live Amazon call or real credential is used. The deployment package also runs this suite after extracting its verified contents into an isolated temporary directory; see package-index.json.
- Android build: current amazon-rvs-build.log passed debug/release/test builds, unit tests and lint. Gradle can reuse unchanged tasks/results. Actual release inspection verifies package/version/API, non-debuggable unsigned state, existing Amazon public PEM, both Amazon visibility declarations and absence of test receipt fixtures in the release APK. Generated default release configuration has no verifier URL/pin and purchases off.
- Kotlin: **{units} passing** tests, current JUnit XML under deliverables/reports/junit. Billing cases include account generations, stale responses, revocation/order, empty restore, expiry, environment/SKU/time bounds, invalid identities and monotonic time under wall-clock changes.
- Physical KFTRWI / Fire HD 10 (2021), Fire OS 7/API 28: **{device_count} passing** tests in {seconds} seconds. This includes {len(contract)} receipt tests: Node-signed assertions on actual Android RSA/JSON, tampering/wrong signer/schema, sandbox/endpoint rejection and rejection of legacy Premium preferences. The other tests cover writing/organising, private media/preservation/backup/PDF, short real microphone recording/playback/seek and the 22-locale capture matrix. Raw microphone data is deleted.
- Layout smoke: three passing home-screen cases, portrait/landscape at 1.3× text and Wi-Fi-disabled reopen. This does not certify all screens, font scales, assistive technology, prolonged offline operation or configured Premium's reboot/offline behavior. Power, rotation, font and Wi-Fi settings were restored; current provenance records the outer batch and inner restoration.
- Collateral checks: all {len(checks['checks'])} groups passed, including Python tests, 22 × 191 app keys, release-locale isolation, authored-copy regression, metadata constraints, browser-locale/review-gate/static-export regressions, TypeScript, 352 exported pages and narrow source patterns. Native-language approval remains absent.
- Lint: **{lint['Error']} errors, {lint['Warning']} warnings**. The independent security assessment is still pending; static patterns and these tests do not replace it.

Two RVS device attempts each ran 17 tests and passed all four new receipt tests, but failed the locale test with No compose hierarchies, first at capture and then at the record control after navigation. Both failed logs are retained as amazon-rvs-device-first-failed.log and amazon-rvs-device-navigation-failed.log. The corrected test adds bounded destination/current-locale/root readiness waits and a stable landscape precondition; functional assertions still fail normally. Its incremental test-only build is recorded in amazon-rvs-test-readiness-build.log. Earlier pre-RVS startup timeout logs are retained and are not declared fixed by a successful retry.

The first layout batch after the 17-test pass completed both larger-text orientations, then UI Automator returned an error while dumping the offline screen. The failed log/result are retained. The dump operation now participates in an eight-attempt readiness loop after repeated null roots were reproduced on 4 November in both dump modes; regression tests reproduce failure at the old three-attempt bound and recovery with a valid fourth tree. No missing tree or failed bounds assertion is accepted as a pass. Consult the current layout result for the executed device outcome. Five recorded visual samples are recorded in amazon-rvs-visual-samples.json; they are not native approval or a full visual audit.

These results do not certify real Amazon RVS credentials, SDK transaction callbacks, deployed HTTPS behavior, marketplace products/prices, live purchase/refund/restore, LAT approval, native linguistic quality, a full device/security assessment or legal approval. See AMAZON_RVS_IMPLEMENTATION.md and AMAZON_OWNER_ACTIONS.md.
'''
    if not complete or not layout_current:
        fire_note='All current instrumentation tests passed, including the corrected full 22-locale capture test.' if complete else 'The locale UI test failed, and the later test-only readiness update has not been executed.'
        asset_note=screenshot_note if captures_current and complete else 'Current screenshot assets are omitted until the full capture run and byte validation pass.'
        layout_note=f"The separate current-app layout smoke is {layout.get('status')}: {len(layout.get('cases',[]))} cases completed; failure: {layout.get('failure')}." if layout.get('debugApkSha256')==run['debugApkSha256'] else 'The layout smoke has not been verified on the current app.'
        warning=f'''# Current RVS evidence — UI QA INCOMPLETE / release BLOCKED

{node_pass} server tests and {units} unit tests passed. The last physical run on the current debug app passed {device_count}/{total}, including all {len(contract)} receipt tests. {fire_note} {layout_note} Original QA settings were restored.

{asset_note} A fresh unlocked-device layout/offline check remains required. This report records incomplete QA; it does not waive a release gate.

Server RVS/client implementation and local tests are complete enough to review; deployment, real credentials/TLS/public pin, product/prices, live Amazon transactions and independent security/privacy/legal/native/remaining product gates remain open. No deployment or submission occurred. See AMAZON_RVS_IMPLEMENTATION.md and amazon-rvs-verification.json for exact hashes and scope.
'''
        (ROOT/'docs/RELEASE_READINESS.md').write_text(warning,encoding='utf-8')
        text=warning+f'''\n## Executed evidence

- Node server: {node_pass}/{node_count} local contract/crypto/HTTP/startup/key-helper tests. No real Amazon receipts or credentials.
- Kotlin unit tests: {units} passing, current JUnit XML retained.
- Fire: {device_count}/{total} passed on the current debug app, including all {len(contract)} signed-receipt tests. {fire_note}
- Android build: debug/release/test APKs and lint completed in amazon-rvs-build.log; the later test-only build is amazon-rvs-test-readiness-build.log. Lint: {lint['Error']} errors and {lint['Warning']} warnings. Release is unsigned, verifier URL/pin empty, and purchases off.
- All {len(checks['checks'])} non-device collateral groups passed: server/Python tests, locale resources/isolation, authored-copy checks, metadata, browser locale/review/static-export regressions, TypeScript, exported website structure and narrow source patterns. These are not independent security or native linguistic approval.
- Screenshots: {asset_note} The validator requires a passing current full run and per-capture byte hashes for a refresh. Native approvals remain zero.
- Layout/offline: {layout_note}

Current instrumentation evidence is in instrumentation.log. Historical locale failures are retained in amazon-rvs-device-first-failed.log and amazon-rvs-device-navigation-failed.log. The layout capture failure is retained in amazon-rvs-layout-first-failed.log. The follow-up locked-device preflight changed no settings; the corrected capture retry has not completed on the tablet. Original power/rotation/font/Wi-Fi settings from the executed runs were restored. Docker execution and independent security assessment remain unverified.
'''
    (ROOT/'docs/TEST_REPORT.md').write_text(text,encoding='utf-8')
    print(json.dumps({key:result[key] for key in ['status','kotlinUnitTestsPassed','physicalDeviceTestsPassed','lint']}))

if __name__=='__main__':main()
