"""Tokenizer runtimes under test.

reference      Hugging Face `tokenizers` (Rust) via transformers, loaded from the
               model creator's tokenizer.json: the behaviour the model was trained with.
llama.cpp      llama-cpp-python (bundled llama.cpp), loading a vocab-only GGUF made by
               llama.cpp's own convert_hf_to_gguf.py from the same tokenizer files.
transformers.js  Hugging Face's JavaScript port (@huggingface/tokenizers), via Node.

Each runtime maps text -> token ids without adding BOS/EOS, and parses special
tokens written in the text (e.g. "<|im_start|>"), which is what chat prompts need.
"""

from __future__ import annotations

import json
import subprocess
from functools import cached_property
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"
GGUF = ROOT / "gguf"
MODEL_NAMES = list(json.loads((ROOT / "models.json").read_text()))


class Reference:
    name = "reference"

    def __init__(self, model: str):
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(MODELS / model)

    def encode(self, text: str) -> list[int]:
        return self.tok.encode(text, add_special_tokens=False)

    def decode(self, ids: list[int]) -> str:
        return self.tok.decode(ids)

    def piece(self, i: int) -> str:
        return self.tok.convert_ids_to_tokens(i)

    @cached_property
    def special_tokens(self) -> list[str]:
        return sorted({t.content for t in self.tok.added_tokens_decoder.values() if t.special})


class LlamaCpp:
    name = "llama.cpp"

    def __init__(self, model: str, gguf: Path | None = None):
        from llama_cpp import Llama
        self.llm = Llama(model_path=str(gguf or GGUF / f"{model}.gguf"), vocab_only=True, verbose=False)

    def encode(self, text: str) -> list[int]:
        return self.llm.tokenize(text.encode("utf-8"), add_bos=False, special=True)


class TransformersJS:
    """One Node process shared by all models; requests are answered in order."""

    name = "transformers.js"
    _proc: subprocess.Popen | None = None
    _next_id = 0

    def __init__(self, model: str):
        self.model = model
        if TransformersJS._proc is None or TransformersJS._proc.poll() is not None:
            TransformersJS._proc = subprocess.Popen(
                ["node", str(ROOT / "js" / "server.mjs"), str(MODELS) + "/"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1, cwd=ROOT / "js")

    def _call(self, payload: dict):
        TransformersJS._next_id += 1
        payload = {"id": TransformersJS._next_id, "model": self.model, **payload}
        proc = TransformersJS._proc
        proc.stdin.write(json.dumps(payload) + "\n")
        proc.stdin.flush()
        reply = json.loads(proc.stdout.readline())
        if not reply["ok"]:
            raise RuntimeError(reply["error"])
        return reply["result"]

    def encode(self, text: str) -> list[int]:
        return [int(i) for i in self._call({"op": "encode", "text": text})]

    def template(self, messages: list[dict], add_generation_prompt: bool = True, **kwargs) -> str:
        return self._call({"op": "template", "messages": messages,
                           "add_generation_prompt": add_generation_prompt, "kwargs": kwargs})


RUNTIMES = {"llama.cpp": LlamaCpp, "transformers.js": TransformersJS}
