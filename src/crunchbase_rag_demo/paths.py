from __future__ import annotations

from pathlib import Path

DEFAULT_RECORDS = Path("data/processed/companies.jsonl")
DEFAULT_INDEX = Path("data/index/tfidf.json")
DEFAULT_RAW_CSV = Path("data/raw/crunchbase-companies.csv")
SOURCE_REPO_URL = "https://github.com/datahoarder/crunchbase-october-2013"
SOURCE_ARCHIVE_URL = f"{SOURCE_REPO_URL}/archive/refs/heads/master.zip"
SOURCE_COMPANIES_CSV = "crunchbase-companies.csv"
