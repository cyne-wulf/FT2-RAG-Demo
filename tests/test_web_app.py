from pathlib import Path


APP_JS = Path(__file__).resolve().parents[1] / "src" / "crunchbase_rag_demo" / "web" / "app.js"


def test_app_does_not_retrieve_on_page_load() -> None:
    script = APP_JS.read_text(encoding="utf-8")
    startup_script = script.split('fetch("/api/status")', maxsplit=1)[1]

    assert 'searchButton.addEventListener("click", retrieve);' in script
    assert 'fetch("/api/status")' in script
    assert "retrieve();" not in startup_script
