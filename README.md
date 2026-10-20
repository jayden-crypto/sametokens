# sametokens

**Do local LLM runtimes feed the model the same tokens it was trained on?** sametokens fuzzes tokenizers across runtimes (llama.cpp, Ollama, transformers.js) against each model creator's reference tokenizer, for 9 of the most-used open models. It shrinks every disagreement to a minimal input, traces each one to a root cause, and measures how much it changes the model's actual predictions.

## Results

27,000 fuzzed strings per runtime (9 models × 3,000), plus 144 chat-template renders:

| Model | llama.cpp | transformers.js |
|---|---|---|
| Qwen2.5 / Qwen3 / DeepSeek-R1-Distill | 7.0–7.2% of strings differ | 0 |
| Mistral v0.3 | 31.5% (mostly reference ambiguity, see below) | 0 |
| Phi-4-mini | 17.4% | 0.2% |
| GPT-OSS | 3.8% | 0 |
| Gemma 3 | 3.6% (intentional) | 0 |
| Llama 3.2, SmolLM3 | 0 | 0 |

**New issues found** (drafts in [`reports/`](reports)):

1. **llama.cpp skips Qwen's NFC normalizer.** Text with decomposed accents is tokenized into base letters and combining marks: Vietnamese 13 → 46 tokens. **Ollama is affected too**: its token counts equal llama.cpp's on all 11 test inputs (`sametokens ollama`).
2. **llama.cpp turns Qwen's plain-text `</s>` into an end-of-generation control token.** A `"</s>"` check added for PaddleOCR in February 2026 (#18825) fires on every Qwen2-family vocab. HTML like `<s>old</s>` in a prompt becomes an EOG token; Ollama is affected too.
3. **llama.cpp drops `rstrip` on Phi-4's role tokens**, because its heuristic only matches models named "phi-3". Any user message starting with a newline, such as pasted text, gets an extra token.
4. **transformers.js strips U+FEFF after `rstrip` tokens**, including Phi-4's `<|user|>` and `<|assistant|>`. It uses `trimStart()`, whose whitespace set is broader than Rust's `is_whitespace`.

**Known issue, newly quantified:** llama.cpp's GPT-4o pre-tokenizer splits Indic vowel signs from their letters ([#27783](https://github.com/ggml-org/llama.cpp/issues/27783)). For GPT-OSS and Phi-4: Hindi 14 → 25 tokens, Tamil 13 → 28, Bengali 11 → 16, Thai 12 → 15, against English identical.

**Does it matter? Yes: the model's answers change.** I asked Qwen2.5-3B-Instruct (the exact GGUF Ollama serves) to translate 16 sentences in 9 languages, written with decomposed accents. Each prompt was built with Qwen's real chat template, then tokenized once by the reference and once by llama.cpp:
- the **greedy reply changed in 15 of 16**, and the first reply token in 11 of 16
- by my reading, **at least 7 replies became clearly wrong**:
  - *"Tôi muốn đặt một bàn cho hai người vào tối nay"* went from **"I want to reserve a table for two people…"** to **"To enter the room without knocking is rude to people."**
  - *"Xin chào thế giới…"* went from "Hello world, are you well today?" to "Hello morning, did you eat today?"
  - Spanish input was reported as "a mix of P[ortuguese]…"
- others are harmless rewordings

Same weights, same text: only the tokenizer differs. The full side-by-side table is in [`REPORT.md`](REPORT.md).

**Things that hold up.** Llama 3.2 and SmolLM3 match everywhere. transformers.js matches the reference on 26,993 of 27,000 strings. Its JavaScript Jinja engine renders all 144 chat prompts identically to Python's jinja2, including GPT-OSS's Harmony template and Llama 3.2's date-dependent one.

## The hard part: what counts as "correct"?

A tokenizer mismatch is only a bug if you know which side matches **training**. sametokens takes the model creator's `tokenizer.json` as the reference, and checks SentencePiece models against their original `tokenizer.model` too. That turned out to matter.

**Mistral v0.3.** In Hugging Face's `tokenizer.json`, `" leading"` → `▁leading`, while the original SentencePiece model and llama.cpp give `▁ ▁leading`. So llama.cpp is *right* and the `tokenizer.json` is the outlier. Those 325 hits are reported as "not a runtime bug", not blamed on llama.cpp. Mistral's text-after-special-token cases are marked *reference-ambiguous* (related to llama.cpp #23840), not new bugs.

**Qwen.** The NFC finding stands because Qwen's own Python tokenizer NFC-normalizes before BPE, so normalized text is what the model was trained on.

**Gemma 3.** `<image_soft_token>` not being parsed from text is likely intentional (images are inserted by the runtime), so it isn't reported.

## How it works

- **Runtimes** ([`runtimes.py`](src/sametokens/runtimes.py)):
  - **Hugging Face `tokenizers`** (the reference)
  - **llama.cpp** via `llama-cpp-python`, built from llama.cpp at the commit it bundles (one day old at test time), loading vocab-only GGUFs made by llama.cpp's own `convert_hf_to_gguf.py`
  - **transformers.js** via a persistent Node process
  - **Ollama** via `prompt_eval_count`, because it no longer exposes token IDs
- **Inputs** ([`gen.py`](src/sametokens/gen.py)) are short strings assembled from known trouble spots:
  - whitespace runs, `\r\n`, NBSP, BOM, zero-width characters
  - digit groups and non-ASCII digits
  - contractions with curly apostrophes
  - NFC/NFD/NFKC pairs, emoji ZWJ sequences, flags and skin tones
  - right-to-left and Indic scripts
  - every special token of the model, glued to all of the above
- **Shrinking** ([`fuzz.py`](src/sametokens/fuzz.py)): delta debugging over code points down to the minimal disagreeing string, then labelled (not-NFC, special-token, leading-space…). Up to 3 distinct minimal examples are kept per label, so one label can't hide a second bug, and the report assigns a root cause to every example.
- **Impact** ([`impact.py`](src/sametokens/impact.py)) runs the real model through llama.cpp on both token sequences. It compares the distribution of the first reply token, then generates the reply greedily under each.
- **Ollama** ([`ollama.py`](src/sametokens/ollama.py)) compares `prompt_eval_count` against the reference and llama.cpp. It sends an unrelated prompt before each measurement so Ollama's prefix cache can't shrink the count.
- **Root-causing** went into llama.cpp's `llama-vocab.cpp` at the bundled commit:
  - the EOG list
  - the "set attributes by model name" heuristics
  - the BPE path with no NFC step

## Quick start

```bash
uv sync
uv run sametokens setup                 # tokenizer files (no weights, ~140 MB), llama.cpp converter, GGUFs, npm install
uv run sametokens fuzz --cases 3000     # ≈1 min for 9 models x 2 runtimes
uv run sametokens templates             # chat templates, Python vs JavaScript Jinja
uv run sametokens impact                # needs `ollama pull qwen2.5:3b` (uses its GGUF directly)
uv run sametokens ollama                # needs a running Ollama with qwen2.5:3b
uv run sametokens report                # REPORT.md
uv run pytest                           # 11 tests, incl. one pinned test per bug
```

## Limitations

- Ollama exposes only token *counts*, so equal counts don't prove equal tokens. Here every count matched llama.cpp's exactly, consistent with Ollama using llama.cpp's tokenizer for this model.
- "Clearly wrong" in the impact section is my reading of 16 replies. The machine-checked numbers are "reply changed" and "first token changed".
- The reference is the model creator's tokenizer as published. For SentencePiece models it's cross-checked against `tokenizer.model`. Where those disagree, as with Mistral, no runtime is blamed.

Versions: llama.cpp 0c1e570 (llama-cpp-python 0.3.36), transformers.js 4.3.0, tokenizers 0.23.2, transformers 5.18.0, Ollama 0.33.0.
