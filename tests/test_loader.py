import zipfile

from crunchbase_rag_demo import loader


def test_download_crunchbase_companies_csv_extracts_source_member(tmp_path, monkeypatch):
    archive_path = tmp_path / "source.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "crunchbase-october-2013-master/crunchbase-companies.csv",
            "permalink,name,category_code\n/company/example,ExampleCo,analytics\n",
        )

    class LocalResponse:
        def __enter__(self):
            self.file = archive_path.open("rb")
            return self.file

        def __exit__(self, exc_type, exc, traceback):
            self.file.close()

    monkeypatch.setattr(loader.urllib.request, "urlopen", lambda _url: LocalResponse())

    output_path = tmp_path / "data" / "raw" / "crunchbase-companies.csv"

    result = loader.download_crunchbase_companies_csv(output_path)

    assert result == output_path
    assert output_path.read_text(encoding="utf-8").startswith("permalink,name,category_code")
