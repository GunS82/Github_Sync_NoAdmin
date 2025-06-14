import os
import sys
import subprocess
import requests
import zipfile
import tempfile
import shutil
import logging
from pathlib import Path
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

REPO_URL_ENV_VAR = "PYTHON_LIB_GITHUB_URL"
DEFAULT_BRANCH = "main"

def get_repo_name_from_url(repo_url: str) -> str | None:
    """Extract repository name from GitHub URL or zip link."""
    try:
        path_parts = [p for p in urlparse(repo_url).path.split("/") if p]
        if not path_parts:
            return None
        if "archive" in path_parts:
            idx = path_parts.index("archive") - 1
            if idx >= 0:
                return path_parts[idx]
        return path_parts[-1].removesuffix(".zip")
    except Exception as exc:
        logging.error(f"Не удалось определить имя репозитория: {exc}")
        return None

def get_repo_url_from_env():
    """Return repository URL from environment variable."""
    repo_url = os.environ.get(REPO_URL_ENV_VAR)
    if not repo_url:
        logging.error(f"Переменная окружения {REPO_URL_ENV_VAR} не установлена.")
        return None
    return repo_url.strip()

def download_repo_zip(repo_url, temp_dir_path):
    """Download repository archive and return path to the zip file."""
    try:
        if repo_url.endswith(".zip"):
            zip_url = repo_url
        else:
            cleaned = repo_url.rstrip("/")
            zip_url = f"{cleaned}/archive/refs/heads/{DEFAULT_BRANCH}.zip"
        response = requests.get(zip_url, stream=True, timeout=30)
        response.raise_for_status()
        zip_file_path = Path(temp_dir_path) / "repo.zip"
        with open(zip_file_path, "wb") as fh:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    fh.write(chunk)
        logging.info(f"Архив скачан: {zip_file_path}")
        return zip_file_path
    except Exception as exc:
        logging.error(f"Не удалось скачать архив: {exc}")
        return None

def extract_repo_zip(zip_path, extract_to_dir_path):
    """Extract zip archive to directory."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to_dir_path)
        logging.info(f"Архив распакован в {extract_to_dir_path}")
        return extract_to_dir_path
    except Exception as exc:
        logging.error(f"Не удалось распаковать архив: {exc}")
        return None

def find_library_root(extract_to_dir_path):
    """Find top-level library directory."""
    try:
        dirs = [p for p in Path(extract_to_dir_path).iterdir() if p.is_dir()]
        if len(dirs) != 1:
            logging.error("Не удалось определить корневую папку библиотеки.")
            return None
        logging.info(f"Найдена корневая папка библиотеки: {dirs[0]}")
        return dirs[0]
    except Exception as exc:
        logging.error(f"Ошибка при поиске корневой папки: {exc}")
        return None

def guess_package_name(library_root: Path) -> str | None:
    """Attempt to determine Python package name from library root."""
    try:
        candidates = [p for p in library_root.iterdir() if (p / "__init__.py").is_file()]
        if candidates:
            return candidates[0].name
    except Exception as exc:
        logging.error(f"Ошибка определения имени пакета: {exc}")
    return library_root.name

def create_virtual_env(venv_path):
    """Create virtual environment."""
    try:
        result = subprocess.run([sys.executable, "-m", "venv", str(venv_path)], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Не удалось создать виртуальное окружение: {result.stderr}")
            return False
        logging.info(f"Виртуальное окружение создано по пути {venv_path}")
        return True
    except Exception as exc:
        logging.error(f"Ошибка при создании виртуального окружения: {exc}")
        return False

def install_library_in_venv(venv_path, library_source_path):
    """Install library into virtual environment."""
    pip_dir = "Scripts" if os.name == "nt" else "bin"
    pip_exe = "pip.exe" if os.name == "nt" else "pip"
    pip_path = Path(venv_path) / pip_dir / pip_exe
    try:
        result = subprocess.run([str(pip_path), "install", str(library_source_path)], capture_output=True, text=True)
        if result.returncode != 0:
            logging.error(f"Ошибка установки библиотеки: {result.stderr}")
            return False
        logging.info("Библиотека успешно установлена.")
        return True
    except Exception as exc:
        logging.error(f"Не удалось установить библиотеку: {exc}")
        return False

def run_demonstration(venv_path, library_name):
    """Run small demonstration script inside virtual environment."""
    python_dir = "Scripts" if os.name == "nt" else "bin"
    python_exe = "python.exe" if os.name == "nt" else "python"
    python_path = Path(venv_path) / python_dir / python_exe
    demo_script = Path(venv_path) / "demo_script.py"
    demo_code = (
        f"import {library_name}\n"
        f"version = getattr({library_name}, '__version__', getattr({library_name}, 'version', 'unknown'))\n"
        f"print(f'Версия библиотеки {library_name}: {{version}}')\n"
    )
    try:
        demo_script.write_text(demo_code, encoding="utf-8")
        result = subprocess.run([str(python_path), str(demo_script)], capture_output=True, text=True)
        logging.info(f"Демонстрация вывода: {result.stdout.strip()}")
        if result.stderr:
            logging.warning(f"Сообщения ошибки демонстрации: {result.stderr.strip()}")
    except Exception as exc:
        logging.error(f"Ошибка выполнения демонстрации: {exc}")
    finally:
        if demo_script.exists():
            demo_script.unlink()

def cleanup(paths_to_remove):
    """Remove temporary directories."""
    for path in paths_to_remove:
        try:
            shutil.rmtree(path, ignore_errors=True)
            logging.info(f"Удалена директория {path}")
        except Exception as exc:
            logging.error(f"Не удалось удалить {path}: {exc}")

def main():
    logging.info("Начало процесса развертывания Python библиотеки.")
    repo_url_str = None
    venv_dir_path = None
    paths_to_clean = []
    try:
        repo_url_str = get_repo_url_from_env()
        if not repo_url_str:
            return
        temp_base_dir = Path(tempfile.mkdtemp(prefix="codex_lib_deploy_"))
        paths_to_clean.append(temp_base_dir)
        logging.info(f"Создана временная директория: {temp_base_dir}")
        temp_download_dir = temp_base_dir / "download"
        temp_download_dir.mkdir()
        temp_extract_dir = temp_base_dir / "extracted"
        temp_extract_dir.mkdir()
        venv_dir_path = temp_base_dir / "venv"
        zip_file_path = download_repo_zip(repo_url_str, temp_download_dir)
        if not zip_file_path:
            return
        extracted_content_path = extract_repo_zip(zip_file_path, temp_extract_dir)
        if not extracted_content_path:
            return
        library_root_path = find_library_root(extracted_content_path)
        if not library_root_path:
            return
        library_name_for_import = guess_package_name(library_root_path)
        if not library_name_for_import:
            logging.error("Не удалось определить имя пакета для импорта.")
            return
        if not create_virtual_env(venv_dir_path):
            return
        if not install_library_in_venv(venv_dir_path, library_root_path):
            return
        logging.info("Попытка запуска демонстрационного кода (если реализовано)...")
        run_demonstration(venv_dir_path, library_name_for_import)
        logging.info("Процесс успешно завершен.")
    except Exception as exc:
        logging.error(f"Произошла критическая ошибка: {exc}", exc_info=True)
    finally:
        logging.info("Запуск процесса очистки...")
        cleanup(paths_to_clean)
        logging.info("Очистка завершена.")

if __name__ == "__main__":
    main()
