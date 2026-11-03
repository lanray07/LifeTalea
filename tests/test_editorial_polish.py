"""Protect authored corrections from the known machine-translation regressions."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from polish_translations import APP_KEYS,EXTRA_KEYS,blocks,adapt,article_overrides
from localize import LOC,read,issues

class EditorialPolishTest(unittest.TestCase):
    def test_every_language_has_complete_unique_app_corrections(self):
        self.assertFalse(set(APP_KEYS)&set(EXTRA_KEYS))
        source=read(LOC/'en-GB.json')
        for filename,keys in [('app.txt',APP_KEYS),('app-extra.txt',EXTRA_KEYS)]:
            drafts=blocks(LOC/'polish'/filename)
            self.assertEqual(len(drafts),15)
            for language,lines in drafts.items():
                with self.subTest(language=language,file=filename):
                    self.assertEqual(len(lines),len(keys))
                    self.assertEqual(issues({key:source[key] for key in keys},dict(zip(keys,lines))),[])

    def test_english_commands_keep_boundaries_and_exact_supported_phrases(self):
        index=APP_KEYS.index('unknown_command')
        for language,lines in blocks(LOC/'polish/app.txt').items():
            text=lines[index]
            for phrase in ['Create a new memory','Open my timeline','Create a keepsake book']:
                self.assertEqual(text.count(phrase),1,language)
            self.assertNotIn('timelineou',text)
            self.assertNotIn('timelineoder',text)

    def test_portuguese_regional_words_are_not_substring_replacements(self):
        self.assertEqual(adapt('salvar salva salvo arquivos aplicativo','pt-PT'),'guardar guardada guardado ficheiros aplicação')
        self.assertEqual(adapt('ressalvar arquivo','pt-PT'),'ressalvar ficheiro')

    def test_all_fifteen_articles_are_authored_for_each_language(self):
        for language in blocks(LOC/'polish/app.txt'):
            articles=article_overrides(language,language)
            self.assertEqual(len(articles),15,language)
            self.assertIn('LifeTalea',articles['voice-transcription']['summary'])
            self.assertIn('banksmi@mail.com',articles['contact']['summary'])
            self.assertEqual(len(articles['privacy']['sections']),4)

if __name__=='__main__':unittest.main()
