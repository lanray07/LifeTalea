"""Validate actual screenshot exports, dimensions and provenance; never approve copy."""
import csv
import hashlib
import argparse
from PIL import Image, ImageStat, ImageChops
from localize import ROOT, read, write

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true',help='Bind newly rendered captures to a passing current device run.');args=parser.parse_args()
    folder=ROOT/'deliverables/store-assets/screenshots/localized-drafts'
    previous=read(folder/'provenance.json',{})
    known={row['asset']:row for row in previous.get('assets',[])}
    run=read(ROOT/'deliverables/reports/device-test-run.json')
    if args.refresh:
        if run.get('status')!='PASS':raise RuntimeError('A passing full device run is required before refreshing screenshot provenance')
        for key,path in [('debugApkSha256','android/app/build/outputs/apk/debug/app-debug.apk'),('testApkSha256','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')]:
            if run.get(key)!=digest(ROOT/path):raise RuntimeError('Device evidence does not match the current APKs')
        fresh={row['path']:row['sha256'] for row in run.get('evidence',[])}
    elif not previous.get('debugApkSha256'):
        raise RuntimeError('No previous provenance exists; use --refresh after a complete device run')
    rows=list(csv.DictReader((folder/'manifest.csv').open(encoding='utf-8-sig')))
    provenance=[]
    for row in rows:
        for key in ['asset','actualCapture','composition']:row[key]=row[key].replace('\\','/')
        asset=ROOT/row['asset'];capture=ROOT/row['actualCapture']
        if args.refresh:
            if fresh.get(row['actualCapture'])!=digest(capture):raise RuntimeError('Capture not proven by this device run: '+row['actualCapture'])
        else:
            old=known.get(row['asset'],{})
            if old.get('sha256')!=digest(asset) or old.get('actualCapture')!=row['actualCapture'] or old.get('captureSha256')!=digest(capture):
                raise RuntimeError('Screenshot bytes changed; render and use --refresh after a passing device run: '+row['asset'])
        with Image.open(asset) as image:
            if image.size!=(1920,1200) or image.format!='JPEG':raise RuntimeError(f'Invalid export: {asset}')
            if max(ImageStat.Stat(image.convert('RGB')).stddev)<10:raise RuntimeError(f'Blank export: {asset}')
        with Image.open(capture) as image:
            if image.size!=(1920,1092):raise RuntimeError(f'Unexpected device capture: {capture}')
            with Image.open(asset) as exported:
                difference=ImageChops.difference(exported.convert('RGB').crop((0,108,1920,1200)),image.convert('RGB'))
                if max(ImageStat.Stat(difference).mean)>8:raise RuntimeError(f'Composition differs from actual locale-matched capture: {asset}')
        row['status']='EXPORTED_DRAFT_PENDING_NATIVE_REVIEW'
        provenance.append({'locale':row['locale'],'shot':row['shot'],'asset':row['asset'],'sha256':digest(asset),'actualCapture':row['actualCapture'],'captureSha256':digest(capture),'nativeApproved':False})
    if len(rows)!=176:raise RuntimeError('Expected 22 locales × 8 real screens')
    with (folder/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(folder/'provenance.json',{'status':'DRAFT_PENDING_NATIVE_REVIEW','count':len(rows),'dimensions':[1920,1200],'format':'JPEG','device':'KFTRWI / Fire OS 7 / landscape','debugApkSha256':run['debugApkSha256'] if args.refresh else previous['debugApkSha256'],'visualReview':'Not established by this automated validator. Consult the dated delivery report for actual manual samples. Native review and other device sizes remain incomplete.','assets':provenance})
    print(f'{len(rows)} nonblank JPEG compositions validated at 1920 × 1200; native approval absent')

if __name__=='__main__':main()
