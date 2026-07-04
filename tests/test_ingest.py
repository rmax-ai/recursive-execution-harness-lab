from __future__ import annotations

from pathlib import Path

from rxh.ingest import ingest_corpus, load_documents_jsonl


def test_ingest_corpus_reads_md_and_txt_skips_pdf(
    tmp_corpus: Path, tmp_path: Path
) -> None:
    out_path = tmp_path / "out" / "documents.jsonl"

    docs = ingest_corpus(tmp_corpus, out_path)

    assert [doc.source_path for doc in docs] == [
        str(tmp_corpus / "doc1.md"),
        str(tmp_corpus / "doc2.txt"),
    ]
    assert [doc.id for doc in docs] == ["doc_0000", "doc_0001"]
    assert docs[0].char_count == len("# Doc 1\n\nContent of document one.")
    assert docs[1].char_count == len("Content of document two.")


def test_load_documents_jsonl_round_trips(tmp_corpus: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "out" / "documents.jsonl"
    docs = ingest_corpus(tmp_corpus, out_path)

    loaded = load_documents_jsonl(out_path)

    assert loaded == docs
