"""Check exported components in the actual unsigned release/LAT manifests."""
import hashlib,json,re,subprocess
from datetime import datetime,timezone
from inspect_amazon_apk import ROOT,SDK

def components(text):
    rows=[];current=None;depth=0
    for line in text.splitlines():
        element=re.match(r'^(\s*)E: ([\w-]+)',line)
        if element:
            indent=len(element[1])
            if current and indent<=depth:rows.append(current);current=None
            if element[2] in {'activity','activity-alias','receiver','service','provider'}:
                depth=indent;current={'type':element[2]}
        attr=re.match(r'^(\s*)A: android:(name|exported|permission)\([^)]*\)=(.*)$',line)
        if current and attr and len(attr[1])==depth+2:
            if attr[2]=='exported':current['exported']=attr[3].endswith('0xffffffff')
            else:current[attr[2]]=re.search(r'"([^"]+)"',attr[3])[1]
    if current:rows.append(current)
    return rows

def main():
    allowed={'com.lifetalea.app.MainActivity':None,'com.amazon.device.iap.ResponseReceiver':'com.amazon.inapp.purchasing.Permission.NOTIFY','androidx.profileinstaller.ProfileInstallReceiver':'android.permission.DUMP'}
    artifacts=[]
    for relative in ['release/app-release-unsigned.apk','amazonTest/app-amazonTest-unsigned.apk']:
        apk=ROOT/'android/app/build/outputs/apk'/relative
        text=subprocess.check_output([str(SDK/'build-tools/35.0.0/aapt.exe'),'dump','xmltree',str(apk),'AndroidManifest.xml'],text=True,encoding='utf-8')
        rows=components(text)
        assert rows and all('name' in row and 'exported' in row for row in rows)
        exported={row['name']:row.get('permission') for row in rows if row['exported']}
        assert exported==allowed,exported
        artifacts.append({'apk':apk.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'components':rows})
    report={'observedAt':datetime.now(timezone.utc).isoformat(),'status':'PASS_UNSIGNED_ARTIFACT_ALLOWLIST','artifacts':artifacts,'scope':'Actual merged manifests: launcher and permission-guarded SDK/profile receivers only. Not an independent audit, runtime permission-grant assessment, or inspection of Amazon DRM-processed output.'}
    (ROOT/'deliverables/reports/amazon-component-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Both unsigned APK component allowlists passed; Amazon-processed manifest remains unverified.')

if __name__=='__main__':main()
