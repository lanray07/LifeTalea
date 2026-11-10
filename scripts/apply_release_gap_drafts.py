"""Apply authored release-gap strings; they remain drafts until native approval."""
import json
import xml.etree.ElementTree as ET
from localize import ROOT, TARGETS, read, write, source_hash, extract, generate, configure_locales, issues

def main():
    draft = read(ROOT / 'localization/release-gap-drafts.json')
    keys = draft['keys']
    assert len(keys) == len(set(keys))
    for texts in draft['languages'].values():
        assert len(texts) == len(keys) and all(texts)
    path = ROOT / 'android/app/src/main/res/values/strings.xml'
    tree = ET.parse(path)
    existing = {node.attrib.get('name'): node for node in tree.getroot()}
    for key, text in zip(keys, draft['languages']['en']):
        node = existing.get(key)
        if node is None: node = ET.SubElement(tree.getroot(), 'string', {'name': key})
        node.text = text.replace("'", "\\'")
    ET.indent(tree, space='    ')
    tree.write(path, encoding='utf-8', xml_declaration=True)
    source = extract()
    for locale in TARGETS:
        language = locale if locale.startswith('zh-') else locale.split('-')[0]
        target = read(ROOT / f'localization/{locale}.json')
        values = dict(zip(keys, draft['languages'][language]))
        if locale == 'pt-PT':
            values = {k:v.replace('mídia','multimédia').replace('usuário','utilizador').replace('aplicativo','aplicação').replace('registros','registos').replace('arquivos','ficheiros').replace('excluídos','eliminados') for k,v in values.items()}
        target.update(values)
        assert not issues(source, target), locale
        write(ROOT / f'localization/{locale}.json', target)
        generate(locale, source, True)
        web_path = ROOT / f'website/src/dictionaries/{locale}.json'
        web = read(web_path)
        body = web['articles']['privacy']['sections'][1]['body']
        # Replacing a previously appended paragraph keeps this operation idempotent.
        marker = '\n\n'
        web['articles']['privacy']['sections'][1]['body'] = body.split(marker)[0] + marker + values['purchase_privacy'] + marker + values['reminder_notice']
        write(web_path, web)
        listing_path = ROOT / f'deliverables/store-assets/metadata/{locale}/listing.json'
        listing = read(listing_path)
        if values['reminder_notice'] not in listing['longDescription']:
            listing['longDescription'] += '\n\n' + values['reminder_notice']
        assert len(listing['longDescription']) <= 4000, locale
        listing['status'] = 'DRAFT_NOT_SUBMISSION_READY'
        listing['targetHash'] = source_hash({key:listing[key] for key in ('title','shortDescription','longDescription','featureBullets','keywords','releaseNotes','screenshotHeadlines') if key in listing})
        write(listing_path, listing)
    configure_locales(source)
    print(json.dumps({'keys':len(source),'locales':len(TARGETS),'nativeApproval':False}))

if __name__ == '__main__': main()

