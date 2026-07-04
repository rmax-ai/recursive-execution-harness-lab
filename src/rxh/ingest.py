from __future__ import annotations

import hashlib
from pathlib import Path

from .models import DocumentRef

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_corpus(corpus_path: Path, out_path: Path) -> list[DocumentRef]:
    """Walk corpus directory, read .md/.txt files, produce DocumentRef list."""
    docs: list[DocumentRef] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for i, path in enumerate(sorted(corpus_path.rglob("*"))):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        doc = DocumentRef(
            id=f"doc_{i:04d}",
            source_path=str(path),
            title=path.stem,
            content_hash=hash_text(text),
            char_count=len(text),
            metadata={"extension": path.suffix.lower()},
        )
        docs.append(doc)

    with out_path.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(doc.model_dump_json() + "\n")

    return docs


def load_document_text(doc: DocumentRef) -> str:
    """Read the full text of a document from its source path."""
    return Path(doc.source_path).read_text(encoding="utf-8", errors="ignore")


def load_documents_jsonl(path: Path) -> list[DocumentRef]:
    """Load DocumentRef objects from a JSONL file."""
    docs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            docs.append(DocumentRef.model_validate_json(line))
    return docs
