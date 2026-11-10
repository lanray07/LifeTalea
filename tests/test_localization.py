import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from localize import issues, source_hash, approved, generate, write, check_debug_resources, resource_xml
from unittest.mock import patch
from tempfile import TemporaryDirectory
class LocalizationTest(unittest.TestCase):
    def test_catalogue_writer_preserves_portable_review_hash_bytes(self):
        with TemporaryDirectory() as directory:
            file=Path(directory)/'catalogue.json'
            write(file,{'save':'Enregistrer'})
            self.assertNotIn(b'\r',file.read_bytes())
            self.assertTrue(file.read_bytes().endswith(b'\n'))
    def test_stale_debug_overlay_cannot_shadow_current_source(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);catalogues=root/'localization'
            source={'save':'Save'}
            write(catalogues/'en-GB.json',source)
            overlay=root/'android/app/src/debug/res/values-b+en+GB/strings.xml'
            overlay.parent.mkdir(parents=True)
            overlay.write_text(resource_xml({'save':'Obsolete copy'}),encoding='utf-8')
            with patch('localize.ROOT',root),patch('localize.LOC',catalogues):
                with self.assertRaisesRegex(RuntimeError,'Stale debug'):
                    check_debug_resources(source)
                overlay.write_text(resource_xml(source),encoding='utf-8')
                check_debug_resources(source)
    def test_format_specifiers_preserved(self):
        self.assertEqual([],issues({'count':'%1$d memories'},{'count':'%1$d souvenirs'}))
        self.assertTrue(issues({'count':'%1$d memories'},{'count':'%s souvenirs'}))
    def test_missing_plural_and_brand_reported(self):
        self.assertTrue(issues({'n':{'one':'%d story','other':'%d stories'}},{'n':{'one':'%d récit'}}))
        self.assertTrue(issues({'name':'LifeTalea'},{'name':'Different'}))
    def test_source_change_invalidates_review(self): self.assertNotEqual(source_hash({'a':'One'}),source_hash({'a':'Two'}))
    def test_locale_specific_plural_categories_validate_every_form(self):
        source={'n':{'one':'%d story','other':'%d stories'}}
        self.assertEqual([],issues(source,{'n':{'one':'%d récit','few':'%d récits','other':'%d récits'}}))
        self.assertTrue(issues(source,{'n':{'other':'%d récits','few':'récits'}}))
        self.assertTrue(issues(source,{'n':{'other':'%d récits','invalid':'%d récits'}}))
    def test_extra_keys_empty_text_and_duplicate_placeholders_fail(self):
        self.assertTrue(issues({'a':'Save'},{'a':'','rogue':'x'}))
        self.assertTrue(issues({'a':'%1$d %1$d'},{'a':'%1$d'}))
    def test_approval_binds_both_catalogues_and_reviewer_identity(self):
        source={'save':'Save'}; target={'save':'Enregistrer'}
        record={'status':'APPROVED','sourceHash':source_hash(source),'targetHash':source_hash(target),'reviewer':'Test reviewer','reviewedAt':'2026-11-02'}
        with patch('localize.read',return_value={'fr-FR':record}):
            self.assertTrue(approved('fr-FR',source,target))
            self.assertFalse(approved('fr-FR',source,{'save':'Changed after review'}))
            record['reviewer']=''
            self.assertFalse(approved('fr-FR',source,target))
    def test_unreviewed_generation_is_debug_only(self):
        with TemporaryDirectory() as directory:
            root=Path(directory);catalogues=root/'localization'
            source={'save':'Save'};target={'save':'Enregistrer'}
            write(catalogues/'fr-FR.json',target)
            with patch('localize.ROOT',root),patch('localize.LOC',catalogues):
                with self.assertRaisesRegex(RuntimeError,'editorial review'):
                    generate('fr-FR',source)
                generate('fr-FR',source,draft=True)
                self.assertTrue((root/'android/app/src/debug/res/values-b+fr+FR/strings.xml').exists())
                self.assertFalse((root/'android/app/src/main').exists())
if __name__=='__main__': unittest.main()
