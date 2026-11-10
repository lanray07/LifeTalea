"""Create an honest linguistic review queue; heuristics never approve a language."""
import csv
import hashlib
import re
from localize import ROOT, LOC, TARGETS, extract, read, write, leaves, source_hash, approved

SCRIPTS={'ar':r'[\u0600-\u06ff]','hi':r'[\u0900-\u097f]','ja':r'[\u3040-\u30ff\u3400-\u9fff]','ko':r'[\uac00-\ud7af]','zh':r'[\u3400-\u9fff]'}
EXEMPT={'app_name','premium','date_hint'}

def main():
    source=extract();rows=[];flags=[]
    for locale in TARGETS[1:]:
        target=read(LOC/f'{locale}.json',{})
        for key,value in source.items():
            for form,text in leaves(target.get(key,{})):
                original=value.get(form,value.get('other','')) if isinstance(value,dict) else value
                reasons=[]
                if not locale.startswith('en') and key not in EXEMPT:
                    if text==original:reasons.append('UNCHANGED_SOURCE_REVIEW')
                    script=SCRIPTS.get(locale.split('-')[0])
                    if script and not re.search(script,text):reasons.append('EXPECTED_SCRIPT_MISSING')
                status='APPROVED_AI_EDITORIAL' if approved(locale,source,target) else 'EDITORIAL_REVIEW_REQUIRED'
                row={'locale':locale,'key':key,'form':form,'source':original,'draft':text,'status':status,'flags':';'.join(reasons)}
                rows.append(row)
                if reasons:flags.append({k:v for k,v in row.items() if k not in ['source','draft']})
    folder=ROOT/'deliverables/localization';folder.mkdir(exist_ok=True,parents=True)
    with (folder/'native-review-queue.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=['locale','key','form','source','draft','status','flags']);writer.writeheader();writer.writerows(rows)
    write(folder/'linguistic-flags.json',{'status':'HEURISTIC_FLAGS_FOR_REVIEW','sourceHash':source_hash(source),'entries':len(rows),'heuristicFlagCount':len(flags),'flags':flags,'limitations':'Heuristics do not approve copy. Current hash-bound editorial approvals are read from review records; AI review is not native-speaker certification.'})
    from translate_collateral import flatten, FIELDS, HEADLINES
    website=read(ROOT/'website/src/dictionaries/en-GB.json')
    listing=read(ROOT/'deliverables/store-assets/metadata/en-GB/listing.json')
    collateral={'website':flatten(website),'store':flatten({key:listing[key] for key in [*FIELDS,'screenshotHeadlines']})}
    review_files={'website':read(ROOT/'website/localization/reviews.json',{}),'store':read(LOC/'store-reviews.json',{})}
    def digest(area,locale):
        if area=='website':return hashlib.sha256((ROOT/f'website/src/dictionaries/{locale}.json').read_bytes()).hexdigest()
        value=read(ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json')
        return source_hash({key:value[key] for key in [*FIELDS,'screenshotHeadlines']})
    collateral_rows=[]
    for locale in TARGETS[1:]:
        target_listing=read(ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json')
        targets={'website':flatten(read(ROOT/f'website/src/dictionaries/{locale}.json')),'store':flatten({key:target_listing[key] for key in [*FIELDS,'screenshotHeadlines']})}
        for area,strings in collateral.items():
            review=review_files[area].get(locale,{})
            current=(review.get('status')=='APPROVED' and review.get('sourceHash')==digest(area,'en-GB') and review.get('targetHash')==digest(area,locale) and review.get('reviewer') and review.get('reviewedAt'))
            for key,original in strings.items():
                collateral_rows.append({'locale':locale,'area':area,'key':key,'source':original,'draft':targets[area][key],'status':'APPROVED_AI_EDITORIAL' if current else 'EDITORIAL_REVIEW_REQUIRED'})
    with (folder/'collateral-native-review-queue.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(collateral_rows[0]));writer.writeheader();writer.writerows(collateral_rows)
    print(f'{len(rows)} app review entries; {len(flags)} heuristic flags; approvals require current review records')
    print(f'{len(collateral_rows)} website/store/headline review entries; zero approvals inferred')

if __name__=='__main__':main()
