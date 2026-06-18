# Crunchbase RAG Demo

A minimal local RAG app for the October 2013 Crunchbase snapshot.

The app downloads the public snapshot from [datahoarder/crunchbase-october-2013](https://github.com/datahoarder/crunchbase-october-2013), extracts `crunchbase-companies.csv`, builds a local search index, opens a browser UI, and lets you ask questions over the companies in that snapshot.

## What It Does

- Downloads and extracts `crunchbase-companies.csv` from the source repository when needed.
- Normalizes company rows into searchable text.
- Builds a local JSON TF-IDF index.
- Opens a local webpage with a prompt box.
- Shows retrieved company records and the exact prompt sent to Codex.
- Uses your local Codex login only when you click **Ask Codex**.

No database, Docker, Node, GPU, hosted embedding service, or OpenAI API key is required.

## Setup

Run these commands one at a time, in order. Copy one command, run it, wait for it to finish, then copy the next command.

```bash
git clone https://github.com/cyne-wulf/FT2-RAG-Demo
```

```bash
cd FT2-RAG-Demo
```

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
git clone https://github.com/cyne-wulf/FT2-RAG-Demo
```

```powershell
cd FT2-RAG-Demo
```

```powershell
py -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -e ".[dev]"
```

## Run

```bash
crunchbase-rag serve
```

On first run, this downloads the GitHub archive for [datahoarder/crunchbase-october-2013](https://github.com/datahoarder/crunchbase-october-2013), extracts `crunchbase-companies.csv` to `data/raw/crunchbase-companies.csv`, builds a local index, and opens `http://127.0.0.1:8000`.

If you already have a local copy, pass it directly:

```bash
crunchbase-rag serve path/to/crunchbase-companies.csv
```

By default, the first 2,000 company rows are indexed so startup stays fast. To index every matching company row:

```bash
crunchbase-rag serve --limit 0
```

## Codex Login

Retrieval is local. Generated answers use the Codex CLI, so authenticate once with your Codex subscription:

```bash
codex login
```

If browser login is unavailable:

```bash
codex login --device-auth
```

You can still use the webpage to retrieve records and inspect the assembled prompt without logging in. Login is only needed for **Ask Codex**.

## Data

This repo does not redistribute the Crunchbase snapshot. The loader pulls the upstream archive at runtime and stores only your local extracted copy under `data/raw/`, which is ignored by Git.

Source: [datahoarder/crunchbase-october-2013](https://github.com/datahoarder/crunchbase-october-2013)

## Development

```bash
pytest
```

The runtime app uses only the Python standard library. `pytest` is only for tests.
