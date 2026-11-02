"""Validate actual capture files without passing them as finished store compositions."""
from pathlib import Path
from PIL import Image
import json
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'deliverables/reports/device-evidence/screenshots'
allowed={(800,480),(1024,600),(1280,720),(1280,800),(1920,1080),(1920,1200),(2560,1600)}
captures=[]
for path in sorted(BASE.rglob('*.png')):
    with Image.open(path) as image:
        width,height=image.size;image.verify()
    captures.append({'path':str(path.relative_to(ROOT)),'localeFolder':path.parent.name,'width':width,'height':height,'imageValid':True,'rawCaptureMatchesAmazonDimensions':(width,height) in allowed or (height,width) in allowed,'storeApproval':'NOT_APPROVED_REQUIRES_COMPOSITION_AND_REVIEW'})
manifest=ROOT/'deliverables/store-assets/manifests/captured-files.json'
manifest.parent.mkdir(parents=True,exist_ok=True);manifest.write_text(json.dumps(captures,indent=2),encoding='utf-8')
report='# Screenshot validation — INCOMPLETE\n\nActual Compose UI captures from physical KFTRWI testing, with fictional demonstration data. Generated design concepts are excluded. A locale folder is provenance from the test run, not a native-language approval. These are raw development captures, not finished marketing compositions.\n\n|Capture|Size|Valid image|Raw Amazon dimensions|Approval|\n|---|---:|---|---|---|\n'
for row in captures:report+=f"|{Path(row['path']).name}|{row['width']}×{row['height']}|PASS|{'PASS' if row['rawCaptureMatchesAmazonDimensions'] else 'Requires composition/export'}|NOT APPROVED|\n"
report+='\nAll eight reviewed compositions per approved store locale are still required. No translation is accepted over English UI. Automatic transcription is unavailable and cannot be advertised. The phone distribution channel and required variant mapping need confirmation. Editable template: deliverables/store-assets/screenshots/template.html. Required rows: required-screenshots.csv.\n'
(ROOT/'deliverables/reports/SCREENSHOT_VALIDATION_REPORT.md').write_text(report,encoding='utf-8')
print(json.dumps({'validRawCaptures':len(captures),'approvedStoreCompositions':0,'status':'INCOMPLETE'}))
