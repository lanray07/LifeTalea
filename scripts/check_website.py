"""Checks exported HTML, links, headings, structured JSON and required routes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'website/out'
class Page(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.images=[];self.h1=0;self.title=False;self.description=False;self.canonical=False;self.jsons=[];self.script=False;self.data=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1':self.h1+=1
        if tag=='title':self.title=True
        if tag=='meta' and a.get('name')=='description':self.description=bool(a.get('content'))
        if tag=='link' and a.get('rel')=='canonical':self.canonical=True
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='img':self.images.append(a)
        if tag=='script' and a.get('type')=='application/ld+json':self.script=True;self.data=''
    def handle_endtag(self,tag):
        if tag=='script' and self.script:self.jsons.append(json.loads(self.data));self.script=False
    def handle_data(self,text):
        if self.script:self.data+=text
def main():
    errors=[];pages=[];required=['features','family-memory-journal','voice-story-recording','voice-transcription','digital-scrapbook','family-timeline','keepsake-books','offline-memory-journal','fire-tablet-compatibility','languages','pricing','faq','privacy','support','contact']
    for slug in ['',*required]:
        file=OUT/'en-GB'/slug/'index.html'
        if not file.exists():errors.append(f'Missing {slug}');continue
        page=Page();page.feed(file.read_text(encoding='utf-8'));pages.append(file)
        if page.h1!=1 or not page.title or not page.description or not page.canonical:errors.append(f'Invalid headings/metadata: {file}')
        if not page.jsons:errors.append(f'No structured data: {file}')
        for href in page.links:
            url=urlsplit(href)
            if url.scheme or url.netloc or not url.path.startswith('/'):continue
            target=OUT/unquote(url.path.lstrip('/'))
            if not target.exists():errors.append(f'Broken link {href} from {file}')
        for image in page.images:
            if 'alt' not in image:errors.append(f'Image lacks alt: {file}')
    for name in ['sitemap.xml','robots.txt']:
        if not (OUT/name).exists():errors.append(f'Missing {name}')
    report={'status':'PASS' if not errors else 'FAIL','htmlPagesChecked':len(pages),'errors':errors,'scope':'English static export. Public domain and deployment remain unconfigured. Localised website copy is pending native review.'}
    path=ROOT/'deliverables/reports/website-checks.json';path.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
