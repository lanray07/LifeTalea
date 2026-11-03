"""Exercise bounded accessibility-dump retries without a connected device."""
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import check_fire_layouts as layouts


class FireLayoutCaptureTest(unittest.TestCase):
    def test_transient_dump_failure_still_requires_a_valid_home_tree_and_bounds(self):
        buffer=io.BytesIO();Image.new('RGB',(20,30),'white').save(buffer,format='PNG')
        dumps=[]
        def adb(*args,binary=False):
            if args[:3]==('shell','uiautomator','dump'):
                dumps.append(args)
                if len(dumps)==1:raise RuntimeError('Transient dump failure')
            if args[:2]==('shell','cat'):
                return '<hierarchy><node package="com.lifetalea.app.debug" text="Add a memory" bounds="[1,2][10,20]"/></hierarchy>'
            if args[:2]==('exec-out','screencap'):return buffer.getvalue()
            return ''
        with tempfile.TemporaryDirectory() as directory,patch.object(layouts,'OUT',Path(directory)),patch.object(layouts,'adb',side_effect=adb),patch.object(layouts.time,'sleep'):
            result=layouts.capture('synthetic-test-only')
            self.assertEqual(2,len(dumps))
            self.assertTrue(result['homeActionInAccessibilityTreeAndWithinDisplay'])
            self.assertTrue((Path(directory)/'synthetic-test-only.xml').exists())

    def test_repeated_dump_failures_stop_after_three_attempts(self):
        dumps=[]
        def adb(*args,binary=False):
            if args[:3]==('shell','uiautomator','dump'):
                dumps.append(args);raise RuntimeError('Dump failed')
            return ''
        with patch.object(layouts,'adb',side_effect=adb),patch.object(layouts.time,'sleep'):
            with self.assertRaisesRegex(AssertionError,'home action not available'):
                layouts.capture('synthetic-test-only')
        self.assertEqual(3,len(dumps))


if __name__=='__main__':unittest.main()
