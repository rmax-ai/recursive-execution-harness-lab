from __future__ import annotations

import pytest

from rxh.json_utils import extract_json_object


def test_extract_json_object_plain_json() -> None:
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_extract_json_object_with_prefix_and_suffix_text() -> None:
    text = 'prefix {"a": 1, "b": "two"} suffix'

    assert extract_json_object(text) == {"a": 1, "b": "two"}


def test_extract_json_object_raises_on_missing_json() -> None:
    with pytest.raises(ValueError, match="No JSON object found"):
        extract_json_object("no json here")


def test_extract_json_object_raises_on_empty_string() -> None:
    with pytest.raises(ValueError, match="No JSON object found"):
        extract_json_object("")
