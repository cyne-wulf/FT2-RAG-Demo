from __future__ import annotations

import shutil
import subprocess

from crunchbase_rag_demo.retrieval import SearchResult


ANSWER_INSTRUCTIONS = """You are answering a question about the 2013 Crunchbase dataset.
Use only the supplied retrieved context.
Do not edit files, run shell commands, or use external tools.
If the context is thin or does not contain the answer, say what is missing.
Cite company names from the context in the answer."""


def build_rag_prompt(question: str, results: list[SearchResult]) -> str:
    context_blocks = []
    for number, result in enumerate(results, start=1):
        record = result.record
        context_blocks.append(
            "\n".join(
                [
                    f"[{number}] {record.citation()}",
                    f"Source: {record.source}",
                    f"Relevance score: {result.score:.3f}",
                    record.search_text(),
                ]
            )
        )

    context = "\n\n".join(context_blocks) if context_blocks else "No retrieved records."
    return f"""{ANSWER_INSTRUCTIONS}

Question:
{question}

Retrieved Crunchbase context:
{context}

Answer with a concise, evidence-grounded response."""


def answer_with_codex(question: str, results: list[SearchResult]) -> str:
    prompt = build_rag_prompt(question, results)
    if shutil.which("codex") is None:
        return (
            "The Codex CLI was not found, so no model call was made.\n\n"
            "Install Codex, run `codex login`, then retry this command. "
            "Here is the RAG prompt that would be sent to Codex:\n\n"
            f"{prompt}"
        )

    try:
        completed = subprocess.run(
            ["codex", "exec", "--ephemeral", "--sandbox", "read-only", "-"],
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return "Codex did not finish within 180 seconds. Try again with fewer retrieved records."

    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
        return (
            "Codex could not answer with the current local login.\n\n"
            "Run `codex login` to authenticate with ChatGPT/Codex OAuth, then retry. "
            "If browser login is unavailable, run `codex login --device-auth`.\n\n"
            f"Codex output:\n{details}\n\n"
            f"RAG prompt:\n{prompt}"
        )

    return completed.stdout.strip()
