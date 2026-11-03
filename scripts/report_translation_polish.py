"""Record field-level editorial changes against an explicit Git baseline."""
import argparse
from collections import Counter
import json
import subprocess
from localize import ROOT, TARGETS, read, write
from translate_collateral import flatten, FIELDS

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',required=True);args=parser.parse_args()
    baseline=subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','--verify',args.baseline+'^{commit}'],cwd=ROOT,text=True).strip()
    rows=[]
    for locale in TARGETS:
        for area,path in [('app',f'localization/{locale}.json'),('website',f'website/src/dictionaries/{locale}.json'),('store',f'deliverables/store-assets/metadata/{locale}/listing.json')]:
            original=json.loads(subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','show',baseline+':'+path],cwd=ROOT).decode('utf-8'))
            current=read(ROOT/path)
            if area=='store':original={key:original[key] for key in FIELDS};current={key:current[key] for key in FIELDS}
            original=flatten(original);current=flatten(current)
            for key,text in current.items():
                if original[key]!=text:rows.append({'locale':locale,'area':area,'key':key,'before':original[key],'after':text})
    counts=Counter(row['area'] for row in rows)
    output={'date':'2026-11-03','baselineCommit':baseline,'status':'DRAFT_PENDING_NATIVE_REVIEW','changedFields':len(rows),'counts':dict(counts),'changedLocales':sorted({row['locale'] for row in rows}),'nativeApprovalsAdded':0,'changes':rows}
    write(ROOT/'deliverables/localization/polish-changes.json',output)
    print(json.dumps({key:value for key,value in output.items() if key!='changes'}))

if __name__=='__main__':main()
