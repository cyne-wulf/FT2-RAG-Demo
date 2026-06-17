from crunchbase_rag_demo.data import read_csv_records
from crunchbase_rag_demo.retrieval import TfidfIndex


def test_search_finds_retail_analytics_companies(tmp_path):
    csv_path = tmp_path / "objects.csv"
    csv_path.write_text(
        "\n".join(
            [
                "id,entity_type,name,category_code,status,city,state_code,country_code,description,overview,tag_list",
                "c:1,Company,LocalIQ,analytics,operating,San Francisco,CA,USA,Location analytics for retailers,Helps retailers understand local customer behavior,retail analytics",
                "c:2,Company,MarketLens,advertising,operating,New York,NY,USA,Audience intelligence for brands,Recommends customer segments for retailers,retail analytics",
                "c:3,Company,CloudLedger,enterprise,operating,Seattle,WA,USA,Cloud accounting workflow software,Automates invoice approvals,finance",
            ]
        ),
        encoding="utf-8",
    )
    records = read_csv_records(csv_path)
    index = TfidfIndex.build(records)

    results = index.search("retail customer behavior analytics", k=3)

    names = [result.record.name for result in results]
    assert "LocalIQ" in names
    assert "MarketLens" in names
    assert results[0].score > 0
