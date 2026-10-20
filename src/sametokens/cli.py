"""sametokens: do LLM runtimes tokenize your prompt the way the model was trained?

    sametokens setup                      download tokenizers, build vocab-only GGUFs, npm install
    sametokens fuzz --cases 3000          differential token fuzzing, all models x runtimes
    sametokens templates                  chat-template rendering: Python Jinja2 vs transformers.js
    sametokens impact                     effect of the NFC mismatch on Qwen2.5-3B (needs Ollama's qwen2.5:3b)
    sametokens ollama                     token counts from a running Ollama (qwen2.5:3b) vs the reference
    sametokens report                     results/ -> REPORT.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RESULTS = Path("results")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="sametokens", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fuzz")
    f.add_argument("--cases", type=int, default=3000)
    f.add_argument("--models", nargs="*")
    f.add_argument("--runtimes", nargs="*", default=["llama.cpp", "transformers.js"])
    f.add_argument("--seed", type=int, default=0)
    sub.add_parser("setup")
    sub.add_parser("ollama")
    sub.add_parser("templates")
    sub.add_parser("impact")
    sub.add_parser("report")
    args = p.parse_args(argv)
    RESULTS.mkdir(exist_ok=True)

    if args.cmd == "setup":
        from .setup import setup
        setup()
    elif args.cmd == "ollama":
        from .ollama import run_ollama
        rows = run_ollama()
        (RESULTS / "ollama.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        for r in rows:
            print(f"{r['reference']:3} vs {r['ollama']:3}  {r['case']}")
    elif args.cmd == "fuzz":
        from .fuzz import run_all
        from .runtimes import MODEL_NAMES
        run_all(args.models or MODEL_NAMES, args.runtimes, args.cases, RESULTS, args.seed)
    elif args.cmd == "templates":
        from .runtimes import MODEL_NAMES
        from .templates import run_templates
        rows = run_templates(MODEL_NAMES)
        (RESULTS / "templates.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        print(f"{sum(r['same'] for r in rows)}/{len(rows)} renders identical")
    elif args.cmd == "impact":
        from .impact import Scorer, nfd_experiment, ollama_gguf
        from .runtimes import LlamaCpp, Reference
        gguf = ollama_gguf()
        rows = nfd_experiment(Scorer(gguf), Reference("qwen2.5"), LlamaCpp("qwen2.5", gguf=gguf))
        (RESULTS / "impact_nfd.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        print(json.dumps(rows[:2], indent=1, ensure_ascii=False))
    else:
        from .report import write_report
        write_report(RESULTS, Path("REPORT.md"))
        print("wrote REPORT.md")


if __name__ == "__main__":
    main()
