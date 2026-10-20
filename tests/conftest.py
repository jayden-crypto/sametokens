import pytest

from sametokens.runtimes import GGUF, MODEL_NAMES, MODELS, ROOT


def pytest_collection_modifyitems(config, items):
    """Tests that need tokenizer files / GGUFs are skipped on a fresh clone until `sametokens setup` ran."""
    ready = all((MODELS / m / "tokenizer.json").exists() and (GGUF / f"{m}.gguf").exists() for m in MODEL_NAMES)
    ready = ready and (ROOT / "js" / "node_modules").exists()
    if ready:
        return
    skip = pytest.mark.skip(reason="run `uv run sametokens setup` first")
    for item in items:
        if "tok" in item.fixturenames or item.name.startswith("test_plain"):
            item.add_marker(skip)
