"""Reproducible offline translation drafts. No user memories or credentials are used.

--prepare downloads the pinned official MIT-licensed M2M100 model and converts it.
Inference then stays local. Outputs are debug-only and require native review.
"""
import argparse
import hashlib
import re
import time
from localize import ROOT, LOC, TARGETS, read, write, extract, source_hash, issues, generate, configure_locales, report, leaves, approved

MODEL = 'facebook/m2m100_418M'
REVISION = '55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636'
WEIGHT_SHA256 = 'd907ea45e4e4b9db163382a6674f6218b3c59566fe06d77f4055c208b4e87ed1'
MODELS = ROOT/'.translation-models'
ORIGINAL = MODELS/'m2m100-source'
CONVERTED = MODELS/'m2m100-int8'
# Preserve identifiers and format strings outside model inference, not by hoping
# a generated placeholder is retained. Sentence segments are cached separately.
PROTECTED = re.compile(r'LifeTalea Premium|LifeTalea|Amazon|O\.Bankole|banksmi@mail\.com|github\.com/lanray07/LifeTalea|Create a new memory|Open my timeline|Create a keepsake book|YYYY-MM-DD|YYYY-MM|YYYY|%\d+\$[ds]|%(?:d|s)|\b(?:PDF|TTS|MiB)\b|\d+(?:\.\d+)*')

def pieces(text,pattern=PROTECTED):
    result=[]; start=0
    for match in pattern.finditer(text):
        if match.start()>start: result.append((False,text[start:match.start()]))
        result.append((True,match.group()));start=match.end()
    if start<len(text):result.append((False,text[start:]))
    return result

def prepare():
    from huggingface_hub import snapshot_download
    from ctranslate2.converters import TransformersConverter
    files=['config.json','pytorch_model.bin','sentencepiece.bpe.model','vocab.json','tokenizer_config.json','special_tokens_map.json','README.md']
    if not all((ORIGINAL/name).exists() for name in files):
        snapshot_download(MODEL,revision=REVISION,local_dir=ORIGINAL,allow_patterns=files)
    digest=hashlib.sha256()
    with (ORIGINAL/'pytorch_model.bin').open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    if digest.hexdigest()!=WEIGHT_SHA256:raise RuntimeError('Official model weights checksum mismatch; remove the incomplete download and prepare again')
    if not (CONVERTED/'model.bin').exists():
        TransformersConverter(str(ORIGINAL),load_as_float16=False).convert(str(CONVERTED),quantization='int8')
    print('Pinned official model prepared locally',flush=True)

def run(locales):
    import ctranslate2
    import sentencepiece
    from opencc import OpenCC
    # Equivalent to the pinned M2M100Tokenizer: SentencePiece pieces wrapped
    # by the source language token and EOS. Avoid importing the training stack
    # during inference (particularly expensive on Windows).
    tokenizer=sentencepiece.SentencePieceProcessor(model_file=str(ORIGINAL/'sentencepiece.bpe.model'))
    translator=ctranslate2.Translator(str(CONVERTED),device='cpu',compute_type='int8',inter_threads=1,intra_threads=4)
    source=extract();cache=read(LOC/'local-cache.json',{})
    corrections=read(LOC/'terminology.json',{})
    voice_notices=read(LOC/'voice-notices.json',{})
    editorial=read(LOC/'editorial-drafts.json',{})
    navigation=read(LOC/'navigation-drafts.json',{})
    reviews=read(LOC/'reviews.json',{})
    for locale in locales:
        if approved(locale,source,read(LOC/f'{locale}.json',{})):
            print(f'{locale}: preserving current native-approved catalogue',flush=True);continue
        started=time.monotonic();lang=locale.split('-')[0]
        if lang=='en':
            def regional(text):return text.replace('Organise','Organize').replace('organise','organize').replace('favourite','favorite').replace('recognised','recognized') if locale=='en-US' else text
            target={k:({q:regional(t) for q,t in v.items()} if isinstance(v,dict) else regional(v)) for k,v in source.items()}
        else:
            overrides={**corrections.get(lang,{}),**navigation.get(lang,{}),**editorial.get(lang,{})}
            overrides['voice_notice']=voice_notices[lang]
            remaining={key:value for key,value in source.items() if key not in overrides}
            texts=sorted({part.strip() for value in remaining.values() for _,text in leaves(value) for protected,part in pieces(text) if not protected and re.search(r'[A-Za-z]',part)})
            pending=[text for text in texts if source_hash([MODEL,REVISION,lang,text]) not in cache]
            for offset in range(0,len(pending),16):
                batch=pending[offset:offset+16]
                tokens=[['__en__',*tokenizer.encode(text,out_type=str),'</s>'] for text in batch]
                results=translator.translate_batch(tokens,target_prefix=[[f'__{lang}__']]*len(tokens),beam_size=3,max_batch_size=16,max_input_length=512,max_decoding_length=512,no_repeat_ngram_size=4)
                for text,result in zip(batch,results):
                    if len(result.hypotheses[0])>=512:raise RuntimeError('Possible truncated translation')
                    cache[source_hash([MODEL,REVISION,lang,text])]=tokenizer.decode([token for token in result.hypotheses[0][1:] if token not in ['</s>','<s>','<pad>']]).strip()
                write(LOC/'local-cache.json',cache)
                print(f'{locale}: {min(offset+16,len(pending))}/{len(pending)} new segments',flush=True)
            def translated(text):
                output=[]
                for protected,part in pieces(text):
                    if protected or not re.search(r'[A-Za-z]',part):output.append(part);continue
                    leading=part[:len(part)-len(part.lstrip())];trailing=part[len(part.rstrip()):]
                    output.append(leading+cache[source_hash([MODEL,REVISION,lang,part.strip()])]+trailing)
                return ''.join(output)
            target={k:(overrides[k] if k in overrides else {q:translated(t) for q,t in v.items()} if isinstance(v,dict) else translated(v)) for k,v in source.items()}
            target.update(corrections.get(lang,{}))
            target.update(navigation.get(lang,{}))
            target['voice_notice']=voice_notices[lang]
            target.update(editorial.get(lang,{}))
            if lang=='zh':
                convert=OpenCC('s2t' if locale=='zh-Hant' else 't2s')
                target={k:({q:convert.convert(t) for q,t in v.items()} if isinstance(v,dict) else convert.convert(v)) for k,v in target.items()}
                if locale=='zh-Hant':target.update({'albums':'相簿','album_title':'相簿名稱','album_members':'相簿中的回憶','memory_count':{'other':'%1$d 則回憶'}})
            if locale=='pt-PT':
                target.update({'settings':'Definições','save':'Guardar','delete':'Eliminar','story':'A sua história','timeline':'Cronologia'})
        errors=issues(source,target)
        if errors:raise RuntimeError(f'{locale}: '+'; '.join(errors))
        write(LOC/f'{locale}.json',target)
        reviews[locale]={'status':'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':source_hash(source),'targetHash':source_hash(target),'reviewer':'','reviewedAt':'','generator':'Codex English regional adaptation' if lang=='en' else f'{MODEL}@{REVISION}; local int8; terminology corrections','regionalReviewRequired':True}
        write(LOC/'reviews.json',reviews);generate(locale,source,draft=True)
        print(f'{locale}: {len(target)} draft keys in {time.monotonic()-started:.1f}s',flush=True)
    configure_locales(source);report(source)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--locale',choices=TARGETS,action='append');args=parser.parse_args()
    if args.prepare:prepare()
    else:run(args.locale or TARGETS[1:])
