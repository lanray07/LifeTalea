"""Add authored transcription notices without regenerating existing translations."""
from localize import LOC, TARGETS, read, write, extract, issues, generate, configure_locales, report, source_hash
from opencc import OpenCC

keys = ['transcription_notice', 'transcription_working', 'transcription_failed', 'transcription_empty',
        'transcription_review', 'transcription_apply', 'transcription_limit', 'transcription_consent_required']
source = extract()
drafts = read(LOC / 'transcription-drafts.json')
reviews = read(LOC / 'reviews.json')
for locale in TARGETS[1:]:
    target = read(LOC / f'{locale}.json')
    if locale.startswith('en'): values = [source[key] for key in keys]
    else:
        values = drafts[locale.split('-')[0]]
        assert len(values) == len(keys)
        if locale == 'zh-Hant': values = [OpenCC('s2t').convert(text).replace('設備', '裝置').replace('音頻', '音訊').replace('文本', '文字') for text in values]
        if locale == 'pt-PT':
            values = [text.replace('São aceitas', 'São aceites').replace('revise', 'reveja')
                      .replace('salvar', 'guardar').replace('salva', 'guardada').replace('digite', 'escreva')
                      .replace('Transcrevendo', 'A transcrever').replace('Revisar', 'Rever') for text in values]
    target.update(dict(zip(keys, values)))
    assert not issues(source, target), issues(source, target)
    write(LOC / f'{locale}.json', target)
    reviews[locale].update({'status': 'DRAFT_PENDING_NATIVE_REVIEW', 'sourceHash': source_hash(source),
                            'targetHash': source_hash(target), 'reviewer': '', 'reviewedAt': ''})
    generate(locale, source, draft=True)
write(LOC / 'reviews.json', reviews)
configure_locales(source); report(source)
print('Transcription notices added to 22 drafts; no native approvals added')
