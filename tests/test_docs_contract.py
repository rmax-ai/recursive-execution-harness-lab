from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_avoids_removed_architecture_claims() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "reference-based execution" not in readme
    assert "Reference-Based Execution" not in readme
    assert "Reference-Indexed Execution" in readme
    assert "policy gate" in readme


def test_site_source_avoids_removed_architecture_claims() -> None:
    hero = (ROOT / "site/src/lib/components/sections/Hero.svelte").read_text(
        encoding="utf-8"
    )
    mode_comparison = (
        ROOT / "site/src/lib/components/sections/ModeComparison.svelte"
    ).read_text(encoding="utf-8")
    pipeline = (ROOT / "site/src/lib/components/sections/Pipeline.svelte").read_text(
        encoding="utf-8"
    )

    assert "reference-based execution" not in hero
    assert "policy gate" in mode_comparison
    assert "governed execution graph" not in pipeline
    assert "reference-indexed bounded execution" in hero


def test_site_config_defaults_to_root_safe_base_path() -> None:
    svelte_config = (ROOT / "site/svelte.config.js").read_text(encoding="utf-8")

    assert 'const base = process.env.SITE_BASE_PATH ?? "";' in svelte_config
    assert 'base: "/recursive-execution-harness-lab"' not in svelte_config
