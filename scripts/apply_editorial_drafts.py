"""Apply explicit draft corrections without rerunning a model or claiming review."""
from localize import LOC, TARGETS, read, write, extract, issues, source_hash, generate, configure_locales, report, approved

def main():
    from opencc import OpenCC
    source=extract();reviews=read(LOC/'reviews.json',{})
    editorial=read(LOC/'editorial-drafts.json',{})
    navigation=read(LOC/'navigation-drafts.json',{})
    notices=read(LOC/'voice-notices.json',{})
    for locale in TARGETS[1:]:
        target=read(LOC/f'{locale}.json',{})
        if not target:raise RuntimeError(f'Generate {locale} before applying the complete correction pass')
        if approved(locale,source,target):continue
        language=locale.split('-')[0]
        corrections={**navigation.get(language,{}),**editorial.get(language,{})}
        if language in notices:corrections['voice_notice']=notices[language]
        if locale=='zh-Hant':
            convert=OpenCC('s2t')
            corrections={k:convert.convert(v).replace('相冊','相簿') for k,v in corrections.items()}
        if locale=='pt-PT':
            corrections={k:v.replace('aplicativo','aplicação').replace('configurações','definições').replace('backup','cópia de segurança').replace('criptografia','cifragem').replace('Excluir','Eliminar') for k,v in corrections.items()}
        target.update(corrections)
        errors=issues(source,target)
        if errors:raise RuntimeError(f'{locale}: '+str(errors))
        write(LOC/f'{locale}.json',target)
        review=reviews.setdefault(locale,{})
        review.update({'status':'DRAFT_PENDING_NATIVE_REVIEW','sourceHash':source_hash(source),'targetHash':source_hash(target),'reviewer':'','reviewedAt':'','editorialCorrections':'Codex drafts for privacy, archive limits, deletion and voice consent; not native approval'})
        write(LOC/'reviews.json',reviews);generate(locale,source,draft=True)
    configure_locales(source);report(source)

if __name__=='__main__':main()
