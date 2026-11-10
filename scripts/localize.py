"""Development-only translation pipeline. No provider key or unreviewed website copy ships.
Usage: extract | translate --locale fr-FR | validate | generate --locale fr-FR
Review localization/reviews.json after native review; generation requires approval.
"""
import argparse, hashlib, json, os, re, sys, urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / 'localization'
TARGETS = ['en-GB','en-US','en-AU','es-ES','es-419','fr-FR','fr-CA','de-DE','it-IT','pt-BR','pt-PT','nl-NL','pl-PL','sv-SE','ja-JP','hi-IN','ar','tr-TR','id-ID','ko-KR','zh-Hans','zh-Hant']
PLACEHOLDER = re.compile(r'%(?:\d+\$)?[-+# 0,(]*\d*(?:\.\d+)?[a-zA-Z]|\{[a-zA-Z_][\w.]*\}')
def read(path, fallback=None): return json.loads(path.read_text(encoding='utf-8')) if path.exists() else fallback
def write(path, value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def source_hash(source): return hashlib.sha256(json.dumps(source,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def extract():
    tree = ET.parse(ROOT/'android/app/src/main/res/values/strings.xml')
    source = {}
    for node in tree.getroot():
        if node.tag == 'string': source[node.attrib['name']] = ''.join(node.itertext()).replace("\\'", "'")
        elif node.tag == 'plurals': source[node.attrib['name']] = {item.attrib['quantity']: ''.join(item.itertext()) for item in node}
    write(LOC/'en-GB.json',source); return source
def leaves(value):
    return value.items() if isinstance(value,dict) else [('value',value)]
def issues(source, translated):
    problems=[]
    if not isinstance(translated,dict): return ['catalog: invalid type']
    for key in translated.keys()-source.keys(): problems.append(f'{key}: unknown key')
    for key,value in source.items():
        if key not in translated: problems.append(f'{key}: missing'); continue
        target=translated[key]
        if type(value)!=type(target): problems.append(f'{key}: invalid type'); continue
        if isinstance(value,dict) and 'other' not in target: problems.append(f'{key}: missing plural other')
        if isinstance(target,dict):
            for quantity in target:
                if quantity not in ['zero','one','two','few','many','other']: problems.append(f'{key}: invalid plural category {quantity}')
        for quantity,actual in leaves(target):
            text = value.get(quantity,value.get('other','')) if isinstance(value,dict) else value
            if not isinstance(actual,str) or not actual.strip(): problems.append(f'{key}.{quantity}: empty'); continue
            if sorted(PLACEHOLDER.findall(text))!=sorted(PLACEHOLDER.findall(actual)): problems.append(f'{key}.{quantity}: placeholders differ')
            if 'LifeTalea' in text and 'LifeTalea' not in actual: problems.append(f'{key}: protected brand changed')
    return problems
def translate(locale, source):
    key=os.environ.get('DEEPL_AUTH_KEY')
    if not key: raise RuntimeError('BLOCKED: DEEPL_AUTH_KEY is unavailable. Configure it in the development environment; never put it in the app.')
    endpoint=os.environ.get('DEEPL_API_URL','https://api-free.deepl.com/v2/translate')
    if endpoint not in ['https://api-free.deepl.com/v2/translate','https://api.deepl.com/v2/translate']: raise RuntimeError('Unapproved translation endpoint')
    cache=read(LOC/'cache.json',{}); output={}
    target={'es-419':'ES','en-AU':'EN-GB','fr-CA':'FR','zh-Hans':'ZH-HANS','zh-Hant':'ZH-HANT'}.get(locale,locale.upper())
    if target not in ['EN-GB','EN-US','PT-BR','PT-PT','ZH-HANS','ZH-HANT']: target=target.split('-')[0]
    for name,value in source.items():
        parts={}
        for quantity,text in leaves(value):
            digest=source_hash([locale,text])
            if digest not in cache:
                tokens=[]
                def protect(match): tokens.append(match.group()); return f'<x id="{len(tokens)-1}">{escape(match.group())}</x>'
                protected=PLACEHOLDER.sub(protect,escape(text)).replace('LifeTalea','<x>LifeTalea</x>')
                payload=json.dumps({'text':[f'<root>{protected}</root>'],'source_lang':'EN','target_lang':target,'tag_handling':'xml','ignore_tags':['x']}).encode()
                request=urllib.request.Request(endpoint,data=payload,headers={'Authorization':f'DeepL-Auth-Key {key}','Content-Type':'application/json'})
                with urllib.request.urlopen(request,timeout=40) as response: result=json.load(response)['translations'][0]['text']
                cache[digest]=''.join(ET.fromstring(result).itertext()); write(LOC/'cache.json',cache)
            parts[quantity]=cache[digest]
        output[name]=parts if isinstance(value,dict) else parts['value']
    errors=issues(source,output)
    if errors: raise RuntimeError('\n'.join(errors))
    write(LOC/f'{locale}.json',output)
    reviews=read(LOC/'reviews.json',{}); reviews[locale]={'sourceHash':source_hash(source),'status':'MACHINE_TRANSLATED_PENDING_REVIEW','reviewer':'','reviewedAt':''}; write(LOC/'reviews.json',reviews)
def approved(locale,source,target):
    review=read(LOC/'reviews.json',{}).get(locale,{})
    return (review.get('status')=='APPROVED' and review.get('sourceHash')==source_hash(source)
            and review.get('targetHash')==source_hash(target) and bool(review.get('reviewer')) and bool(review.get('reviewedAt')))

def resource_xml(target):
    lines=['<resources>']
    for name,value in target.items():
        def android(text): return escape(text).replace('\\','\\\\').replace("'","\\'").replace('"','\\"').replace('@','\\@').replace('?','\\?').replace('\n','\\n')
        if isinstance(value,dict): lines += [f'<plurals name="{name}">']+[f'<item quantity="{q}">{android(v)}</item>' for q,v in value.items()]+['</plurals>']
        else: lines.append(f'<string name="{name}">{android(value)}</string>')
    lines.append('</resources>'); return '\n'.join(lines)

def generate(locale,source,draft=False):
    target=read(LOC/f'{locale}.json',{}); errors=issues(source,target)
    if errors: raise RuntimeError('BLOCKED: incomplete translation: '+'; '.join(errors[:10]))
    if not draft and not approved(locale,source,target): raise RuntimeError('BLOCKED: native review for the current source and target hashes is required')
    qualifier='values-b+'+'+'.join(locale.split('-'))
    folder=ROOT/f'android/app/src/{"debug" if draft else "main"}/res'/qualifier; folder.mkdir(exist_ok=True,parents=True)
    (folder/'strings.xml').write_text(resource_xml(target),encoding='utf-8')

def check_release(source):
    root=ROOT/'android/app/src/main/res'
    expected=['en-GB']
    for folder in root.glob('values-*'):
        file=folder/'strings.xml'
        if not file.exists():continue
        locale=folder.name.removeprefix('values-b+').replace('+','-')
        if locale not in TARGETS:raise RuntimeError(f'Untracked release locale: {folder.name}')
        target=read(LOC/f'{locale}.json',{})
        if issues(source,target) or not approved(locale,source,target):raise RuntimeError(f'Unreviewed or stale release translation: {locale}')
        if file.read_text(encoding='utf-8')!=resource_xml(target):raise RuntimeError(f'Release XML differs from reviewed catalogue: {locale}')
        expected.append(locale)
    actual=[item.text for item in ET.parse(root/'values/locales.xml').getroot().find('string-array')]
    declared=[item.attrib['{http://schemas.android.com/apk/res/android}name'] for item in ET.parse(root/'xml/locales_config.xml').getroot()]
    if set(actual)!=set(expected) or set(declared)!=set(expected):raise RuntimeError('Release language picker/configuration does not match reviewed resources')
    print('Release locale isolation: PASS')

def configure_locales(source):
    for variant in ['main','debug']:
        enabled=['en-GB']
        for locale in TARGETS[1:]:
            target=read(LOC/f'{locale}.json',{})
            path=ROOT/f'android/app/src/{variant}/res'/('values-b+'+'+'.join(locale.split('-')))/'strings.xml'
            if path.exists() and not issues(source,target) and (variant=='debug' or approved(locale,source,target)): enabled.append(locale)
        root=ROOT/f'android/app/src/{variant}/res'
        (root/'xml').mkdir(exist_ok=True,parents=True);(root/'values').mkdir(exist_ok=True,parents=True)
        (root/'xml/locales_config.xml').write_text('<locale-config xmlns:android="http://schemas.android.com/apk/res/android">\n'+''.join(f'  <locale android:name="{tag}" />\n' for tag in enabled)+'</locale-config>\n',encoding='utf-8')
        (root/'values/locales.xml').write_text('<resources>\n<string-array name="supported_locale_tags" translatable="false">\n'+''.join(f'  <item>{tag}</item>\n' for tag in enabled)+'</string-array>\n</resources>\n',encoding='utf-8')
def report(source):
    reviews=read(LOC/'reviews.json',{}); rows=[]
    for locale in TARGETS:
        target=read(LOC/f'{locale}.json',{}); errors=issues(source,target); invalid={e.split(':')[0].split('.')[0] for e in errors}; count=sum(key not in invalid for key in source)
        assets=ROOT/f'deliverables/store-assets/screenshots/localized-drafts/{locale}'
        rows.append({'locale':locale,'translatedKeys':count,'totalKeys':len(source),'coverage':round(count/len(source)*100,2),'review':reviews.get(locale,{}).get('status','SOURCE' if locale=='en-GB' else 'PENDING'),'releaseApproved':approved(locale,source,target),'debugResource':(ROOT/'android/app/src/debug/res'/('values-b+'+'+'.join(locale.split('-')))/'strings.xml').exists(),'issues':errors,'rtl':locale=='ar','voiceRecognition':'ENGLISH_COMMANDS_ONLY_DEVICE_DEPENDENT','tts':'DEVICE_DEPENDENT_NOT_TESTED','transcription':'ON_DEVICE_ENGINE_LANGUAGE_ACCURACY_PENDING','storeListing':'DRAFT_PENDING_NATIVE_REVIEW' if (ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json').exists() else 'MISSING','distributionCountries':'PENDING_PUBLISHER_SELECTION','screenshots':len(list(assets.glob('*.jpg'))),'screenshotReview':'DRAFT_PENDING_NATIVE_REVIEW','website':'DRAFT_PREVIEW' if (ROOT/f'website/src/dictionaries/{locale}.json').exists() else 'MISSING'})
    write(ROOT/'deliverables/localization/coverage.json',rows)
    report=ROOT/'deliverables/reports/LOCALIZATION_TEST_REPORT.md'
    report.write_text('# Localisation validation\n\nStructural coverage is measured separately from linguistic approval. Draft resources are debug-only. Native review is not implied by coverage.\n\n|Locale|Keys|Coverage|Review|\n|---|---:|---:|---|\n'+'\n'.join(f"|{r['locale']}|{r['translatedKeys']}/{r['totalKeys']}|{r['coverage']}%|{r['review']}|" for r in rows)+'\n\nDevice evidence and limitations: docs/LOCALIZATION.md.\n',encoding='utf-8')
    print(json.dumps({'sourceKeys':len(source),'targets':len(TARGETS),'fullyTranslated':sum(r['coverage']==100 for r in rows),'releaseApproved':sum(r['releaseApproved'] and r['coverage']==100 for r in rows)}))
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['extract','translate','validate','generate','check-release']); parser.add_argument('--locale',choices=TARGETS); parser.add_argument('--draft',action='store_true',help='Generate debug-only resources without claiming release approval'); parser.add_argument('--strict',action='store_true',help='Fail if any target catalogue has structural errors'); args=parser.parse_args()
    source=extract()
    if args.action in ['translate','generate']:
        if not args.locale: parser.error('--locale required')
        if args.action=='translate': translate(args.locale,source)
        else: generate(args.locale,source,args.draft); configure_locales(source)
    if args.action=='check-release':check_release(source)
    report(source)
    if args.action=='validate' and args.strict:
        invalid={locale:issues(source,read(LOC/f'{locale}.json',{})) for locale in TARGETS}
        invalid={locale:errors for locale,errors in invalid.items() if errors}
        if invalid: raise RuntimeError('Invalid catalogues: '+json.dumps(invalid,ensure_ascii=False))
if __name__=='__main__':
    try: main()
    except Exception as error: print(str(error),file=sys.stderr); sys.exit(1)
