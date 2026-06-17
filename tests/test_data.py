from crunchbase_rag_demo.data import normalize_row, read_csv_records


def test_normalize_old_crunchbase_company_row():
    record = normalize_row(
        {
            "id": "c:123",
            "entity_type": "Company",
            "name": "ExampleCo",
            "category_code": "analytics",
            "status": "operating",
            "founded_at": "2011-01-01",
            "city": "San Francisco",
            "state_code": "CA",
            "country_code": "USA",
            "description": "Customer analytics",
            "overview": "Helps retailers understand behavior.",
            "funding_total_usd": "1000000",
        },
        source="objects.csv",
    )

    assert record is not None
    assert record.name == "ExampleCo"
    assert record.location == "San Francisco, CA, USA"
    assert "retailers" in record.search_text()


def test_read_csv_records_filters_non_companies(tmp_path):
    csv_path = tmp_path / "objects.csv"
    csv_path.write_text(
        "\n".join(
            [
                "id,entity_type,name,category_code,status,city,state_code,country_code,description",
                "c:1,Company,ExampleCo,analytics,operating,San Francisco,CA,USA,Customer analytics",
                "p:1,Person,Jane Doe,,,,,,Not a company",
            ]
        ),
        encoding="utf-8",
    )

    records = read_csv_records(csv_path)

    assert len(records) == 1
    assert records[0].source == "objects.csv"
