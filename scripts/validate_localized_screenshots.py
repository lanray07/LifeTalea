"""Validate actual screenshot exports, dimensions and provenance; never approve copy."""
import csv
import hashlib
from PIL import Image, ImageStat, ImageChops
from localize import ROOT, read, write

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder=ROOT/'deliverables/store-assets/screenshots/localized-drafts'
    rows=list(csv.DictReader((folder/'manifest.csv').open(encoding='utf-8-sig')))
    provenance=[]
    for row in rows:
        for key in ['asset','actualCapture','composition']:row[key]=row[key].replace('\\','/')
        asset=ROOT/row['asset'];capture=ROOT/row['actualCapture']
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
    write(folder/'provenance.json',{'status':'DRAFT_PENDING_NATIVE_REVIEW','count':len(rows),'dimensions':[1920,1200],'format':'JPEG','device':'KFTRWI / Fire OS 7 / landscape','debugApkSha256':read(ROOT/'deliverables/reports/device-test-run.json')['debugApkSha256'],'visualReview':'Not established by this automated validator. Consult the dated delivery report for actual manual samples. Native review and other device sizes remain incomplete.','assets':provenance})
    print(f'{len(rows)} nonblank JPEG compositions validated at 1920 × 1200; native approval absent')

if __name__=='__main__':main()
