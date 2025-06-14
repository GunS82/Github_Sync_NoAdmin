import tempfile
import os
import subprocess
import zipfile
from pathlib import Path
from unittest import mock, TestCase

import deploy_library as dl

class DummyResponse:
    def __init__(self, data: bytes):
        self.data = data
        self.status_code = 200
    def raise_for_status(self):
        pass
    def iter_content(self, chunk_size=1):
        yield self.data

class DeployLibraryTests(TestCase):
    def test_get_repo_url_from_env_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(dl.get_repo_url_from_env())

    def test_get_repo_url_from_env_present(self):
        with mock.patch.dict(os.environ, {dl.REPO_URL_ENV_VAR: 'https://example.com'}):
            self.assertEqual(dl.get_repo_url_from_env(), 'https://example.com')

    def test_download_repo_zip(self):
        dummy_data = b'TESTDATA'
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            with mock.patch('requests.get', return_value=DummyResponse(dummy_data)):
                zip_path = dl.download_repo_zip('https://example.com/repo.zip', temp_path)
                self.assertIsNotNone(zip_path)
                self.assertEqual(zip_path.read_bytes(), dummy_data)

    def test_download_repo_zip_branch_override(self):
        dummy_data = b'TESTDATA'
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            with mock.patch.dict(os.environ, {dl.BRANCH_ENV_VAR: 'feature'}):
                with mock.patch('requests.get', return_value=DummyResponse(dummy_data)) as mock_get:
                    zip_path = dl.download_repo_zip('https://example.com/repo', temp_path)
                    self.assertIsNotNone(zip_path)
                    expected_url = 'https://example.com/repo/archive/refs/heads/feature.zip'
                    mock_get.assert_called_with(expected_url, stream=True, timeout=30)

    def test_extract_repo_zip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            zip_file = tmp_path / 'archive.zip'
            with zipfile.ZipFile(zip_file, 'w') as zf:
                zf.writestr('file.txt', 'content')
            extract_dir = tmp_path / 'extract'
            extract_dir.mkdir()
            self.assertIsNotNone(dl.extract_repo_zip(zip_file, extract_dir))
            self.assertTrue((extract_dir / 'file.txt').is_file())

    def test_find_library_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            root_dir = tmp_path / 'libroot'
            root_dir.mkdir()
            (root_dir / '__init__.py').write_text('')
            self.assertEqual(dl.find_library_root(tmp_path), root_dir)

    def test_create_virtual_env(self):
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0)
            self.assertTrue(dl.create_virtual_env(Path('venv')))

    def test_install_library_in_venv(self):
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = subprocess.CompletedProcess([], 0)
            self.assertTrue(dl.install_library_in_venv(Path('venv'), Path('lib')))

    def test_cleanup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            dir_to_remove = tmp_path / 'dir'
            dir_to_remove.mkdir()
            (dir_to_remove / 'file.txt').write_text('data')
            dl.cleanup([dir_to_remove])
            self.assertFalse(dir_to_remove.exists())
