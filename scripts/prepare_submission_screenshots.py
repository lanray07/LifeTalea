"""Draft English store compositions using actual tested Compose captures.
Run the local HTML pages in the in-built browser at 1920x1200 and capture full-page.
Inspect the capture format before naming it: browser captures in this session are JPEG.
Save these rendered compositions as home.jpg, albums.jpg and scrapbook.jpg.
These three draft images do not satisfy the complete eight-shot/localisation release gate.
"""
from pathlib import Path
import shutil,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/store-assets/screenshots/draft-english';OUT.mkdir(parents=True,exist_ok=True)
CAPTURE=ROOT/'deliverables/reports/device-evidence/screenshots/en-GB'
shots=[('home','01-home.png','Family memories, kept together'),('albums','02-albums.png','A collection for every chapter'),('scrapbook','06-scrapbook.png','Bring your stories into a keepsake')]
for name,file,headline in shots:
    shutil.copy2(CAPTURE/file,OUT/file)
    (OUT/f'{name}.html').write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>LifeTalea - {name} draft store composition</title><style>*{{box-sizing:border-box}}html,body{{margin:0;padding:0;width:1920px;height:1200px;overflow:hidden;background:#faf7f1}}header{{height:108px;display:flex;align-items:center;justify-content:space-between;padding:0 42px;border-bottom:1px solid #c8a46b;color:#38584a;font:44px Georgia,serif}}header span{{font:24px Arial,sans-serif}}img{{display:block;width:1920px;height:1092px;object-fit:contain}}</style><header>{headline}<span>LifeTalea</span></header><img src="{file}" alt="Actual LifeTalea {name} screen with fictional demonstration data"></html>''',encoding='utf-8')
(OUT/'provenance.json').write_text(json.dumps({'status':'DRAFT_TECHNICAL_REVIEW_ONLY','source':'Actual physical KFTRWI Compose captures from the passed device suite','locale':'English source UI; UK spelling shared by the current binary','dimensions':[1920,1200],'composition':'108px headline band plus unaltered 1920x1092 actual app capture','doesNotComplete':'Eight-shot catalogue, native linguistic approval, worldwide screenshots or release approval','shots':[{'name':n,'source':f,'headline':h} for n,f,h in shots]},ensure_ascii=False,indent=2),encoding='utf-8')
print(OUT)
