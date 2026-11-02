"""Local, resumable website and Amazon listing drafts. Never publishes copy."""
import argparse
import copy
import hashlib
import re
from localize import ROOT, LOC, TARGETS, read, write, source_hash, issues
from local_translation import MODEL, REVISION, ORIGINAL, CONVERTED, PROTECTED, pieces

WEB=ROOT/'website/src/dictionaries'
STORE=ROOT/'deliverables/store-assets/metadata'
PATTERN=re.compile(PROTECTED.pattern+r'|https?://[^\s]+|\b(?:Android|AAC|M4A|SDKs?|Fire|KFTRWI|UK)\b')
FIELDS=['title','shortDescription','longDescription','featureBullets','keywords','releaseNotes']
HEADLINES={'home':'Keep the moments that matter','albums':'A collection for every chapter','timeline':'Follow your family’s timeline','keepsakes':'Bring stories into a keepsake','settings':'Keep a copy you control','editor':'Write the story behind the photo','voice':'Make room for their voice','transcript':'Add transcripts in your own words'}

def flatten(value,prefix=''):
    if isinstance(value,dict):
        return {path:text for key,child in value.items() for path,text in flatten(child,f'{prefix}.{key}' if prefix else key).items()}
    if isinstance(value,list):
        return {path:text for index,child in enumerate(value) for path,text in flatten(child,f'{prefix}.{index}').items()}
    if not isinstance(value,str):raise TypeError(f'{prefix}: expected editorial text')
    return {prefix:value}

def rebuild(template,translated,prefix=''):
    if isinstance(template,dict):return {key:rebuild(child,translated,f'{prefix}.{key}' if prefix else key) for key,child in template.items()}
    if isinstance(template,list):return [rebuild(child,translated,f'{prefix}.{index}') for index,child in enumerate(template)]
    return translated[prefix]

def segments(text):
    # Preserve paragraphs and sentence separators; shorter inputs reduce omissions.
    return [(protected,part) for sentence in re.split(r'(\n+|(?<=[.!?])\s+)',text) if sentence for protected,part in pieces(sentence,PATTERN)]

def file_hash(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    import ctranslate2
    import sentencepiece
    from opencc import OpenCC
    parser=argparse.ArgumentParser();parser.add_argument('--locale',choices=TARGETS,action='append');args=parser.parse_args()
    tokenizer=sentencepiece.SentencePieceProcessor(model_file=str(ORIGINAL/'sentencepiece.bpe.model'))
    translator=ctranslate2.Translator(str(CONVERTED),device='cpu',compute_type='int8',inter_threads=1,intra_threads=4)
    website=read(WEB/'en-GB.json');listing=read(STORE/'en-GB/listing.json')
    source={'website':website,'store':{**{key:listing[key] for key in FIELDS},'screenshotHeadlines':HEADLINES}}
    flat=flatten(source)
    cache=read(LOC/'local-cache.json',{});cache.update(read(LOC/'collateral-cache.json',{}))
    reviews_file=ROOT/'website/localization/reviews.json';reviews=read(reviews_file,{})
    validation=[]
    for locale in args.locale or TARGETS:
        language=locale.split('-')[0]
        if language=='en':
            def regional(text):return text.replace('Organise','Organize').replace('organise','organize').replace('favourite','favorite').replace('recognised','recognized') if locale=='en-US' else text
            translated={key:regional(text) for key,text in flat.items()}
        else:
            texts=sorted({part.strip() for text in flat.values() for protected,part in segments(text) if not protected and re.search('[A-Za-z]',part)})
            pending=[text for text in texts if source_hash([MODEL,REVISION,language,text]) not in cache]
            for offset in range(0,len(pending),16):
                batch=pending[offset:offset+16]
                tokens=[['__en__',*tokenizer.encode(text,out_type=str),'</s>'] for text in batch]
                results=translator.translate_batch(tokens,target_prefix=[[f'__{language}__']]*len(tokens),beam_size=3,max_batch_size=16,max_input_length=512,max_decoding_length=512,no_repeat_ngram_size=4)
                for text,result in zip(batch,results):
                    if len(result.hypotheses[0])>=512:raise RuntimeError(f'{locale}: possible truncated segment')
                    cache[source_hash([MODEL,REVISION,language,text])]=tokenizer.decode([token for token in result.hypotheses[0][1:] if token not in ['<s>','</s>','<pad>']]).strip()
                write(LOC/'collateral-cache.json',cache)
                print(f'{locale}: {min(offset+16,len(pending))}/{len(pending)} collateral segments',flush=True)
            translated={}
            for key,text in flat.items():
                output=[]
                for protected,part in segments(text):
                    if protected or not re.search('[A-Za-z]',part):output.append(part);continue
                    left=part[:len(part)-len(part.lstrip())];right=part[len(part.rstrip()):]
                    output.append(left+cache[source_hash([MODEL,REVISION,language,part.strip()])]+right)
                translated[key]=''.join(output)
            if language=='zh':
                converter=OpenCC('s2t' if locale=='zh-Hant' else 't2s')
                translated={key:converter.convert(text) for key,text in translated.items()}
        errors=issues(flat,translated)
        if errors:raise RuntimeError(f'{locale}: '+str(errors))
        result=rebuild(source,translated)
        app=read(LOC/f'{locale}.json',{})
        if locale!='en-GB':
            # Reuse corrected, matching app terminology for shared navigation.
            for web_key,app_key in [('privacy','privacy'),('support','support'),('language','language')]:
                if app_key in app:result['website']['ui'][web_key]=app[app_key]
            write(WEB/f'{locale}.json',result['website'])
        record={'status':'SOURCE' if locale=='en-GB' else 'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':file_hash(WEB/'en-GB.json'),'targetHash':file_hash(WEB/f'{locale}.json'),'reviewer':'','reviewedAt':'','generator':f'{MODEL}@{REVISION}; local inference; segmented prose','regionalReviewRequired':True}
        reviews[locale]=record;write(reviews_file,reviews)
        local_listing=copy.deepcopy(listing);local_listing.update(result['store']);local_listing.update({'locale':locale,'translationStatus':'DRAFT_PENDING_NATIVE_REVIEW','storeLocaleMapping':'PENDING_AMAZON_CONSOLE_LANGUAGE_SUPPORT','sourceHash':source_hash(source['store']),'targetHash':source_hash(result['store'])})
        if locale!='en-GB':write(STORE/locale/'listing.json',local_listing)
        else:write(STORE/'en-GB/screenshot-headlines.json',HEADLINES)
        checks={'title':len(local_listing['title'])<=200,'shortDescription':len(local_listing['shortDescription'])<=1200 and len(local_listing['shortDescription'].encode('utf-8'))<=2000,'longDescription':len(local_listing['longDescription'])<=4000,'featureBullets':3<=len(local_listing['featureBullets'])<=5}
        validation.append({'locale':locale,'websiteStrings':len(flatten(result['website'])),'storeStrings':len(flatten(result['store'])),'structuralIssues':errors,'storeLimits':checks,'review':'PENDING_NATIVE_REVIEW','releaseApproved':False})
        write(ROOT/'deliverables/localization/collateral-coverage.json',validation)
        if not all(checks.values()):raise RuntimeError(f'{locale}: store draft exceeds current Amazon form limits')
        print(f'{locale}: website and store draft saved',flush=True)

if __name__=='__main__':main()
