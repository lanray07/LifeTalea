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
    for key,value in source.items():
        if key not in translated: problems.append(f'{key}: missing'); continue
        target=translated[key]
        if type(value)!=type(target): problems.append(f'{key}: invalid type'); continue
        if isinstance(value,dict) and 'other' not in target: problems.append(f'{key}: missing plural other')
        for quantity,text in leaves(value):
            actual = target.get(quantity,'') if isinstance(target,dict) else target
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
def generate(locale,source):
    target=read(LOC/f'{locale}.json',{}); errors=issues(source,target)
    if errors: raise RuntimeError('BLOCKED: incomplete translation: '+'; '.join(errors[:10]))
    review=read(LOC/'reviews.json',{}).get(locale,{})
    if review.get('status')!='APPROVED' or review.get('sourceHash')!=source_hash(source): raise RuntimeError('BLOCKED: native review for the current source hash is required')
    qualifier='values-b+'+'+'.join(locale.split('-'))
    folder=ROOT/'android/app/src/main/res'/qualifier; folder.mkdir(exist_ok=True)
    lines=['<resources>']
    for name,value in target.items():
        def android(text): return escape(text).replace("'","\\'")
        if isinstance(value,dict): lines += [f'<plurals name="{name}">']+[f'<item quantity="{q}">{android(v)}</item>' for q,v in value.items()]+['</plurals>']
        else: lines.append(f'<string name="{name}">{android(value)}</string>')
    lines.append('</resources>'); (folder/'strings.xml').write_text('\n'.join(lines),encoding='utf-8')
def report(source):
    reviews=read(LOC/'reviews.json',{}); rows=[]
    for locale in TARGETS:
        target=read(LOC/f'{locale}.json',{}); errors=issues(source,target); count=len(source)-len({e.split(':')[0].split('.')[0] for e in errors})
        rows.append({'locale':locale,'translatedKeys':count,'totalKeys':len(source),'coverage':round(count/len(source)*100,2),'review':reviews.get(locale,{}).get('status','PENDING'),'issues':errors,'rtl':locale=='ar','voiceRecognition':'DEVICE_DEPENDENT_NOT_TESTED','tts':'DEVICE_DEPENDENT_NOT_TESTED','transcription':'BLOCKED_NO_ENGINE','storeListing':'PENDING_MARKETPLACE_MAPPING','distributionCountries':'PENDING_PUBLISHER_SELECTION','screenshots':'PENDING','website':'ENGLISH_PREVIEW' if locale=='en-GB' else 'PENDING'})
    write(ROOT/'deliverables/localization/coverage.json',rows)
    report=ROOT/'deliverables/reports/LOCALIZATION_TEST_REPORT.md'
    report.write_text('# Localisation validation\n\nOnly source coverage is measured; this is not language approval. No target translation credentials are configured.\n\n|Locale|Keys|Coverage|Review|\n|---|---:|---:|---|\n'+'\n'.join(f"|{r['locale']}|{r['translatedKeys']}/{r['totalKeys']}|{r['coverage']}%|{r['review']}|" for r in rows)+'\n\nRTL, font expansion, plural layout and native-language review remain required on devices.\n',encoding='utf-8')
    print(json.dumps({'sourceKeys':len(source),'targets':len(TARGETS),'fullyTranslated':sum(r['coverage']==100 for r in rows),'releaseApproved':sum(r['review']=='APPROVED' and r['coverage']==100 for r in rows)}))
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['extract','translate','validate','generate']); parser.add_argument('--locale',choices=TARGETS); args=parser.parse_args()
    source=extract()
    if args.action in ['translate','generate']:
        if not args.locale: parser.error('--locale required')
        (translate if args.action=='translate' else generate)(args.locale,source)
    report(source)
if __name__=='__main__':
    try: main()
    except Exception as error: print(str(error),file=sys.stderr); sys.exit(1)
