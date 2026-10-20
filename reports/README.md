# Bug reports (drafts, not yet filed)

| # | Project | Issue | Draft |
|---|---|---|---|
| 1 | `ggml-org/llama.cpp` | Qwen2-family tokenizer skips the NFC normalizer (NFD text → 2–3.5× tokens; also in Ollama) | [llamacpp-qwen2-nfc.md](llamacpp-qwen2-nfc.md) |
| 2 | `ggml-org/llama.cpp` | `</s>` added to the EOG list for PaddleOCR promotes Qwen2's plain-text `</s>` to a control token | [llamacpp-eog-lookalike.md](llamacpp-eog-lookalike.md) |
| 3 | `ggml-org/llama.cpp` | Phi-4 special tokens lose `rstrip` (heuristic matches only "phi-3") | [llamacpp-phi4-rstrip.md](llamacpp-phi4-rstrip.md) |
| 4 | `huggingface/tokenizers.js` | `rstrip`/`lstrip` use `trimStart()`/`trimEnd()`, which strip U+FEFF; Rust doesn't | [transformersjs-rstrip-whitespace.md](transformersjs-rstrip-whitespace.md) |
| – | `ggml-org/llama.cpp#27783` (known) | Data comment: how much the GPT-4o pre-tokenizer's `\p{M}` handling changes Indic tokenization | [comment-27783-indic-measurements.md](comment-27783-indic-measurements.md) |

Search the tracker again right before filing; file from your own account.
