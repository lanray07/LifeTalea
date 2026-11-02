"""Apply draft editorial corrections while preserving native-review gates."""
import re
from localize import ROOT,LOC,TARGETS,read,write,source_hash
from translate_collateral import flatten,rebuild,file_hash,FIELDS

def main():
    from opencc import OpenCC
    source=read(ROOT/'website/src/dictionaries/en-GB.json');source_flat=flatten(source)
    store_source=read(ROOT/'deliverables/store-assets/metadata/en-GB/listing.json')
    store_flat=flatten({key:store_source[key] for key in FIELDS})
    corrections=read(LOC/'web-editorial-drafts.json')
    landing=read(LOC/'landing-drafts.json',{})
    headlines=read(LOC/'screenshot-headlines-drafts.json',{})
    reviews_path=ROOT/'website/localization/reviews.json';reviews=read(reviews_path,{})
    for locale in TARGETS:
        if locale.startswith('en'):continue
        language=locale.split('-')[0];values=corrections[language].copy()
        if language=='zh':
            converter=OpenCC('s2t' if locale=='zh-Hant' else 't2s');values={key:converter.convert(value) for key,value in values.items()}
        file=ROOT/f'website/src/dictionaries/{locale}.json';dictionary=read(file)
        if not dictionary:raise RuntimeError(f'Missing {locale} website draft')
        translated=flatten(dictionary)
        for key,text in translated.items():
            if 'passphrase' in source_flat[key].lower():translated[key]=re.sub(re.escape(values['passport']),values['passphrase'],text,flags=re.IGNORECASE)
        dictionary=rebuild(source,translated)
        for section,fields in landing.get(language,{}).items():
            if language=='zh':fields={key:converter.convert(value) for key,value in fields.items()}
            dictionary[section].update(fields)
        dictionary['home'].update({'titleFirst':values['first'],'titleSecond':values['second'],'metaTitle':values['title']})
        dictionary['ui']['previewNotice']=values['notice']
        write(file,dictionary)
        reviews[locale].update({'status':'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':file_hash(ROOT/'website/src/dictionaries/en-GB.json'),'targetHash':file_hash(file),'reviewer':'','reviewedAt':'','editorialCorrections':'Codex draft headlines, titles, review notice and passphrase terminology; not native approval'})
        listing_file=ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json';listing=read(listing_file)
        listing_fields=flatten({key:listing[key] for key in FIELDS})
        for key,text in listing_fields.items():
            if 'passphrase' in store_flat[key].lower():listing_fields[key]=re.sub(re.escape(values['passport']),values['passphrase'],text,flags=re.IGNORECASE)
        listing.update(rebuild({key:store_source[key] for key in FIELDS},listing_fields));listing['title']=values['title']
        listing['screenshotHeadlines']=headlines[language]
        if language=='zh':listing['screenshotHeadlines']={key:converter.convert(value) for key,value in listing['screenshotHeadlines'].items()}
        listing['targetHash']=source_hash({key:listing[key] for key in [*FIELDS,'screenshotHeadlines']})
        write(listing_file,listing)
    write(reviews_path,reviews)
    print('Draft collateral corrections applied; no native approvals added')

if __name__=='__main__':main()
