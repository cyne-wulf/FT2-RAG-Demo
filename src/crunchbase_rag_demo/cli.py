from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from crunchbase_rag_demo.data import read_csv_records, write_jsonl
from crunchbase_rag_demo.loader import ensure_crunchbase_companies_csv
from crunchbase_rag_demo.paths import DEFAULT_INDEX, DEFAULT_RAW_CSV, DEFAULT_RECORDS
from crunchbase_rag_demo.retrieval import TfidfIndex
from crunchbase_rag_demo.server import serve_app


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


def build_local_index(args: argparse.Namespace) -> None:
    input_csv = args.input_csv
    if input_csv == DEFAULT_RAW_CSV and not input_csv.exists():
        print("Downloading Crunchbase October 2013 companies CSV...")
        input_csv = ensure_crunchbase_companies_csv(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(
            f"{input_csv} was not found. Put the Crunchbase snapshot CSV there, "
            "or pass its path to `crunchbase-rag serve`."
        )
    limit = None if args.limit <= 0 else args.limit
    records = read_csv_records(input_csv, limit=limit)
    write_jsonl(records, DEFAULT_RECORDS)
    index = TfidfIndex.build(records)
    index.save(DEFAULT_INDEX)
    print(f"Loaded {len(records)} company records from {input_csv}")
    print(f"Wrote {DEFAULT_RECORDS}")
    print(f"Wrote {DEFAULT_INDEX}")


def serve(args: argparse.Namespace) -> None:
    build_local_index(args)
    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        webbrowser.open(url)
    print(f"Serving Crunchbase RAG at {url}")
    print("Press Ctrl+C to stop.")
    try:
        serve_app(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nServer stopped.")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crunchbase-rag",
        description="Run a local browser RAG app over a Crunchbase snapshot CSV.",
    )
    subparsers = parser.add_subparsers(required=True)

    serve_parser = subparsers.add_parser("serve", help="Build the local index and open the app.")
    serve_parser.add_argument(
        "input_csv",
        nargs="?",
        default=DEFAULT_RAW_CSV,
        type=Path,
        help=f"Path to the Crunchbase companies CSV. Default: {DEFAULT_RAW_CSV}",
    )
    serve_parser.add_argument("--limit", type=int, default=2000, help="Use 0 for no limit.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--no-browser", action="store_true")
    serve_parser.set_defaults(func=serve)

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
