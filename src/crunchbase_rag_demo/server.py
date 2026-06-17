from __future__ import annotations

import json
import mimetypes
import shutil
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import PurePosixPath
from urllib.parse import urlparse

from crunchbase_rag_demo.generation import answer_with_codex, build_rag_prompt
from crunchbase_rag_demo.paths import DEFAULT_INDEX, DEFAULT_RECORDS
from crunchbase_rag_demo.retrieval import SearchResult, TfidfIndex

STATIC_ROOT = files("crunchbase_rag_demo").joinpath("web")


def serve_app(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), RagRequestHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


class RagRequestHandler(BaseHTTPRequestHandler):
    server_version = "CrunchbaseRagDemo/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            self._send_json(status_payload())
            return
        if path == "/" or path == "":
            self._send_static("index.html")
            return
        self._send_static(path.lstrip("/"))

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            if path == "/api/search":
                payload = self._read_json()
                question = str(payload.get("question", "")).strip()
                top_k = int(payload.get("top_k", 5))
                results, prompt = run_retrieval(question, top_k)
                self._send_json({"results": serialize_results(results), "prompt": prompt})
                return
            if path == "/api/ask":
                payload = self._read_json()
                question = str(payload.get("question", "")).strip()
                top_k = int(payload.get("top_k", 5))
                results, prompt = run_retrieval(question, top_k)
                answer = answer_with_codex(question, results)
                self._send_json(
                    {
                        "results": serialize_results(results),
                        "prompt": prompt,
                        "answer": answer,
                    }
                )
                return
            self.send_error(404)
        except (json.JSONDecodeError, OSError, ValueError) as error:
            self._send_json({"error": str(error)}, status=400)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, payload: dict[str, object], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, name: str) -> None:
        parts = PurePosixPath(name).parts
        if not parts or any(part in {"..", ""} for part in parts) or parts[0] == "api":
            self.send_error(404)
            return
        resource = STATIC_ROOT.joinpath(name)
        if not resource.is_file():
            self.send_error(404)
            return
        content = resource.read_bytes()
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_retrieval(question: str, top_k: int) -> tuple[list[SearchResult], str]:
    if not question:
        raise ValueError("Question must not be empty.")
    index = load_or_create_index()
    results = index.search(question, k=max(1, min(top_k, 12)))
    return results, build_rag_prompt(question, results)


def load_or_create_index() -> TfidfIndex:
    if DEFAULT_INDEX.exists():
        return TfidfIndex.load(DEFAULT_INDEX)
    raise FileNotFoundError("No local index exists. Restart with `crunchbase-rag serve`.")


def serialize_results(results: list[SearchResult]) -> list[dict[str, object]]:
    return [
        {
            "score": result.score,
            "record": asdict(result.record),
        }
        for result in results
    ]


def status_payload() -> dict[str, object]:
    return {
        "index_exists": DEFAULT_INDEX.exists(),
        "records_exists": DEFAULT_RECORDS.exists(),
        "index_path": str(DEFAULT_INDEX),
        "records_path": str(DEFAULT_RECORDS),
        "codex_available": shutil.which("codex") is not None,
    }
