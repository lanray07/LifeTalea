"""Create an honest linguistic review queue; heuristics never approve a language."""
import csv
import re
from localize import ROOT, LOC, TARGETS, extract, read, write, leaves, source_hash

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
                row={'locale':locale,'key':key,'form':form,'source':original,'draft':text,'status':'NATIVE_REVIEW_REQUIRED','flags':';'.join(reasons)}
                rows.append(row)
                if reasons:flags.append({k:v for k,v in row.items() if k not in ['source','draft']})
    folder=ROOT/'deliverables/localization';folder.mkdir(exist_ok=True,parents=True)
    with (folder/'native-review-queue.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=['locale','key','form','source','draft','status','flags']);writer.writeheader();writer.writerows(rows)
    write(folder/'linguistic-flags.json',{'status':'PENDING_NATIVE_REVIEW','sourceHash':source_hash(source),'entries':len(rows),'heuristicFlagCount':len(flags),'flags':flags,'limitations':'These checks cannot establish meaning, dialect, grammar, pronunciation or release approval.'})
    from translate_collateral import flatten, FIELDS, HEADLINES
    website=read(ROOT/'website/src/dictionaries/en-GB.json')
    listing=read(ROOT/'deliverables/store-assets/metadata/en-GB/listing.json')
    collateral={'website':flatten(website),'store':flatten({**{key:listing[key] for key in FIELDS},'screenshotHeadlines':HEADLINES})}
    collateral_rows=[]
    for locale in TARGETS[1:]:
        target_listing=read(ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json')
        targets={'website':flatten(read(ROOT/f'website/src/dictionaries/{locale}.json')),'store':flatten({key:target_listing[key] for key in [*FIELDS,'screenshotHeadlines']})}
        for area,strings in collateral.items():
            for key,original in strings.items():
                collateral_rows.append({'locale':locale,'area':area,'key':key,'source':original,'draft':targets[area][key],'status':'NATIVE_REVIEW_REQUIRED'})
    with (folder/'collateral-native-review-queue.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(collateral_rows[0]));writer.writeheader();writer.writerows(collateral_rows)
    print(f'{len(rows)} native-review entries; {len(flags)} heuristic flags; zero approvals inferred')
    print(f'{len(collateral_rows)} website/store/headline review entries; zero approvals inferred')

if __name__=='__main__':main()
