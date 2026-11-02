"""Compose draft store layouts around actual locale-matched device captures.

Render the HTML in the browser at 1920x1200; save its JPEG bytes as .jpg.
No missing or mocked UI is substituted. All files remain pending native review.
"""
import csv
from html import escape
from localize import ROOT, TARGETS, read
from translate_collateral import HEADLINES

def main():
    output=ROOT/'deliverables/store-assets/screenshots/localized-drafts';output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for locale in TARGETS:
        metadata=read(ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json',{})
        headlines=read(ROOT/'deliverables/store-assets/metadata/en-GB/screenshot-headlines.json',{}) if locale=='en-GB' else metadata.get('screenshotHeadlines',{})
        folder=output/locale;folder.mkdir(exist_ok=True)
        for shot in HEADLINES:
            capture=ROOT/f'deliverables/reports/device-evidence/localization/{locale}-{shot}.png'
            headline=headlines.get(shot,'')
            html=folder/f'{shot}.html'
            image=folder/f'{shot}.jpg'
            ready=capture.exists() and bool(headline)
            if ready:
                html.write_text(f'''<!doctype html><html lang="{locale}" dir="{'rtl' if locale=='ar' else 'ltr'}"><meta charset="utf-8"><title>LifeTalea {locale} {shot} draft</title><style>*{{box-sizing:border-box}}html,body{{margin:0;width:1920px;height:1200px;overflow:hidden;background:#faf7f1}}header{{height:108px;display:flex;align-items:center;justify-content:space-between;gap:32px;padding:0 42px;border-bottom:1px solid #c8a46b;color:#38584a}}h1{{font:42px/1.12 Georgia,serif;margin:0;max-width:1640px;overflow-wrap:anywhere}}header span{{font:24px Arial,sans-serif;white-space:nowrap}}img{{display:block;width:1920px;height:1092px;object-fit:contain}}html:lang(ar) h1{{font-family:Arial,sans-serif;line-height:1.3}}</style><header><h1>{escape(headline)}</h1><span>LifeTalea</span></header><img src="../../../../reports/device-evidence/localization/{locale}-{shot}.png" alt="{escape(headline,quote=True)}"></html>''',encoding='utf-8')
            rows.append({'locale':locale,'shot':shot,'headline':headline,'actualCapture':capture.relative_to(ROOT).as_posix(),'composition':html.relative_to(ROOT).as_posix() if ready else '', 'asset':image.relative_to(ROOT).as_posix(),'status':'READY_TO_RENDER_DRAFT' if ready else 'WAITING_FOR_CAPTURE_OR_COPY','nativeApproved':False})
    manifest=output/'manifest.csv'
    with manifest.open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(f'{sum(row["status"]=="READY_TO_RENDER_DRAFT" for row in rows)}/{len(rows)} actual-capture compositions ready; zero native approvals')

if __name__=='__main__':main()
