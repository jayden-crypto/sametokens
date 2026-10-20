"""results/ -> REPORT.md: mismatch matrix, triaged findings, template check, impact."""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path

# Root causes, established by hand while triaging (see README / reports/).
CAUSES = [
    (lambda f: f["runtime"] == "llama.cpp" and "not-NFC" in f["label"],
     "llama.cpp skips the NFC normalizer declared in tokenizer.json", "new", "llamacpp-qwen2-nfc"),
    (lambda f: f["runtime"] == "llama.cpp" and "</s>" in f["text"],
     "llama.cpp promotes the plain-text token `</s>` to a control/EOG token", "new", "llamacpp-eog-lookalike"),
    (lambda f: f["runtime"] == "llama.cpp" and f["model"] == "phi4-mini" and "special-token" in f["label"],
     "llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3')", "new",
     "llamacpp-phi4-rstrip"),
    (lambda f: f["runtime"] == "transformers.js" and f["model"] == "phi4-mini",
     "transformers.js `rstrip` uses JavaScript's \\s (includes U+FEFF), unlike Rust", "new",
     "transformersjs-rstrip-whitespace"),
    (lambda f: f["runtime"] == "llama.cpp" and f["model"] in ("phi4-mini", "gpt-oss"),
     "GPT-4o/o200k pre-tokenizer regex drops \\p{M}: combining marks split from letters (Indic scripts)",
     "known", "https://github.com/ggml-org/llama.cpp/issues/27783"),
    (lambda f: "deviates from sentencepiece" in f["verdict"],
     "Hugging Face tokenizer.json disagrees with the original SentencePiece model (leading spaces); "
     "llama.cpp matches SentencePiece", "not a runtime bug", ""),
    (lambda f: f["model"] == "mistral-v0.3" and "special-token" in f["label"],
     "SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree",
     "reference ambiguous", "https://github.com/ggml-org/llama.cpp/issues/23840"),
    (lambda f: f["model"] == "gemma3" and "<image_soft_token>" in f["text"],
     "`<image_soft_token>` not parsed as special in text (images are inserted by the runtime)",
     "likely intentional", "https://github.com/ggml-org/llama.cpp/issues/12876"),
]


def explain(f: dict) -> tuple[str, str, str]:
    for match, cause, status, ref in CAUSES:
        if match(f):
            return cause, status, ref
    return "untriaged", "new?", ""


def write_report(results: Path, out: Path) -> None:
    fuzz = json.loads((results / "token_fuzz.json").read_text())
    vers = {k: metadata.version(k) for k in ("tokenizers", "transformers", "llama_cpp_python")}
    js = json.loads((Path(__file__).resolve().parents[2] / "js/node_modules/@huggingface/transformers/package.json")
                    .read_text())["version"]
    models = list(dict.fromkeys(r["model"] for r in fuzz))
    runtimes = list(dict.fromkeys(r["runtime"] for r in fuzz))
    lines = ["# sametokens report", "",
             f"Reference: Hugging Face tokenizers {vers['tokenizers']} / transformers {vers['transformers']}. "
             f"Runtimes: llama.cpp via llama-cpp-python {vers['llama_cpp_python']} (llama.cpp 0c1e570, Oct 1 2026), "
             f"transformers.js {js}. {fuzz[0]['cases']:,} fuzzed strings per model x runtime.", "",
             "## Share of fuzzed strings tokenized differently from the reference", "",
             "| Model | " + " | ".join(runtimes) + " |", "|---|" + "---|" * len(runtimes)]
    for m in models:
        cells = []
        for rt in runtimes:
            r = next(x for x in fuzz if x["model"] == m and x["runtime"] == rt)
            cells.append(f"{100 * r['rate']:.1f}%" if r["rate"] else "0")
        lines.append(f"| {m} | " + " | ".join(cells) + " |")

    lines += ["", "## Minimised findings", "",
              "| Model | Runtime | Hits | Minimal input | Reference pieces | Runtime pieces | Cause | Status |",
              "|---|---|---|---|---|---|---|---|"]
    for r in fuzz:
        for f in r["findings"]:
            cause, status, ref = explain(f)
            status = f"[{status}]({ref})" if ref.startswith("http") else status
            lines.append(f"| {f['model']} | {f['runtime']} | {f['hits']} | `{f['text']!r}` | "
                         f"`{' '.join(f['reference_pieces'])[:40]}` | `{' '.join(f['got_pieces'])[:40]}` | "
                         f"{cause} | {status} |")

    tpl = results / "templates.json"
    if tpl.exists():
        rows = json.loads(tpl.read_text())
        lines += ["", "## Chat templates: Python jinja2 vs transformers.js (@huggingface/jinja)", "",
                  f"{sum(r['same'] for r in rows)}/{len(rows)} renders identical across "
                  f"{len({r['model'] for r in rows})} models x {len({r['conversation'] for r in rows})} conversations "
                  "x add_generation_prompt on/off."]
    imp = results / "impact_nfd.json"
    if imp.exists():
        rows = json.loads(imp.read_text())
        changed = sum(r["reply_changed"] for r in rows)
        lines += ["", "## Impact: Qwen2.5-3B (Ollama's GGUF) translating NFD text, reference vs llama.cpp tokens", "",
                  f"Same weights, same prompt text, only the tokenization differs. The greedy reply changed in "
                  f"{changed}/{len(rows)} sentences; the first reply token changed in "
                  f"{sum(r['top1_changed'] for r in rows)}/{len(rows)}.", "",
                  "| Sentence | Tokens (ref → llama.cpp) | KL(first reply token) | Reply with reference tokens "
                  "| Reply with llama.cpp tokens |", "|---|---|---|---|---|"]
        for r in rows:
            def cell(t):
                return t.strip().replace("\n", " ").replace("|", "\\|")[:70]
            lines.append(f"| {r['text']} | {r['ref_tokens']} → {r['runtime_tokens']} | {r['kl_first_reply_token']:.2f} "
                         f"| {cell(r['reply_reference'])} | {cell(r['reply_runtime'])} |")
    oll = results / "ollama.json"
    if oll.exists():
        rows = json.loads(oll.read_text())
        lines += ["", "## Ollama (qwen2.5:3b) prompt token counts", "",
                  "| Input | Reference | llama.cpp | Ollama |", "|---|---|---|---|"]
        lines += [f"| {r['case']} | {r['reference']} | {r['llama.cpp']} | {r['ollama']} |" for r in rows]
    out.write_text("\n".join(lines) + "\n")
