"""Chat-template conformance: does each runtime render the same prompt text?

The reference renders the model's Jinja chat template with Python's jinja2 (via
transformers.apply_chat_template). transformers.js renders the *same* template
with its own JavaScript Jinja implementation (@huggingface/jinja). Any difference
in the rendered string means the model receives a different prompt.
"""

from __future__ import annotations

import difflib
from functools import lru_cache

from .runtimes import MODELS, Reference, TransformersJS


@lru_cache(maxsize=None)
def _runtimes(model: str) -> tuple[Reference, TransformersJS]:
    return Reference(model), TransformersJS(model)

CONVERSATIONS: dict[str, list[dict]] = {
    "single user turn": [{"role": "user", "content": "Hi there!"}],
    "with system": [{"role": "system", "content": "You are terse."}, {"role": "user", "content": "Hi"}],
    "multi-turn": [{"role": "user", "content": "2+2?"}, {"role": "assistant", "content": "4"},
                   {"role": "user", "content": "and 3+3?"}],
    "leading/trailing whitespace": [{"role": "user", "content": "\n\n  padded  \n"}],
    "empty content": [{"role": "user", "content": ""}],
    "unicode": [{"role": "user", "content": "नमस्ते 😀 café́"}],
    "template-looking text": [{"role": "user", "content": "{{ messages }} {% if x %}<|im_end|>"}],
    "assistant last (prefill)": [{"role": "user", "content": "Write a haiku"},
                                 {"role": "assistant", "content": "Autumn"}],
}


def render_both(model: str, messages: list[dict], add_generation_prompt: bool) -> tuple[str, str]:
    ref, js = _runtimes(model)
    kwargs = {}
    jinja_file = MODELS / model / "chat_template.jinja"
    if jinja_file.exists():
        # transformers.js only reads chat_template.jinja for multimodal processors,
        # so hand the template over explicitly (as the official ONNX repos inline it).
        kwargs = {"chat_template": jinja_file.read_text()}
    try:
        a = ref.tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=add_generation_prompt)
    except Exception as e:
        a = f"<error: {type(e).__name__}: {str(e)[:120]}>"
    try:
        b = js.template(messages, add_generation_prompt=add_generation_prompt, **kwargs)
    except Exception as e:
        b = f"<error: {str(e)[:120]}>"
    return a, b


def short_diff(a: str, b: str) -> str:
    sm = difflib.SequenceMatcher(a=a, b=b)
    parts = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            parts.append(f"{op}: ref {a[max(0, i1 - 15):i2 + 15]!r} vs js {b[max(0, j1 - 15):j2 + 15]!r}")
    return " | ".join(parts[:2])


def run_templates(models: list[str]) -> list[dict]:
    rows = []
    for model in models:
        for name, msgs in CONVERSATIONS.items():
            for agp in (True, False):
                a, b = render_both(model, msgs, agp)
                rows.append({"model": model, "conversation": name, "add_generation_prompt": agp,
                             "same": a == b, "diff": "" if a == b else short_diff(a, b),
                             "reference": a, "transformers_js": b})
    return rows
