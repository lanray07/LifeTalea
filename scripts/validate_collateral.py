"""Check draft completeness and metadata limits without approving language quality."""
import json
from localize import ROOT, LOC, TARGETS, read, write, issues
from translate_collateral import flatten, FIELDS, HEADLINES

def main():
    source_web=read(ROOT/'website/src/dictionaries/en-GB.json')
    source_store=read(ROOT/'deliverables/store-assets/metadata/en-GB/listing.json')
    rows=[];failures=[]
    for locale in TARGETS:
        web=read(ROOT/f'website/src/dictionaries/{locale}.json',{})
        listing=read(ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json',{})
        web_errors=issues(flatten(source_web),flatten(web))
        source_fields={key:source_store[key] for key in FIELDS}
        target_fields={key:listing.get(key,'') for key in FIELDS}
        store_errors=issues(flatten(source_fields),flatten(target_fields))
        for field,limit in [('title',200),('shortDescription',1200),('longDescription',4000)]:
            if not isinstance(listing.get(field),str) or len(listing[field])>limit:store_errors.append(f'{field}: invalid Amazon draft length')
        if isinstance(listing.get('shortDescription'),str) and len(listing['shortDescription'].encode('utf-8'))>2000:store_errors.append('shortDescription: exceeds 2000 UTF-8 bytes')
        if not isinstance(listing.get('featureBullets'),list) or not 3<=len(listing['featureBullets'])<=5:store_errors.append('featureBullets: expected 3 to 5')
        headline=read(ROOT/'deliverables/store-assets/metadata/en-GB/screenshot-headlines.json',{}) if locale=='en-GB' else listing.get('screenshotHeadlines',{})
        headline_errors=issues(HEADLINES,headline)
        rows.append({'locale':locale,'websiteKeys':len(flatten(web)),'websiteIssues':web_errors,'storeIssues':store_errors,'screenshotHeadlineIssues':headline_errors,'nativeApproval':False})
        failures.extend(f'{locale}: {message}' for message in [*web_errors,*store_errors,*headline_errors])
    write(ROOT/'deliverables/localization/collateral-validation.json',{'status':'FAIL' if failures else 'PASS','rows':rows,'errors':failures,'scope':'Structural checks and current Amazon form lengths; regional, legal, keyword and native-language review remain pending.'})
    print(json.dumps({'status':'FAIL' if failures else 'PASS','locales':len(rows),'errors':failures},ensure_ascii=False))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
