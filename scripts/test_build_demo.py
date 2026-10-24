"""The public demo includes only the explicit fictional assets, never private app files."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_demo
class DemoBuildTests(unittest.TestCase):
    def test_public_allowlist_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'project';(source/'demo').mkdir(parents=True)
            for n in build_demo.FILES:
                dest=source/'demo'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((build_demo.ROOT/'demo'/n).read_bytes())
            (source/'demo/private-database.sqlite').write_text('FICTIONAL_PRIVATE')
            (source/'demo/drive-auth.json').write_text('FICTIONAL_SECRET')
            with patch.object(build_demo,'ROOT',source),contextlib.redirect_stdout(io.StringIO()):
                build_demo.build(root/'public')
                self.assertEqual({p.relative_to(root/'public').as_posix() for p in (root/'public').rglob('*') if p.is_file()},set(build_demo.FILES)|{'.nojekyll'})
                (source/'demo/shared/style.css').write_text('changed')
                with self.assertRaisesRegex(ValueError,'checksum'):build_demo.build(root/'other')
if __name__=='__main__':unittest.main()
