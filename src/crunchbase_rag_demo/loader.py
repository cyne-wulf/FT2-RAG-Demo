from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from crunchbase_rag_demo.paths import DEFAULT_RAW_CSV, SOURCE_ARCHIVE_URL, SOURCE_COMPANIES_CSV


def ensure_crunchbase_companies_csv(path: Path = DEFAULT_RAW_CSV) -> Path:
    if path.exists():
        return path
    return download_crunchbase_companies_csv(path)


def download_crunchbase_companies_csv(path: Path = DEFAULT_RAW_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / "crunchbase-october-2013.zip"
        with urllib.request.urlopen(SOURCE_ARCHIVE_URL) as response:
            with archive_path.open("wb") as archive_file:
                shutil.copyfileobj(response, archive_file)

        with zipfile.ZipFile(archive_path) as archive:
            member = _find_companies_member(archive)
            temp_csv = Path(temp_dir) / SOURCE_COMPANIES_CSV
            with archive.open(member) as source_file:
                with temp_csv.open("wb") as output_file:
                    shutil.copyfileobj(source_file, output_file)

        temp_csv.replace(path)
    return path


def _find_companies_member(archive: zipfile.ZipFile) -> str:
    for name in archive.namelist():
        if name.endswith(f"/{SOURCE_COMPANIES_CSV}") or name == SOURCE_COMPANIES_CSV:
            return name
    raise FileNotFoundError(f"{SOURCE_COMPANIES_CSV} was not found in the source archive.")
