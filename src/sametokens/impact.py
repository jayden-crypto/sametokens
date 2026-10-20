"""How much does a tokenization mismatch change what the model does?

Loads a real model (Qwen2.5-3B-Instruct, the GGUF Ollama ships) and, for each
test prompt, feeds it twice: once with the reference token ids the model was
trained on, once with the ids the runtime produced. We measure

  * KL(ref || runtime) of the next-token distribution after the prompt,
  * whether the greedy (top-1) next token changes,
  * how much more "surprised" the model is by the text (log-loss per byte).

Same model weights, same text, only the tokenization differs, so any change in
behaviour is caused purely by the tokenizer. `nfd_experiment` goes one step further and
lets the model answer: does its actual reply change?
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

import numpy as np

OLLAMA = Path.home() / ".ollama" / "models"


def ollama_gguf(name: str = "qwen2.5", tag: str = "3b") -> Path:
    manifest = json.loads((OLLAMA / "manifests" / "registry.ollama.ai" / "library" / name / tag).read_text())
    digest = next(layer["digest"] for layer in manifest["layers"] if layer["mediaType"].endswith(".model"))
    return OLLAMA / "blobs" / digest.replace(":", "-")


def _log_softmax(x: np.ndarray) -> np.ndarray:
    x = x - x.max(axis=-1, keepdims=True)
    return x - np.log(np.exp(x).sum(axis=-1, keepdims=True))


class Scorer:
    def __init__(self, gguf: Path):
        from llama_cpp import Llama
        self.llm = Llama(model_path=str(gguf), n_ctx=1024, logits_all=True, verbose=False, n_gpu_layers=-1)

    def logprobs(self, ids: list[int]) -> np.ndarray:
        self.llm.reset()
        self.llm.eval(ids)
        return _log_softmax(np.array(self.llm.scores[: len(ids)], dtype=np.float64))

    def greedy(self, ids: list[int], max_tokens: int) -> str:
        out = self.llm.create_completion(prompt=ids, max_tokens=max_tokens, temperature=0.0)
        return out["choices"][0]["text"]

    def compare(self, prefix: list[int], ref: list[int], got: list[int], n_bytes: int) -> dict:
        lp_ref, lp_got = self.logprobs(prefix + ref), self.logprobs(prefix + got)
        nxt_ref, nxt_got = lp_ref[-1], lp_got[-1]
        kl = float(np.sum(np.exp(nxt_ref) * (nxt_ref - nxt_got)))

        def text_nll(lp, ids):  # log-loss of the text tokens given everything before them
            start = len(prefix)
            return -float(sum(lp[i - 1, ids[i - start]] for i in range(start, start + len(ids))))

        return {
            "kl_next_token": kl,
            "top1_changed": int(np.argmax(nxt_ref) != np.argmax(nxt_got)),
            "nll_per_byte_ref": text_nll(lp_ref, ref) / n_bytes,
            "nll_per_byte_runtime": text_nll(lp_got, got) / n_bytes,
        }


# Prompts written in normal (NFC) form; the experiment feeds their NFD form,
# which is what decomposed text from e.g. macOS file names or some keyboards looks like.
NFD_SENTENCES = [
    "Xin chào thế giới, hôm nay bạn khỏe không?",
    "Tôi muốn đặt một bàn cho hai người vào tối nay.",
    "Cảm ơn bạn rất nhiều vì đã giúp đỡ tôi.",
    "Hà Nội là thủ đô của Việt Nam.",
    "Le café était délicieux, mais l'addition était trop élevée.",
    "Où est la gare la plus proche, s'il vous plaît ?",
    "Crème brûlée à la française, très appréciée.",
    "Mañana iré a la estación con mi señora.",
    "¿Dónde está el baño? Necesito ayuda urgente.",
    "Ärger über die Größe der Bücher in München.",
    "Die Brücke über den Fluss ist für Fußgänger gesperrt.",
    "São Paulo é a maior cidade do Brasil, não é?",
    "Příliš žluťoučký kůň úpěl ďábelské ódy.",
    "Zażółć gęślą jaźń, proszę bardzo.",
    "Çok güzel bir gün, değil mi?",
    "Ångström och smörgåsbord är svenska ord.",
]


def nfd_experiment(scorer: Scorer, ref_tok, runtime, max_tokens: int = 24) -> list[dict]:
    """Each sentence (in NFD form) inside Qwen's real chat template, tokenized by the reference
    (which NFC-normalises) and by the runtime. Compare the model's *reply*: the distribution of
    its first token, and its greedy answer."""
    rows = []
    for s in NFD_SENTENCES:
        text = unicodedata.normalize("NFD", s)
        prompt = ref_tok.tok.apply_chat_template(
            [{"role": "user", "content": f"Translate to English: {text}"}],
            tokenize=False, add_generation_prompt=True)
        ref, got = ref_tok.encode(prompt), runtime.encode(prompt)
        lp_ref, lp_got = scorer.logprobs(ref)[-1], scorer.logprobs(got)[-1]
        reply_ref, reply_got = scorer.greedy(ref, max_tokens), scorer.greedy(got, max_tokens)
        rows.append({
            "text": s, "ref_tokens": len(ref), "runtime_tokens": len(got),
            "kl_first_reply_token": float(np.sum(np.exp(lp_ref) * (lp_ref - lp_got))),
            "top1_changed": int(np.argmax(lp_ref) != np.argmax(lp_got)),
            "reply_changed": int(reply_ref != reply_got),
            "reply_reference": reply_ref, "reply_runtime": reply_got,
        })
    return rows
