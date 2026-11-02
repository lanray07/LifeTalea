"""Prepare honest draft metadata and a required-shot manifest; never invent screenshots."""
from pathlib import Path
import json,csv
from localize import TARGETS
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/store-assets';(OUT/'metadata/en-GB').mkdir(parents=True,exist_ok=True);(OUT/'manifests').mkdir(exist_ok=True)
metadata={
 'status':'DRAFT_NOT_SUBMISSION_READY', 'publisher':'O.Bankole','supportEmail':'banksmi@mail.com',
 'title':'LifeTalea - Family Stories & Voice Journal',
 'shortDescription':'Keep family stories, photographs and voice memories together in a private journal. Create albums, explore a timeline and save scrapbook drafts on your device.',
 'longDescription':'''Keep the moments. Remember the voices.

LifeTalea gives family stories a private place on your tablet. Begin with one photograph, a few written lines, or a voice recording. No LifeTalea account is required.

SAVE THE STORY BEHIND THE PHOTOGRAPH
Add photographs, tags and an optional location you enter yourself. Choose a year, month, exact date or unknown date. Organise memories into albums and mark favourites.

MAKE ROOM FOR THEIR VOICE
Record, pause, resume and play a spoken story. Audio stays in private app storage. The free tier supports recordings up to three minutes. Microphone permission is requested when you choose to record. Voice commands and spoken playback depend on installed device services; touch and text alternatives remain available.

FOLLOW YOUR FAMILY'S CHAPTERS
Browse saved memories in a timeline. Search written stories, tags and manually edited transcripts. Create scrapbook drafts, arrange pages and add captions.

PRESERVE A COPY YOU CONTROL
Create a local backup and explicitly choose whether to include photographs and recordings. Restore validates the archive before importing. Keep exports and passphrases somewhere safe.

OPTIONAL PREMIUM
Premium is designed as a one-time purchase for unlimited albums, longer recordings, local PDF keepsake export and encrypted archive creation. Actual local prices will be supplied by Amazon. Existing stories remain accessible without Premium.

DEVELOPMENT STATUS
This listing is a draft. Automatic transcription is not configured. Worldwide translations, required device tests and Amazon purchasing verification are incomplete. No cloud sync is offered. Do not publish this draft as a finished product listing.

Publisher: O.Bankole
Support: banksmi@mail.com''',
 'featureBullets':['Save written stories, photographs and local voice recordings together.','Organise private albums with tags, favourites and approximate dates.','Explore a family timeline and create saved scrapbook drafts.','Create local backups with explicitly selected photos and audio.','Use touch and text alternatives when device speech services are unavailable.'],
 'keywords':['family memory journal','voice journal','record family stories','digital scrapbook','private family journal','memory timeline'],
 'keywordEvidence':'Intent hypotheses only; no search volume, rankings or conversion data obtained.',
 'categoryRecommendation':'Lifestyle (confirm category in console)',
 'releaseNotes':'Initial development preview. Not approved for public submission.',
 'privacyUrl':'https://github.com/lanray07/LifeTalea/blob/main/docs/PRIVACY_POLICY.md',
 'supportUrl':'https://github.com/lanray07/LifeTalea/blob/main/docs/SUPPORT.md',
 'liveDownloadUrl':None
}
(OUT/'metadata/en-GB/listing.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
assert len(metadata['shortDescription'].encode())<=2000
assert len(metadata['longDescription'])<=4000
assert 3<=len(metadata['featureBullets'])<=5
shots=[('01-home','Family Memories & Voice Journal'),('02-albums','Private Family Photo Albums'),('03-voice','Record Family Stories by Voice'),('04-transcription','Voice Notes & Story Transcription'),('05-timeline','Family Memory Timeline'),('06-scrapbook','Digital Scrapbook Creator'),('07-offline','Offline Memory Journal'),('08-keepsakes','Printable Family Memory Books')]
with (OUT/'manifests/required-screenshots.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=['locale','deviceVariant','shot','headline','status','actualCapture','blocker']);writer.writeheader()
    for locale in TARGETS:
        for variant in ['fire-tablet','phone']:
            for name,headline in shots:
                capture=ROOT/f'deliverables/reports/device-evidence/screenshots/{locale}/{name}.png'
                writer.writerow({'locale':locale,'deviceVariant':variant,'shot':name,'headline':headline if locale=='en-GB' else '', 'status':'CAPTURE_ONLY_NEEDS_COMPOSITION_REVIEW' if capture.exists() else 'BLOCKED' if locale!='en-GB' or 'transcription' in name else 'NOT_TESTED','actualCapture':str(capture.relative_to(ROOT)) if capture.exists() else '', 'blocker':'Approved native copy and real localised app captures required' if locale!='en-GB' else 'Automatic transcription unavailable; cannot advertise it' if 'transcription' in name else 'Capture, approved dimensions, fictional-data check and visual review required'})
(OUT/'metadata/validation.json').write_text(json.dumps({'status':'PASS','scope':'English draft limits only','titleCharacters':len(metadata['title']),'shortDescriptionBytes':len(metadata['shortDescription'].encode()),'longDescriptionCharacters':len(metadata['longDescription']),'featureBullets':len(metadata['featureBullets']),'releaseStatus':'BLOCKED'},indent=2))
print('English draft metadata validated. Required screenshot matrix generated; missing files remain incomplete.')
