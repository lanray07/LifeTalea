"""Apply authored editorial drafts, validate before writing, retain review gates.

Run after machine generation/editorial seeds. --check detects stale regeneration.
No API calls, personal content, model inference or invented reviewer identities.
"""
import argparse
import copy
import re
from datetime import datetime, timezone
from functools import lru_cache
from localize import ROOT, LOC, TARGETS, read, write, extract, issues, source_hash, generate, configure_locales, report
from translate_collateral import flatten, file_hash, FIELDS

APP_KEYS='recent_memories confirm date precision unknown month location tags search all delete_memory delete_album delete_attachment delete_book voice_story recording_notice microphone_notice microphone_denied recording_failed operation_failed seek transcription_unavailable voice_unavailable voice_error command run_command unknown_command read_story tts_unavailable stop_speaking prompt_lesson answer_prompt no_results no_books_body pdf_note missing_memory spoken_feedback year_filter album_filter finish_recording backup_busy view_memory saved_locally record_first no_story save_first reminders_pending search_year_hint'.split()
EXTRA_KEYS='no_books paper caption layout story_layout photo_layout move_up move_down preview export_pdf pdf_options include_location include_transcript page_size empty_book welcome welcome_body skip device_language language_note family childhood legacy appearance system light dark privacy backup restore_notice restore_counts restore_now backup_saved pdf_saved premium_body free_tier free_limits one_time upgrade premium_active billing_unconfigured billing_unavailable purchase_failed album_limit refresh saved support support_body draft select_all album_members no_photo new_page offline permission reminders'.split()

def blocks(file):
    result={};current=None
    for line in file.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):continue
        if line.startswith('[') and line.endswith(']'):
            current=line[1:-1]
            if current in result:raise ValueError(f'Duplicate language in {file}: {current}')
            result[current]=[]
        else:
            if current is None:raise ValueError(f'Missing language header: {file}')
            result[current].append(line)
    return result

@lru_cache(maxsize=1)
def traditional_converter():
    from opencc import OpenCC
    return OpenCC('s2t')

def adapt(text,locale):
    if locale=='zh-Hant':
        text=traditional_converter().convert(text)
        for before,after in [('相冊','相簿'),('設備','裝置'),('文件夾','資料夾'),('文件','檔案'),('粘貼','貼上'),('文本框','文字方塊'),('存儲','儲存'),('保存','儲存'),('設置','設定'),('備份與恢復','備份與還原'),('刷新','重新整理'),('數據','資料'),('爲','為')]:text=text.replace(before,after)
    if locale=='pt-PT':
        for before,after in [('aplicativo','aplicação'),('arquivos','ficheiros'),('arquivo','ficheiro'),('Excluir','Eliminar'),('excluída','eliminada'),('salvas','guardadas'),('salva','guardada'),('salvo','guardado'),('Salvo','Guardado'),('Salvar','Guardar'),('salvar','guardar'),('Salve','Guarde'),('salve','guarde'),('Busque','Pesquise'),('Buscar','Pesquisar'),('busca','pesquisa'),('tela','ecrã'),('controles','controlos'),('criptografados','encriptados'),('criptografadas','encriptadas')]:text=re.sub(r'\b'+re.escape(before)+r'\b',after,text)
        text=text.replace('Você também pode escrever.','Também pode escrever.').replace('Você pode digitar','Pode escrever').replace('Que conselho você daria a si mesmo','Que conselho daria a si próprio')
        for before,after in [('Pular','Ignorar'),('Prévia','Pré-visualização'),('prévia','pré-visualização'),('restauração','restauro'),('Restaurar','Restaurar'),('Configuração','Definição'),('configurações','definições'),('criptografia','encriptação'),('salvas','guardadas'),('salva','guardada')]:text=re.sub(r'\b'+re.escape(before)+r'\b',after,text)
    if locale=='es-419':
        for before,after in [('Añade','Agrega'),('añade','agrega'),('Añadir','Agregar'),('añadir','agregar'),('tabletas','tablets'),('tableta','tablet')]:text=re.sub(r'\b'+before+r'\b',after,text)
    return text

def article_overrides(language,locale):
    file=LOC/'polish'/f'{language}.web.txt'
    if not file.exists():return {}
    source=read(ROOT/'website/src/dictionaries/en-GB.json')['articles'];result={}
    for line in file.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):continue
        slug,*values=line.split('¦')
        if slug not in source or slug in result:raise ValueError(f'Invalid/duplicate article: {file}/{slug}')
        if len(values)!=2+2*len(source[slug]['sections']):raise ValueError(f'{file}/{slug}: incorrect field count {len(values)}')
        values=[adapt(value,locale) for value in values]
        result[slug]={'title':values[0],'summary':values[1],'sections':[{'title':values[i],'body':values[i+1]} for i in range(2,len(values),2)]}
    if set(result)!=set(source):raise ValueError(f'{file}: missing articles {set(source)-set(result)}')
    app_locale=locale if (LOC/f'{locale}.json').exists() else next(tag for tag in TARGETS if tag.split('-')[0]==language)
    app=read(LOC/f'{app_locale}.json')
    result['voice-transcription']['summary']=app['transcription_notice']
    result['voice-transcription']['sections'][1]={'title':app['transcription_review'],'body':app['transcription_limit']}
    result['offline-memory-journal']['sections'][1]['body']=app['voice_notice']+' '+app['transcription_notice']
    result['faq']['sections'][3]['body']=app['transcription_notice']
    result['privacy']['sections'][1]['body'] += '\n\n' + app['purchase_privacy'] + '\n\n' + app['reminder_notice']
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--app-only',action='store_true');args=parser.parse_args()
    app_drafts=blocks(LOC/'polish/app.txt');extra_drafts=blocks(LOC/'polish/app-extra.txt');source=extract();reviews=read(LOC/'reviews.json');web_reviews_path=ROOT/'website/localization/reviews.json';web_reviews=read(web_reviews_path)
    source_web=read(ROOT/'website/src/dictionaries/en-GB.json');pending=[];changes=[]
    for locale in TARGETS:
        if locale.startswith('en'):continue
        language=locale.split('-')[0];lines=app_drafts[language]
        if len(lines)!=len(APP_KEYS):raise ValueError(f'{language}: expected {len(APP_KEYS)} app values, got {len(lines)}')
        if not args.check and (reviews.get(locale,{}).get('status')=='APPROVED' or web_reviews.get(locale,{}).get('status')=='APPROVED'):raise RuntimeError(f'Refusing to overwrite native-approved copy: {locale}')
        app_file=LOC/f'{locale}.json';app=read(app_file);before=copy.deepcopy(app)
        app.update({key:adapt(value,locale) for key,value in zip(APP_KEYS,lines)})
        if len(extra_drafts[language])!=len(EXTRA_KEYS):raise ValueError(f'{language}: expected {len(EXTRA_KEYS)} extra app values, got {len(extra_drafts[language])}')
        app.update({key:adapt(value,locale) for key,value in zip(EXTRA_KEYS,extra_drafts[language])})
        if issues(source,app):raise ValueError(f'{locale}: {issues(source,app)}')
        changes.extend({'locale':locale,'area':'app','key':key,'before':before[key],'after':value} for key,value in app.items() if value!=before[key])
        pending.append((app_file,app))
        reviews[locale].update({'status':'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':source_hash(source),'targetHash':source_hash(app),'reviewer':'','reviewedAt':'','editorialCorrections':'Authored editorial polish 2026-11-03; not native approval'})
        if args.app_only:continue
        web_file=ROOT/f'website/src/dictionaries/{locale}.json';web=read(web_file);old_web=flatten(web)
        web['articles']=article_overrides(language,locale)
        if language=='de':web['ui']['related']='Entdecken Sie das nächste Kapitel'
        if not web['articles']:raise ValueError(f'Missing authored website articles: {language}')
        errors=issues(flatten(source_web),flatten(web))
        if errors:raise ValueError(f'{locale} website: {errors}')
        changes.extend({'locale':locale,'area':'website','key':key,'before':old_web[key],'after':value} for key,value in flatten(web).items() if value!=old_web[key])
        pending.append((web_file,web))
        listing_file=ROOT/f'deliverables/store-assets/metadata/{locale}/listing.json';listing=read(listing_file);old_listing=flatten({key:listing[key] for key in FIELDS})
        a=web['articles']
        listing['shortDescription']=a['features']['summary']
        listing['featureBullets']=[a[slug]['summary'] for slug in ['family-memory-journal','voice-story-recording','digital-scrapbook','family-timeline']]+[a['fire-tablet-compatibility']['sections'][2]['body']]
        listing['longDescription']='\n\n'.join([web['home']['subtitle'],a['features']['sections'][0]['body'],a['features']['sections'][1]['body'],app['recording_notice'],app['voice_notice'],a['pricing']['sections'][1]['body'],app['backup_notice'],web['home']['releaseNote'],a['voice-transcription']['summary'],app['reminder_notice'],web['ui']['previewNotice'],'O.Bankole · banksmi@mail.com'])
        listing['keywords']=[app[key] for key in ['family','voice_story','history','keepsakes','timeline','personal']]
        listing['releaseNotes']=web['ui']['previewNotice']+' '+web['home']['releaseNote']
        listing['status']='DRAFT_NOT_SUBMISSION_READY';listing['targetHash']=source_hash({key:listing[key] for key in [*FIELDS,'screenshotHeadlines']})
        changes.extend({'locale':locale,'area':'store','key':key,'before':old_listing[key],'after':value} for key,value in flatten({key:listing[key] for key in FIELDS}).items() if value!=old_listing[key])
        if len(listing['longDescription'])>4000:raise ValueError(f'{locale}: Amazon long description exceeds limit')
        pending.append((listing_file,listing))
    if args.check:
        if changes:raise RuntimeError(f'Authored polish is stale: {len(changes)} fields differ; run polish_translations.py')
        print('Editorial draft regression check: PASS (native review remains pending)');return
    for path,value in pending:write(path,value)
    write(LOC/'reviews.json',reviews)
    for locale in TARGETS[1:]:
        if not locale.startswith('en'):generate(locale,source,draft=True)
    configure_locales(source)
    if not args.app_only:
        for locale in TARGETS:
            if locale.startswith('en'):continue
            web_reviews[locale].update({'status':'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':file_hash(ROOT/'website/src/dictionaries/en-GB.json'),'targetHash':file_hash(ROOT/f'website/src/dictionaries/{locale}.json'),'reviewer':'','reviewedAt':'','editorialCorrections':'Authored complete article and store draft polish 2026-11-03; not native approval'})
        write(web_reviews_path,web_reviews)
    write(ROOT/'deliverables/localization/polish-changes.json',{'date':datetime.now(timezone.utc).date().isoformat(),'editorialBaseDate':'2026-11-03','status':'DRAFT_PENDING_NATIVE_REVIEW','changedFields':len(changes),'changes':changes})
    report(source);print(f'{len(changes)} editorial changes applied; zero approvals added')

if __name__=='__main__':main()
