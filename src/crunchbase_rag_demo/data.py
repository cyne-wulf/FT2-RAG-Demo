from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CompanyRecord:
    record_id: str
    name: str
    category: str
    status: str
    founded: str
    location: str
    funding_total_usd: str
    homepage_url: str
    summary: str
    source: str

    def search_text(self) -> str:
        parts = [
            self.name,
            self.category,
            self.status,
            self.founded,
            self.location,
            self.funding_total_usd,
            self.homepage_url,
            self.summary,
        ]
        return "\n".join(part for part in parts if part)

    def citation(self) -> str:
        details = [self.category, self.location, self.founded]
        suffix = " | ".join(part for part in details if part)
        return f"{self.name} ({suffix})" if suffix else self.name


def read_csv_records(path: Path, limit: int | None = None) -> list[CompanyRecord]:
    try:
        return _read_csv_records_with_encoding(path, "utf-8-sig", limit)
    except UnicodeDecodeError:
        return _read_csv_records_with_encoding(path, "latin-1", limit)


def _read_csv_records_with_encoding(
    path: Path,
    encoding: str,
    limit: int | None = None,
) -> list[CompanyRecord]:
    records: list[CompanyRecord] = []
    with path.open(newline="", encoding=encoding) as file:
        reader = csv.DictReader(file)
        for row in reader:
            record = normalize_row(row, source=path.name)
            if record is None:
                continue
            records.append(record)
            if limit is not None and len(records) >= limit:
                break
    return records


def normalize_row(row: dict[str, str], source: str) -> CompanyRecord | None:
    entity_type = _first(row, ["entity_type", "type", "roles"])
    if entity_type and not _looks_like_company(entity_type):
        return None

    name = _first(row, ["name", "company_name", "organization_name"])
    if not name:
        return None

    location = ", ".join(
        part
        for part in [
            _first(row, ["city"]),
            _first(row, ["region", "state_code"]),
            _first(row, ["country_code", "country"]),
        ]
        if part
    )

    summary = _clean_text(
        " ".join(
            part
            for part in [
                _first(row, ["short_description", "description"]),
                _first(row, ["overview", "long_description"]),
                _first(row, ["tag_list", "category_list", "category_groups_list"]),
            ]
            if part
        )
    )
    category = _first(row, ["category_code", "category_groups_list", "category_list"])
    status = _first(row, ["status"])
    founded = _first(row, ["founded_at", "founded_on"])
    funding_total_usd = _first(row, ["funding_total_usd", "total_funding_usd"])
    if not summary:
        summary = _clean_text(
            " ".join(
                part
                for part in [
                    f"Category: {category}" if category else "",
                    f"Status: {status}" if status else "",
                    f"Founded: {founded}" if founded else "",
                    f"Total funding USD: {funding_total_usd}" if funding_total_usd else "",
                ]
                if part
            )
        )

    return CompanyRecord(
        record_id=_first(row, ["id", "uuid", "permalink", "entity_id"]) or name,
        name=name,
        category=category,
        status=status,
        founded=founded,
        location=location,
        funding_total_usd=funding_total_usd,
        homepage_url=_first(row, ["homepage_url", "domain", "website_url"]),
        summary=summary,
        source=source,
    )


def write_jsonl(records: Iterable[CompanyRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[CompanyRecord]:
    records: list[CompanyRecord] = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(CompanyRecord(**json.loads(line)))
    return records


def _first(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and value.strip():
            return value.strip()
    return ""


def _looks_like_company(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in ["company", "organization", "primary_company"])


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\\n", " ").replace("\n", " ").split())
