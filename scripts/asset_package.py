"""Editable brand applications derived from the project's original vector identity/art.
These are source artworks, not actual app screenshots or approved store compositions.
"""
from pathlib import Path
import base64,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/brand-assets'
hero=base64.b64encode((OUT/'hero-book.png').read_bytes()).decode()
def svg(name,width,height,body,bg='#FAF7F1'):
    (OUT/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" fill="{bg}"/>{body}</svg>',encoding='utf-8')
def book(x,y,w,h):return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{hero}"/>'
def label(text,x,y,size=64,color='#38584A'):return f'<text x="{x}" y="{y}" font-family="Georgia,serif" font-size="{size}" fill="{color}">{text}</text>'
svg('splash-artwork.svg',1200,1920,label('LifeTalea',360,620,88)+book(130,700,940,620))
svg('onboarding-stories.svg',1200,1000,label('Every story deserves a place.',100,150,62)+book(90,220,1020,680))
svg('empty-state-stories.svg',1200,900,book(240,100,720,480)+label('Your story starts here.',230,710,62))
svg('premium-upgrade.svg',1200,900,label('LifeTalea Premium',180,150,80)+book(200,210,800,530))
svg('voice-waveform.svg',1200,700,'<path d="M130 350H230L260 310 300 425 340 205 380 500 420 290 460 390 500 350H600L640 255 680 455 720 165 760 525 800 305 840 385 880 350H1070" fill="none" stroke="#38584A" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"/>'+label('Keep the voices you treasure.',160,610,58))
svg('timeline-artwork.svg',1200,900,'<path d="M260 120V780" stroke="#C8A46B" stroke-width="6"/>'+''.join(f'<circle cx="260" cy="{y}" r="22" fill="#38584A"/><path d="M310 {y}H980" stroke="#C8A46B" stroke-width="2"/>' for y in [200,450,700]))
svg('keepsake-cover.svg',1200,1600,label('LifeTalea',140,190,74)+book(140,370,920,610)+'<path d="M140 300H1060M140 1310H1060" stroke="#C8A46B" stroke-width="3"/>'+label('Your family. Your stories.',160,1200,64))
for name,w,h in [('promotional-banner.svg',1920,1080),('social-story.svg',1080,1920),('website-hero-source.svg',1600,900)]:
    if h>w:body=label('LifeTalea',95,190,90)+label('Keep the moments.',95,360,64)+label('Remember the voices.',95,445,64)+book(30,650,1020,680)
    else:body=label('LifeTalea',110,170,80)+label('Keep the moments.',110,340,64)+label('Remember the voices.',110,425,64)+book(w*.49,h*.23,w*.48,h*.61)
    svg(name,w,h,body)
svg('wordmark-light.svg',1000,220,label('LifeTalea',50,150,130))
svg('wordmark-dark.svg',1000,220,label('LifeTalea',50,150,130,'#FAF7F1'),'#1D2621')
inventory=[]
for file in sorted(OUT.iterdir()):
    if file.suffix in ['.svg','.png']:inventory.append({'file':str(file.relative_to(ROOT)),'kind':'design_reference_not_app_capture' if file.name=='design-concept.png' else 'original_brand_source','review':'VISUAL_REVIEW_PENDING' if file.suffix=='.svg' and file.name not in ['logo.svg'] else 'INSPECTED_IN_PROJECT_CONTEXT'})
(OUT/'asset-inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print(f'{len(inventory)} brand source assets inventoried; rendered store approval is separate.')
