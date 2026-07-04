from __future__ import annotations

from pathlib import Path

import pytest

from rxh.models import DocumentRef, TaskSpec
from rxh.providers import MockProvider


@pytest.fixture
def sample_task() -> TaskSpec:
    return TaskSpec(
        id="test_task",
        title="Test Task",
        question="What is the answer?",
        success_criteria=["Use sources"],
        constraints=["No speculation"],
    )


@pytest.fixture
def sample_docs() -> list[DocumentRef]:
    return [
        DocumentRef(
            id="doc_0001",
            source_path="/f/d1.md",
            title="Doc1",
            content_hash="a1",
            char_count=200,
        ),
        DocumentRef(
            id="doc_0002",
            source_path="/f/d2.md",
            title="Doc2",
            content_hash="b2",
            char_count=300,
        ),
    ]


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider([])


@pytest.fixture
def tmp_corpus(tmp_path: Path) -> Path:
    (tmp_path / "doc1.md").write_text(
        "# Doc 1\n\nContent of document one.", encoding="utf-8"
    )
    (tmp_path / "doc2.txt").write_text("Content of document two.", encoding="utf-8")
    (tmp_path / "skip.pdf").write_text("fake pdf", encoding="utf-8")
    return tmp_path
