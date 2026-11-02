import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from localize import issues, source_hash
class LocalizationTest(unittest.TestCase):
    def test_format_specifiers_preserved(self):
        self.assertEqual([],issues({'count':'%1$d memories'},{'count':'%1$d souvenirs'}))
        self.assertTrue(issues({'count':'%1$d memories'},{'count':'%s souvenirs'}))
    def test_missing_plural_and_brand_reported(self):
        self.assertTrue(issues({'n':{'one':'%d story','other':'%d stories'}},{'n':{'one':'%d récit'}}))
        self.assertTrue(issues({'name':'LifeTalea'},{'name':'Different'}))
    def test_source_change_invalidates_review(self): self.assertNotEqual(source_hash({'a':'One'}),source_hash({'a':'Two'}))
if __name__=='__main__': unittest.main()
