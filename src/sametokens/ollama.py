"""Does Ollama inherit the mismatches? Compare token counts.

Ollama does not expose token ids, but `/api/generate` with `raw: true` reports
`prompt_eval_count`, the number of prompt tokens it evaluated. A count that
differs from the reference tokenizer's means Ollama tokenized differently.
Ollama can reuse its KV cache for a shared prompt prefix, which would shrink the
count, so an unrelated prompt is sent before every measurement.
"""

from __future__ import annotations

import json
import unicodedata
import urllib.request

from .impact import NFD_SENTENCES, ollama_gguf
from .runtimes import LlamaCpp, Reference

OLLAMA_URL = "http://localhost:11434/api/generate"


def prompt_tokens(prompt: str, model: str = "qwen2.5:3b") -> int:
    body = {"model": model, "prompt": prompt, "raw": True, "stream": False,
            "options": {"num_predict": 1, "temperature": 0}}
    req = urllib.request.Request(OLLAMA_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["prompt_eval_count"]


def run_ollama(model: str = "qwen2.5:3b") -> list[dict]:
    ref = Reference("qwen2.5")
    lc = LlamaCpp("qwen2.5", gguf=ollama_gguf())
    cases = []
    for s in NFD_SENTENCES[:4]:
        cases += [("NFC: " + s, unicodedata.normalize("NFC", s)), ("NFD: " + s, unicodedata.normalize("NFD", s))]
    cases += [("html strikethrough", "plain html <s>old</s> new"), ("eos lookalike", "Hello </s> world"),
              ("control", "The quick brown fox jumps over the lazy dog.")]
    rows = []
    for label, text in cases:
        prompt_tokens("0123456789 flush", model)   # break any shared-prefix cache reuse
        rows.append({"case": label, "reference": len(ref.encode(text)), "llama.cpp": len(lc.encode(text)),
                     "ollama": prompt_tokens(text, model)})
    return rows
