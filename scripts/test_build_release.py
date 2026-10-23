"""Distribution contracts with a fully invented source tree; no user files opened."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_release as release


class ReleaseArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.source=self.root/'distrikt'
        self.source.mkdir()
        self.root_patch=patch.object(release,'ROOT',self.root)
        self.src_patch=patch.object(release,'SRC',self.source)
        self.root_patch.start();self.src_patch.start()
        for name in release.PDF_DEPENDENCIES:self.add('distrikt/app/vendor_py/'+name,'invented local dependency fixture')
        self.add('distrikt/app/kort-import-skabelon.xlsx','invented spreadsheet fixture')
        self.add('distrikt/app/server.py',"VERSION='9.9.0'\n")
        self.add('distrikt/config.yaml','version: "9.9.0"\n')
        self.add('distrikt/Dockerfile','FROM fictional-image\n')
        self.add('distrikt/run.sh','#!/bin/sh\n')
        self.add('distrikt/icon.png','FICTIONAL_ICON')
        self.add('distrikt/logo.png','FICTIONAL_LOGO')
        self.add('distrikt/DOCS.md','# Fictional instructions\n')
        self.add('distrikt/README.md','# Fictional app introduction\n')
        self.add('distrikt/CHANGELOG.md','# Fictional app changes\n')
        self.add('distrikt/translations/da.yaml','configuration: {}\n')
        self.add('distrikt/Start-Distrikt.command','#!/bin/bash\n')
        self.add('Opdater-Home-Assistant-Mac.command','#!/bin/bash\n')
        for name in release.REQUIRED:self.add('distrikt/templates/'+name,'invented form fixture')
        for name in release.ROOT_DOCS:self.add(name,'# Fictional project document\n')
        self.changelog='# Fictional changes\n\n## 9.9.0 · Current version\n\nNew changes.\n\n## 9.8.0 · Previous version\n\nPreserved history.\n'
        self.add('CHANGELOG.md',self.changelog)
        self.add('distrikt/CHANGELOG.md',self.changelog)
        for name in release.BRAND_FILES:self.add('assets/brand/'+name,'invented vector fixture')
        self.add('docs/INSTALL.md','# Fictional installation guide\n')
        self.add('demo/README.md','# Fictional demo guide\n')
        self.add('data/kort.sqlite3','DO_NOT_PACKAGE_PRIVATE_TEST_RECORD')

    def tearDown(self):
        self.src_patch.stop();self.root_patch.stop();self.temp.cleanup()

    def add(self,name,text):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)

    def build(self,folder):
        with contextlib.redirect_stdout(io.StringIO()):return release.build(self.root/folder)

    def test_missing_local_pdf_dependency_blocks_release(self):
        (self.source/'app/vendor_py/pypdf-6.21.2.zip').unlink()
        with self.assertRaisesRegex(ValueError,'missing local PDF dependency'):self.build('missing-pdf')

    def test_complete_portable_docs_and_no_data(self):
        output=self.build('first')
        with zipfile.ZipFile(output) as archive:
            names=set(archive.namelist())
            self.assertIn('README.md',names)
            self.assertIn('repository.yaml',names)
            self.assertIn('README.da.md',names)
            self.assertIn('README.en.md',names)
            self.assertIn('ROADMAP.md',names)
            self.assertIn('CONTRIBUTING.md',names)
            self.assertIn('assets/brand/logo-light.svg',names)
            self.assertEqual( archive.read('Home-Assistant/distrikt/icon.png'),b'FICTIONAL_ICON')
            self.assertEqual( archive.read('Home-Assistant/distrikt/logo.png'),b'FICTIONAL_LOGO')
            self.assertIn('assets/brand/logo-dark.svg',names)
            self.assertIn('docs/INSTALL.md',names)
            self.assertIn('Distrikt-lokal/app/server.py',names)
            self.assertIn('Home-Assistant/distrikt/app/server.py',names)
            self.assertIn('Home-Assistant/distrikt/app/kort-import-skabelon.xlsx',names)
            self.assertIn('Distrikt-lokal/app/kort-import-skabelon.xlsx',names)
            self.assertIn('Home-Assistant/distrikt/README.md',names)
            self.assertIn('Home-Assistant/distrikt/CHANGELOG.md',names)
            self.assertIn('Home-Assistant/distrikt/translations/da.yaml',names)
            self.assertIn('CONTRIBUTING.en.md',names)
            self.assertIn('Home-Assistant/SHA256SUMS.txt',names)
            self.assertFalse(any(n.startswith('data/') or n.endswith('.sqlite3') for n in names))
            self.assertFalse(any(b'DO_NOT_PACKAGE_PRIVATE_TEST_RECORD' in archive.read(n) for n in names))
            mode=archive.getinfo('Distrikt-lokal/Start-Distrikt.command').external_attr>>16
            self.assertEqual(mode&0o777,0o755)
        self.assertEqual((self.root/'data/kort.sqlite3').read_text(),'DO_NOT_PACKAGE_PRIVATE_TEST_RECORD')

    def test_portable_guide_links_reach_included_documents(self):
        self.add('README.md','[Notices](distrikt/THIRD-PARTY.md)\n')
        self.add('docs/INSTALL.md','[Sharing](../distrikt/GOOGLE-DRIVE-OPSAETNING.md)\n')
        self.add('distrikt/THIRD-PARTY.md','# Fictional notices\n')
        self.add('distrikt/GOOGLE-DRIVE-OPSAETNING.md','# Fictional sharing guide\n')
        with zipfile.ZipFile(self.build('links')) as archive:
            import posixpath,re
            for name in ('README.md','docs/INSTALL.md'):
                for target in re.findall(r'\]\(([^)]+)\)',archive.read(name).decode()):
                    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),target))
                    self.assertIn(resolved,archive.namelist())

    def test_changelog_matches_in_desktop_ha_and_project_archive(self):
        with zipfile.ZipFile(self.build('changelog')) as archive:
            for name in ('CHANGELOG.md','Distrikt-lokal/CHANGELOG.md','Home-Assistant/distrikt/CHANGELOG.md'):
                self.assertEqual(archive.read(name),self.changelog.encode())

    def test_stale_ha_changelog_blocks_release(self):
        self.add('distrikt/CHANGELOG.md','# Fictional changes\n\n## 9.8.0 · Previous version\n')
        with self.assertRaisesRegex(ValueError,'changelogs differ'):self.build('stale')

    def test_current_version_must_be_first_in_changelog(self):
        old_first=self.changelog.replace('## 9.9.0 · Current version','## 9.8.0 · Old version',1)
        for name in ('CHANGELOG.md','distrikt/CHANGELOG.md'):self.add(name,old_first+'\n## 9.9.0 · Misplaced version\n')
        with self.assertRaisesRegex(ValueError,'current version first'):self.build('old-first')

    def test_missing_changelog_version_blocks_release(self):
        for name in ('CHANGELOG.md','distrikt/CHANGELOG.md'):self.add(name,'# Fictional changes\n')
        with self.assertRaisesRegex(ValueError,'current version first'):self.build('missing-version')

    def test_all_packaged_relative_links_are_validated(self):
        self.add('docs/OTHER.md','[Missing](../missing-guide.md)\n')
        with self.assertRaisesRegex(ValueError,'Broken packaged guide link'):self.build('broken')

    def test_original_s12_pdf_is_required(self):
        (self.source/'templates/S-12-original.pdf').unlink()
        with self.assertRaisesRegex(ValueError,'missing blank form assets'):self.build('missing')

    def test_identical_inputs_make_identical_zip_bytes(self):
        self.assertEqual(self.build('first').read_bytes(),self.build('second').read_bytes())

    def test_missing_original_form_blocks_release(self):
        (self.source/'templates/S-13-background.jpg').unlink()
        with self.assertRaisesRegex(ValueError,'missing blank form assets'):self.build('output')

    def test_missing_excel_template_blocks_release(self):
        (self.source/'app/kort-import-skabelon.xlsx').unlink()
        with self.assertRaisesRegex(ValueError,'missing Excel import template'):self.build('output')

    def test_accidental_credential_json_in_program_tree_blocks_release(self):
        for name in ('drive-auth.json','datafordeler-auth.json','access.json','run.json'):
            with self.subTest(name=name):
                path=self.source/'app'/name
                path.write_text('{"credential":"FICTIONAL_TEST_ONLY"}')
                try:
                    with self.assertRaisesRegex(ValueError,'Private/runtime'):
                        release.files()
                finally:path.unlink()

    def test_accidental_database_in_program_tree_blocks_release(self):
        self.add('distrikt/app/accidental.sqlite3','fake private test record')
        with self.assertRaisesRegex(ValueError,'Private/runtime file'):self.build('output')

    def test_missing_linked_document_blocks_release(self):
        (self.root/'README.en.md').unlink()
        with self.assertRaisesRegex(ValueError,'Missing release document'):self.build('output')


if __name__=='__main__':unittest.main(verbosity=2)
