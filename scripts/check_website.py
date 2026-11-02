"""Validate every exported locale's links, metadata, direction and structured data."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json,sys
from localize import TARGETS,read
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'website/out'

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.images=[];self.h1=0;self.title=False;self.description=False;self.canonical='';self.jsons=[];self.script=False;self.data='';self.lang='';self.direction='';self.alternates={};self.noindex=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.lang=a.get('lang');self.direction=a.get('dir')
        if tag=='h1':self.h1+=1
        if tag=='title':self.title=True
        if tag=='meta' and a.get('name')=='description':self.description=bool(a.get('content'))
        if tag=='meta' and a.get('name')=='robots':self.noindex='noindex' in a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical=a.get('href','')
        if tag=='link' and a.get('rel')=='alternate' and a.get('hrefLang',a.get('hreflang')):self.alternates[a.get('hreflang',a.get('hrefLang'))]=a.get('href')
        if tag=='a' and a.get('href'):self.links.append(a['href'])
        if tag=='img':self.images.append(a)
        if tag=='script' and a.get('type')=='application/ld+json':self.script=True;self.data=''
    def handle_endtag(self,tag):
        if tag=='script' and self.script:self.jsons.append(json.loads(self.data));self.script=False
    def handle_data(self,text):
        if self.script:self.data+=text

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    errors=[];pages=[]
    source_path=ROOT/'website/src/dictionaries/en-GB.json';source=read(source_path)
    baseline=Page();baseline.feed((OUT/'en-GB/index.html').read_text(encoding='utf-8'))
    preview=urlsplit(baseline.canonical).hostname in ['localhost','127.0.0.1']
    reviews=read(ROOT/'website/localization/reviews.json',{})
    locales=['en-GB']
    for locale in TARGETS[1:]:
        file=ROOT/f'website/src/dictionaries/{locale}.json';r=reviews.get(locale,{})
        approved=file.exists() and r.get('status')=='APPROVED' and r.get('sourceHash')==digest(source_path) and r.get('targetHash')==digest(file) and r.get('reviewer') and r.get('reviewedAt')
        if preview or approved:locales.append(locale)
    required=['',*source['articles']]
    for locale in locales:
        for slug in required:
            file=OUT/locale/slug/'index.html'
            if not file.exists():errors.append(f'Missing {locale}/{slug}');continue
            page=Page();page.feed(file.read_text(encoding='utf-8'));pages.append(file)
            if page.h1!=1 or not page.title or not page.description or not page.canonical:errors.append(f'Invalid headings/metadata: {locale}/{slug}')
            if page.lang!=locale or page.direction!=('rtl' if locale=='ar' else 'ltr'):errors.append(f'Invalid HTML language/direction: {locale}/{slug}')
            if urlsplit(page.canonical).path!=f'/{locale}/{slug+"/" if slug else ""}':errors.append(f'Wrong canonical: {locale}/{slug}')
            if set(page.alternates)!=set([*['es' if tag=='es-419' else tag for tag in locales],'x-default']):errors.append(f'Incomplete hreflang: {locale}/{slug}')
            if preview and not page.noindex:errors.append(f'Draft page can be indexed: {locale}/{slug}')
            if not page.jsons or not any(item.get('inLanguage')==locale for item in page.jsons):errors.append(f'Missing localized structured data: {locale}/{slug}')
            for href in [*page.links,*page.alternates.values()]:
                url=urlsplit(href)
                if url.scheme or url.netloc:
                    if url.hostname not in ['localhost','127.0.0.1']:continue
                if not url.path.startswith('/'):continue
                target=OUT/unquote(url.path.lstrip('/'))
                if not target.exists():errors.append(f'Broken link {href} from {locale}/{slug}')
            for image in page.images:
                if 'alt' not in image:errors.append(f'Image lacks alt: {locale}/{slug}')
    for name in ['sitemap.xml','robots.txt']:
        if not (OUT/name).exists():errors.append(f'Missing {name}')
    report={'status':'PASS' if not errors else 'FAIL','htmlPagesChecked':len(pages),'locales':locales,'preview':preview,'errors':errors,'scope':'Exported HTML structure, links, locale metadata and preview indexing controls. Native-language and browser visual review remain separate.'}
    (ROOT/'deliverables/reports/website-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report));return bool(errors)

if __name__=='__main__':sys.exit(main())
