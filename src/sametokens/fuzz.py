"""Differential tokenizer fuzzing: runtime(text) must equal reference(text).

Every mismatch is shrunk (delta debugging over code points) to the smallest
string that still disagrees, labelled with the trouble spots it contains, and
de-duplicated per (model, runtime, label). For SentencePiece models we also ask
the original `tokenizer.model`: if it sides with the runtime, the mismatch is a
Hugging Face `tokenizer.json` quirk, not a runtime bug.
"""

from __future__ import annotations

import json
import random
import time
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from .gen import DIGITS, StringGen
from .runtimes import MODELS, RUNTIMES, Reference


@dataclass
class Finding:
    model: str
    runtime: str
    label: str
    text: str
    reference: list[int]
    got: list[int]
    reference_pieces: list[str]
    got_pieces: list[str]
    sentencepiece: list[int] | None
    verdict: str          # "runtime bug" | "tokenizer.json deviates from sentencepiece" | "runtime error"
    original: str
    hits: int = 1


def shrink(text: str, fails) -> str:
    """ddmin over code points: drop chunks, halving the chunk size, until nothing more can go."""
    chars = list(text)
    n = 2
    while len(chars) >= 2:
        chunk = max(1, len(chars) // n)
        removed = False
        for start in range(0, len(chars), chunk):
            cand = chars[:start] + chars[start + chunk:]
            if cand and fails("".join(cand)):
                chars, n, removed = cand, max(n - 1, 2), True
                break
        if not removed:
            if chunk == 1:
                break
            n = min(len(chars), n * 2)
    return "".join(chars)


def label(text: str, specials: list[str]) -> str:
    tags = []
    if any(t in text for t in specials):
        tags.append("special-token")
    if unicodedata.normalize("NFC", text) != text:
        tags.append("not-NFC")
    if any(unicodedata.combining(c) for c in text):
        tags.append("combining-mark")
    if text[:1].isspace():
        tags.append("leading-space")
    if any(c in text for c in " 　 ​﻿\x0b\x0c"):
        tags.append("unusual-whitespace")
    if any(c in text for c in "‌‍‎‏‮­"):
        tags.append("zero-width/bidi")
    if any(ord(c) > 0x1F000 for c in text):
        tags.append("emoji")
    if any(d in text for d in DIGITS) or any(c.isdigit() for c in text):
        tags.append("digits")
    if "  " in text or "\n\n" in text:
        tags.append("whitespace-run")
    if not tags:
        tags.append("other")
    return "+".join(tags)


class Fuzzer:
    def __init__(self, model: str, runtime: str, seed: int = 0):
        self.model = model
        self.ref = Reference(model)
        self.rt = RUNTIMES[runtime](model)
        self.runtime = runtime
        self.gen = StringGen(random.Random(seed), self.ref.special_tokens)
        sp_path = MODELS / model / "tokenizer.model"
        self.sp = None
        if sp_path.exists():
            import sentencepiece as spm
            self.sp = spm.SentencePieceProcessor(model_file=str(sp_path))

    def disagrees(self, text: str) -> bool:
        try:
            return self.rt.encode(text) != self.ref.encode(text)
        except Exception:
            return True

    def finding(self, original: str) -> Finding:
        text = shrink(original, self.disagrees)
        ref = self.ref.encode(text)
        try:
            got, verdict = self.rt.encode(text), "runtime bug"
        except Exception as e:
            got, verdict = [], f"runtime error: {e}"[:200]
        sp_ids = None
        if self.sp is not None and not any(t in text for t in self.ref.special_tokens):
            sp_ids = self.sp.encode(text)
            if sp_ids == got and got != ref:
                verdict = "tokenizer.json deviates from sentencepiece"
        piece = self.ref.piece
        return Finding(self.model, self.runtime, label(text, self.ref.special_tokens), text, ref, got,
                       [piece(i) for i in ref], [piece(i) if 0 <= i < len(self.ref.tok) else "?" for i in got],
                       sp_ids, verdict, original)

    def run(self, n: int, per_label: int = 3) -> tuple[int, list[Finding]]:
        """Fuzz n strings. Keeps up to `per_label` distinct minimal examples per label, so one
        label can't hide a second, different bug that happens to share it."""
        found: dict[str, list[Finding]] = {}
        mismatches = 0
        for _ in range(n):
            text = self.gen.text()
            if not self.disagrees(text):
                continue
            mismatches += 1
            f = self.finding(text)
            examples = found.setdefault(f"{f.label}|{f.verdict[:13]}", [])
            same = next((e for e in examples if e.text == f.text), None)
            if same:
                same.hits += 1
            elif len(examples) < per_label:
                examples.append(f)
            else:  # keep the shortest examples
                examples.sort(key=lambda e: len(e.text))
                examples[-1].hits += 1
                if len(f.text) < len(examples[-1].text):
                    f.hits = examples[-1].hits
                    examples[-1] = f
        return mismatches, [f for examples in found.values() for f in examples]


def run_all(models: list[str], runtimes: list[str], n: int, out: Path, seed: int = 0) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for model in models:
        for runtime in runtimes:
            t = time.time()
            fz = Fuzzer(model, runtime, seed)
            mismatches, found = fz.run(n)
            rec = {"model": model, "runtime": runtime, "cases": n, "mismatching_cases": mismatches,
                   "rate": mismatches / n, "distinct": len(found), "seconds": round(time.time() - t, 1),
                   "findings": [asdict(f) for f in sorted(found, key=lambda f: -f.hits)]}
            summary.append(rec)
            print(f"{model:14} {runtime:16} {mismatches:5}/{n} mismatching ({100 * mismatches / n:5.1f}%), "
                  f"{len(found)} distinct  [{rec['seconds']}s]", flush=True)
    (out / "token_fuzz.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    return summary
