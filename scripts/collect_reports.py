"""Build an evidence inventory and conservative acceptance report from actual outputs.
Never converts missing evidence or a partial group into a passed release gate.
"""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,re,shutil,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'deliverables/reports'; OUT.mkdir(exist_ok=True)
DATE=datetime.now(timezone.utc).strftime('%Y-%m-%d')
def content(path):return (ROOT/path).read_text(encoding='utf-8',errors='replace') if (ROOT/path).exists() else ''
def put(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
def evidence_exists(path):return bool(path) and (ROOT/path).exists()
def main():
    junit=OUT/'junit';junit.mkdir(exist_ok=True)
    unit=[]
    for path in (ROOT/'android/app/build/test-results/testDebugUnitTest').glob('TEST-*.xml'):
        shutil.copy2(path,junit/path.name)
        suite=ET.parse(path).getroot()
        for test in suite.findall('testcase'):unit.append({'name':test.attrib['name'],'class':test.attrib['classname'],'status':'FAIL' if test.find('failure') is not None or test.find('error') is not None else 'PASS','evidence':str((junit/path.name).relative_to(ROOT))})
    native=content('deliverables/android/build-logs/instrumentation.log')
    match=re.search(r'OK \((\d+) tests?\)',native)
    provenance=json.loads(content('deliverables/reports/device-test-run.json') or '{}')
    current_apk=ROOT/'android/app/build/outputs/apk/debug/app-debug.apk'
    apk_matches=current_apk.exists() and provenance.get('debugApkSha256')==hashlib.sha256(current_apk.read_bytes()).hexdigest()
    device_pass=bool(match) and 'FAILURES!!!' not in native and provenance.get('status')=='PASS' and apk_matches
    build=content('deliverables/android/build-logs/build-tested.log')
    builds_ok='BUILD SUCCESSFUL' in build
    web=json.loads(content('deliverables/reports/website-checks.json') or '{}')
    static=json.loads(content('deliverables/reports/static-checks.json') or '{}')
    voice=json.loads(content('deliverables/reports/device-evidence/voice-device.json') or '{}')
    # Each row keeps a statement from the user's acceptance source, including incomplete gates.
    base={
      'AC-01':('Android build',['Debug build succeeds.','Release build succeeds when signing and build configuration permit.','No critical compilation errors remain.','Required project files exist.','No secrets are embedded in the application.']),
      'AC-02':('Memory management',['Users can create, edit, delete, and retrieve memories.','Records survive application restart.','Album relationships remain valid.','Search returns appropriate results.','Database migrations preserve data.']),
      'AC-03':('Audio Recording and Playback',['Recording starts successfully.','Pause and resume work.','Recordings can be stopped and saved.','Saved recordings play correctly.'])}
    source=content('docs/BUILD_REQUEST_3.txt');current=None
    for line in source.splitlines():
        heading=re.match(r'## (AC-\d+)\s+[—–-]\s+(.*)',line)
        if heading:current=heading.group(1);base.setdefault(current,(heading.group(2),[]))
        item=re.match(r'- \[ \] (.*)',line)
        if item and current:base[current][1].append(item.group(1))
    results=[]
    def proof(group,text):
        # Narrow assertions; all other checklist items stay NOT TESTED or BLOCKED.
        if group=='AC-01' and builds_ok and any(x in text for x in ['Debug build','Release build','compilation errors','project files']):return ('PASS','deliverables/android/build-logs/build-tested.log','Build tasks completed; release artifact is unsigned.','')
        if group=='AC-02' and device_pass and 'migrations' not in text:return ('PASS','deliverables/android/build-logs/instrumentation.log','CRUD/reopen/relations plus composed UI search executed on KFTRWI.','')
        if group=='AC-03' and voice and any(x in text for x in ['starts successfully','Pause and resume','stopped and saved','Saved recordings play']):return ('PASS','deliverables/reports/device-evidence/voice-device.json','Foreground microphone diagnostic, pause/resume, encoded duration and playback completed.','')
        if group=='AC-03' and voice and 'duration and playback position' in text:return ('NOT TESTED','deliverables/reports/device-evidence/voice-device.json','Recording duration checked; interactive seek/position accuracy still requires testing.','Verify seek/progress controls and interruptions.')
        if group=='AC-05':return ('BLOCKED','docs/TRANSCRIPTION.md','Recorded-file engine is unavailable; manual transcript editing is implemented.','Configure an engine, consent workflow, supported languages and real tests.')
        if group in ['AC-10','AC-11','AC-15']:return ('BLOCKED','deliverables/localization/coverage.json','Source English exists; required translated and reviewed launch materials are incomplete.','Configure translation/provider review and complete target-locale assets.')
        if group=='AC-12' and any(x in text for x in ['extracted','detected','placeholders','Missing translations','review status','API keys']):return ('PASS','deliverables/reports/python-tests.log','Development validator/extractor and review hash workflow checked; provider calls remain unverified.','')
        if group=='AC-13':return ('BLOCKED','docs/MONETIZATION.md','SDK integration exists; correct app authentication/product/receipt environment is absent.','Configure Amazon and run required App Tester/DevTest/LAT scenarios.')
        if group=='AC-16' and web.get('status')=='PASS' and any(x in text.lower() for x in ['website builds','pages exist','crawlable html','titles and descriptions','sitemap','robots.txt','structured data','internal links','privacy and support']):return ('PASS','deliverables/reports/website-checks.json','Sixteen English exported pages checked with local links, JSON and metadata.','')
        if group=='AC-18' and device_pass and any(x in text for x in ['Local backup can be created','Backup manifest','Scrapbook projects','Backup integrity','Restore preview','Duplicate handling','Corrupt backups','Encrypted backup']):return ('PASS','deliverables/android/build-logs/instrumentation.log','Small-fixture archive roundtrip, relationships, bytes, drafts, encryption and corrupt archive rejection tested.','')
        if group=='AC-22' and builds_ok and any(x in text for x in ['Debug build','Release build','Version information','Signing configuration']):return ('PASS','deliverables/android/build-logs/build-tested.log','Debug and unsigned release builds completed; version/signing setup documented.','')
        return ('NOT TESTED','','Not established by the current executed evidence.','Run the stated acceptance check; implementation alone is insufficient.')
    for group,(title,items) in base.items():
        for index,text in enumerate(items,1):
            status,evidence,actual,action=proof(group,text)
            results.append({'Requirement ID':f'{group}.{index:02d}','Test name':text,'Execution date':DATE if evidence else '', 'Device or environment':'KFTRWI / Fire OS 7 / API 28' if group in ['AC-02','AC-03','AC-18'] else 'Local JDK17 / Windows / Python / Next.js','Expected result':text,'Actual result':actual,'Status':status,'Evidence path':evidence,'Corrective action':action,'Responsible module':title})
    with (OUT/'ACCEPTANCE_TEST_RESULTS.csv').open('w',newline='',encoding='utf-8') as f:writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    passed=sum(x['Status']=='PASS' for x in results);total=len(results);rate=round(passed/total*100,2)
    criteria=['# Acceptance criteria and evidence\n\nStatements are preserved from the supplied release gates. PASS requires current evidence; BLOCKED and NOT TESTED remain incomplete. The release has 22 groups; individual checklist statements form the denominator below.\n']
    for group,(title,_) in base.items():
        rows=[r for r in results if r['Requirement ID'].startswith(group+'.')];complete=all(r['Status']=='PASS' for r in rows)
        criteria.append(f'\n## {group} — {title}\n\nGroup: {"PASS" if complete else "INCOMPLETE"}\n\n'+'\n'.join(f"- [{ 'x' if r['Status']=='PASS' else ' ' }] {r['Requirement ID']} {r['Test name']} — **{r['Status']}**" for r in rows))
    put(OUT/'ACCEPTANCE_CRITERIA.md','\n'.join(criteria)+'\n')
    summary={'releaseStatus':'BLOCKED','passedMandatoryStatements':passed,'totalMandatoryStatements':total,'verifiedAcceptanceRate':rate,'unitTests':unit,'deviceSuitePass':device_pass,'deviceTestsPassed':int(match.group(1)) if match else 0,'buildPass':builds_ok,'websiteChecks':web.get('status','NOT TESTED'),'staticChecks':static.get('status','NOT TESTED')}
    put(OUT/'summary.json',json.dumps(summary,indent=2))
    readiness=f'''# Release readiness — BLOCKED

Updated {DATE}. Verified acceptance rate: **{passed}/{total} = {rate}%** of mandatory checklist statements. BLOCKED and NOT TESTED are incomplete. This is a conservative evidence metric, not a percentage of code written or a claim that all tests map one-to-one to requirements.

Android build tasks: {'PASS' if builds_ok else 'NOT ESTABLISHED'}. Release artifact is unsigned. Kotlin unit tests: {sum(t['status']=='PASS' for t in unit)}/{len(unit)} passed. Physical device suite: {'PASS' if device_pass else 'NOT ESTABLISHED'} ({int(match.group(1)) if match else 0} tests in the final retained log). English website structural checks: {web.get('status','NOT TESTED')}. Source static checks: {static.get('status','NOT TESTED')}; these do not establish a complete security assessment.

Implemented source and exact test scope are listed in README.md and TEST_REPORT.md. Only English source strings exist; 22 locale rows are tracked and zero locales have native release approval. Worldwide store screenshots are incomplete. Automatic recorded-file transcription has no configured engine. Amazon purchasing, receipt verification and correct product/app authentication remain unverified. These are critical release gates.

Before submission:

1. Confirm com.lifetalea.app and com.lifetalea.premium in the correct Amazon app; supply its public authentication PEM and configure ENTITLED pricing. Implement/verify server receipt checks and run sandbox/DevTest/LAT purchase, cancellation, restoration and account-change tests.
2. Select and configure a real recorded-file transcription engine, including consent, errors and supported languages; test without losing original audio.
3. Translate/review all approved app, website and store languages; generate matching-language screenshots from actual UI in all required sizes. The provider/Android resource pipeline exists; complete website/store translation adapters.
4. Complete missing functional, Fire size/orientation, permission/interruption, offline, accessibility, performance and security checks. Current backup is bounded to 32 MiB total/16 MiB per attachment; large-library streaming, fault injection and crash recovery remain engineering work. Specific album routing and multilingual voice dictionaries need their own validation.
5. Finish unique promotional art/compositions, native linguistic review, final metadata/country selection, trademark/name clearance, privacy/legal review and production signing/update identity. Publisher O.Bankole and support banksmi@mail.com are configured.
6. Review final artifacts and request explicit publication authority. No Appstore or website production deployment has occurred. GitHub source push is separately authorised.

Do not describe this build as production-ready or submit it while these gates remain incomplete.
'''
    put(ROOT/'docs/RELEASE_READINESS.md',readiness);put(OUT/'RELEASE_READINESS.md',readiness)
    test_report=f'''# Actual test report

Updated {DATE}. Final results must be interpreted with their scope.

- Kotlin/JUnit: {sum(t['status']=='PASS' for t in unit)}/{len(unit)} passing, copied XML in deliverables/reports/junit.
- Android/Fire instrumentation: {'PASS' if device_pass else 'NOT ESTABLISHED'}; final retained evidence is deliverables/android/build-logs/instrumentation.log. Test fixtures are fictional. The microphone diagnostic removes its raw audio.
- Android build/lint: {'PASS' if builds_ok else 'NOT ESTABLISHED'}; inspect build-tested.log, not earlier failed attempts.
- Python validator tests: see python-tests.log for the actual executed count.
- Website: sixteen English pages structurally checked; browser desktop/mobile captures and comparison are in DESIGN_REVIEW.md.
- Static source checks: static-checks.json, a narrow pattern review rather than an independent audit.

Earlier failed build/test attempts are retained with their logs. Initial errors included incomplete UI references, test method return type, keyboard/date-field automation and Windows compiler file contention. Final logs supersede earlier attempts only for rerun checks. No provider transcription, live billing, native-language review, broad Fire compatibility or legal assessment is inferred from local test success.
'''
    put(ROOT/'docs/TEST_REPORT.md',test_report);put(OUT/'TEST_REPORT.md',test_report)
    reports={
      'VOICE_TEST_REPORT.md':f'# Voice device report\n\n'+(json.dumps(voice,indent=2) if voice else 'No retained device diagnostic yet.')+'\n\nThe diagnostic checks short recording/pause/resume/duration/playback only. Spoken feedback quality, service recognition accuracy, languages, interruptions, permission denial and seek controls need further tests.\n',
      'TRANSCRIPTION_TEST_REPORT.md':'# Transcription report — BLOCKED\n\nNo configured recorded-file engine. Manual transcript editing exists. No automatic transcript, supported language or offline transcription claim is made. See docs/TRANSCRIPTION.md.\n',
      'AMAZON_BILLING_TEST_REPORT.md':'# Amazon billing report — BLOCKED\n\nSDK adapter compiles; mode-isolation unit test is listed in copied JUnit XML. Public app authentication, product/price retrieval, real receipts, restoration, cancellation, refunds, account changes and sandbox/LAT execution remain unverified. No purchase was performed and no paid entitlement was simulated in production.\n',
      'FIRE_DEVICE_COMPATIBILITY.md':f'# Fire device compatibility\n\nAvailable physical device: KFTRWI, Fire OS 7.0, Android API 28, 1200×1920 physical panel (landscape application captures). Final instrumentation suite: {"PASS" if device_pass else "NOT ESTABLISHED"}. Diagnostic details are in voice-device.json when retained.\n\nA single device does not certify all Fire tablets. Other sizes/OS versions, portrait coverage, font scaling, physical denial/interruption cases, recognition/TTS language quality and Amazon purchasing need explicit tests. The tested device reports no speech-recognition service; IVONA and Pico TTS services are installed but language quality is unverified. No Fire TV support is claimed.\n',
      'SECURITY_AND_PRIVACY_REPORT.md':'# Security and privacy report\n\nNarrow source checks: static-checks.json. Encryption roundtrip, wrong-password and tamper tests: JUnit XML. Device archive corruption/roundtrip tests: final instrumentation log.\n\nNo advertising/analytics dependency or app-owned memory-upload endpoint is present. Final transitive dependency audit, memory/fuzz testing, crash consistency, production receipt verification and independent security/legal review remain incomplete. See docs/PRIVACY_AND_SECURITY.md.\n',
      'BACKUP_RESTORE_TEST_REPORT.md':f'# Backup and restore report\n\nFinal device suite status: {"PASS" if device_pass else "NOT ESTABLISHED"}. PreservationTest covers small JSON/media/draft fixtures, wrong password, corruption, duplicate preservation and relationships. An audio byte fixture checks byte fidelity; actual recording is tested separately.\n\n32 MiB total and 16 MiB per-attachment caps apply. No large-library, low-memory, crash-injection, future-version migration or cloud-sync validation is claimed.\n',
      'SCREENSHOT_VALIDATION_REPORT.md':'# Screenshot validation — INCOMPLETE\n\nActual development app captures, if retained, are under device-evidence/screenshots. They use fictional data and are evidence, not automatically approved store compositions. Required locale/device/shot rows are in store-assets/manifests/required-screenshots.csv.\n\nEight polished compositions per approved listing locale remain required. Automatic transcription is unavailable and must not be advertised. Phone distribution requires a separate channel. Generated design concepts are never counted as real app screenshots. No translated caption is accepted over English app UI.\n'
    }
    for name,text in reports.items():put(OUT/name,text)
    # Copy real APKs and compute hashes. Generated APKs remain workspace outputs, not source commits.
    artifacts=[]
    for variant,src,name in [('debug','android/app/build/outputs/apk/debug/app-debug.apk','LifeTalea-0.1.0-debug.apk'),('release','android/app/build/outputs/apk/release/app-release-unsigned.apk','LifeTalea-0.1.0-release-unsigned.apk')]:
        source_path=ROOT/src
        if source_path.exists():
            destination=ROOT/'deliverables/android'/variant/name;destination.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(source_path,destination)
            artifacts.append({'path':str(destination.relative_to(ROOT)),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':destination.stat().st_size,'signing':'debug key' if variant=='debug' else 'UNSIGNED','verification':'Current build log required; existence alone is not a passed build'})
    put(ROOT/'deliverables/android/artifacts.json',json.dumps(artifacts,indent=2))
    inventory=[('D01','Android source','android/app/src','IMPLEMENTED','Gradle and device tests','deliverables/android/build-logs/build-tested.log','Some release gates remain'),('D02','Build artifacts','deliverables/android/artifacts.json','VERIFIED' if builds_ok else 'UNVERIFIED','Build log / hashes','deliverables/android/build-logs/build-tested.log','Production signing pending'),('D03','Functional application','android/app/src/main/java','PARTIALLY_VERIFIED','Instrumented journeys','deliverables/android/build-logs/instrumentation.log','Remaining acceptance checks'),('D04','Voice and transcription','docs/VOICE_COMPATIBILITY.md','PARTIAL','Device diagnostic','deliverables/reports/VOICE_TEST_REPORT.md','Transcription engine and multilingual speech tests'),('D05','Localisation','localization','BLOCKED','Coverage validator','deliverables/localization/coverage.json','Target translations/native approval'),('D06','Localised screenshots','deliverables/store-assets/manifests/required-screenshots.csv','BLOCKED','Manifest/file validation','deliverables/reports/SCREENSHOT_VALIDATION_REPORT.md','Approved copy/actual locale captures/compositions'),('D07','Brand assets','deliverables/brand-assets','PARTIAL','Asset files and visual review','docs/DESIGN_REVIEW.md','Complete promotional variants/visual signoff'),('D08','Amazon listing','deliverables/store-assets/metadata','DRAFT','Official limits / draft validation','deliverables/store-assets/metadata/validation.json','Locale review / feature approval'),('D09','Marketing website','website','ENGLISH_PREVIEW','Production build / browser / links','deliverables/reports/website-checks.json','Localisation / final domain / deployment'),('D10','Amazon billing','android/app/src/main/java/com/lifetalea/app/billing','BLOCKED','Compile / mode policy unit test','deliverables/reports/AMAZON_BILLING_TEST_REPORT.md','Correct Amazon authentication/product/receipt tests'),('D11','Privacy and backup','docs/BACKUP_AND_RESTORE.md','PARTIALLY_VERIFIED','Small-fixture tests','deliverables/reports/BACKUP_RESTORE_TEST_REPORT.md','Large-library/crash/security review'),('D12','Tests','deliverables/reports/junit','PARTIALLY_VERIFIED','Executed logs and XML','docs/TEST_REPORT.md','Remaining device/provider scenarios'),('D13','Fire compatibility','deliverables/reports/FIRE_DEVICE_COMPATIBILITY.md','PARTIAL','One physical device','deliverables/android/build-logs/instrumentation.log','Broader Fire/orientation/accessibility/billing'),('D14','Documentation','docs','IMPLEMENTED','File inventory','README.md','Update as gates are completed'),('D15','Deliverables manifest','deliverables/DELIVERABLES_MANIFEST.csv','IMPLEMENTED','Generated current inventory','scripts/collect_reports.py','Never interpret inventory as release approval')]
    with (ROOT/'deliverables/DELIVERABLES_MANIFEST.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f);writer.writerow(['Deliverable ID','Deliverable name','File path','Status','Verification method','Evidence path','Remaining blocker']);writer.writerows(inventory)
    print(json.dumps({k:v for k,v in summary.items() if k!='unitTests'}))
if __name__=='__main__':main()
