"""A failed or unrelated device run must never relabel store screenshots."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_localized_screenshots as validator


class ScreenshotProvenanceTest(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.folder=self.root/'deliverables/store-assets/screenshots/localized-drafts'
        self.folder.mkdir(parents=True)
        self.run=self.root/'deliverables/reports/device-test-run.json'
        self.run.parent.mkdir(parents=True)
        self.run.write_text(json.dumps({'status':'FAIL','debugApkSha256':'unrelated'}))

    def invoke(self,*args):
        with patch.object(validator,'ROOT',self.root),patch.object(sys,'argv',['validator',*args]):
            validator.main()

    def test_failed_run_cannot_create_current_provenance(self):
        with self.assertRaisesRegex(RuntimeError,'passing full device run'):
            self.invoke('--refresh')
        self.assertFalse((self.folder/'provenance.json').exists())

    def test_existing_assets_without_provenance_require_a_verified_refresh(self):
        with self.assertRaisesRegex(RuntimeError,'No previous provenance'):
            self.invoke()

    def test_changed_capture_is_rejected_without_relabeling_historical_origin(self):
        (self.root/'asset.jpg').write_bytes(b'previous composition')
        (self.root/'capture.png').write_bytes(b'new partial capture')
        old={'debugApkSha256':'historical-apk','assets':[{'asset':'asset.jpg','actualCapture':'capture.png','sha256':hashlib.sha256(b'previous composition').hexdigest(),'captureSha256':hashlib.sha256(b'previous capture').hexdigest()}]}
        provenance=self.folder/'provenance.json';provenance.write_text(json.dumps(old))
        before=provenance.read_bytes()
        with (self.folder/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as stream:
            writer=csv.DictWriter(stream,fieldnames=['asset','actualCapture','composition'])
            writer.writeheader();writer.writerow({'asset':'asset.jpg','actualCapture':'capture.png','composition':'shot.html'})
        with self.assertRaisesRegex(RuntimeError,'Screenshot bytes changed'):
            self.invoke()
        self.assertEqual(before,provenance.read_bytes())


if __name__=='__main__':unittest.main()
