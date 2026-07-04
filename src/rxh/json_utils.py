from __future__ import annotations

import json


def extract_json_object(text: str) -> dict:
    """Extract the first complete JSON object from text.

    Finds the first '{' and last '}' and parses the content between them.
    Raises ValueError if no JSON object is found.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return json.loads(text[start : end + 1])
