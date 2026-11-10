"""Validate actual screenshot exports, dimensions and provenance; never approve copy."""
import csv
import hashlib
import argparse
from PIL import Image, ImageStat, ImageChops
from localize import ROOT, read, write

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--refresh',action='store_true',help='Bind newly rendered captures to a passing current device run.')
    parser.add_argument('--folder',default='deliverables/store-assets/screenshots/localized-drafts')
    parser.add_argument('--device-report',default='deliverables/reports/device-test-run.json')
    args=parser.parse_args()
    folder=(ROOT/args.folder).resolve();device_report=(ROOT/args.device_report).resolve()
    if not all(path.is_relative_to(ROOT.resolve()) for path in (folder,device_report)):parser.error('Paths must stay inside the workspace')
    previous=read(folder/'provenance.json',{})
    known={row['asset']:row for row in previous.get('assets',[])}
    run=read(device_report)
    if args.refresh:
        if run.get('status')!='PASS' or run.get('testSelection')!='all':raise RuntimeError('A passing full device run is required before refreshing screenshot provenance')
        for key,path in [('debugApkSha256','android/app/build/outputs/apk/debug/app-debug.apk'),('testApkSha256','android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')]:
            if run.get(key)!=digest(ROOT/path):raise RuntimeError('Device evidence does not match the current APKs')
        fresh={row['path']:row['sha256'] for row in run.get('evidence',[])}
    elif not previous.get('debugApkSha256'):
        raise RuntimeError('No previous provenance exists; use --refresh after a complete device run')
    with (folder/'manifest.csv').open(encoding='utf-8-sig') as stream:
        rows=list(csv.DictReader(stream))
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
        copy_binding={}
        if args.refresh or 'headlineSha256' in known.get(row['asset'],{}):
            listing=read(ROOT/f"deliverables/store-assets/metadata/{row['locale']}/listing.json")
            headline=listing['screenshotHeadlines'][row['shot']]
            if row['headline']!=headline:raise RuntimeError('Screenshot headline differs from current copy: '+row['asset'])
            copy_binding={'headlineSha256':hashlib.sha256(headline.encode('utf-8')).hexdigest(),'compositionSha256':digest(ROOT/row['composition'])}
            if not args.refresh and any(known[row['asset']].get(key)!=value for key,value in copy_binding.items()):
                raise RuntimeError('Screenshot composition/copy changed after validation: '+row['asset'])
        with Image.open(asset) as image:
            if image.size!=(1920,1200) or image.format!='JPEG':raise RuntimeError(f'Invalid export: {asset}')
            if max(ImageStat.Stat(image.convert('RGB')).stddev)<10:raise RuntimeError(f'Blank export: {asset}')
        with Image.open(capture) as image:
            if image.size!=(1920,1092):raise RuntimeError(f'Unexpected device capture: {capture}')
            with Image.open(asset) as exported:
                difference=ImageChops.difference(exported.convert('RGB').crop((0,108,1920,1200)),image.convert('RGB'))
                if max(ImageStat.Stat(difference).mean)>8:raise RuntimeError(f'Composition differs from actual locale-matched capture: {asset}')
        row['status']='EXPORTED_VISUAL_REVIEW_SEPARATE'
        provenance.append({'locale':row['locale'],'shot':row['shot'],'asset':row['asset'],'sha256':digest(asset),'actualCapture':row['actualCapture'],'captureSha256':digest(capture),'nativeApproved':False,**copy_binding})
    if len(rows)!=176:raise RuntimeError('Expected 22 locales × 8 real screens')
    with (folder/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write(folder/'provenance.json',{'status':'EXPORTED_VISUAL_REVIEW_SEPARATE','deviceReport':device_report.relative_to(ROOT).as_posix(),'count':len(rows),'dimensions':[1920,1200],'format':'JPEG','device':'KFTRWI / Fire OS 7 / landscape','debugApkSha256':run['debugApkSha256'] if args.refresh else previous['debugApkSha256'],'visualReview':'Not established by this automated validator. Consult the dated delivery report for actual manual samples. AI copy approval is separate; native certification and other device sizes are not inferred.','assets':provenance})
    print(f'{len(rows)} nonblank JPEG compositions validated at 1920 x 1200; native approval absent')

if __name__=='__main__':main()
