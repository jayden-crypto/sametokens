<!-- file at https://github.com/ggml-org/llama.cpp/issues/new (Eval bug) -->
# Eval bug: Phi-4 special tokens lose `rstrip`, so messages starting with whitespace are tokenized differently from HF

### Name and Version
llama.cpp 0c1e570 (Oct 1 2026), via llama-cpp-python 0.3.36.

### Problem description
In `microsoft/Phi-4-mini-instruct`, the role tokens `<|system|>`, `<|user|>`, `<|assistant|>`, `<|end|>` and others are `AddedToken(rstrip=True)`, so HF swallows whitespace after them. llama.cpp sets `LLAMA_TOKEN_ATTR_RSTRIP` only when `general.name` contains `phi-3`/`phi3` (`llama-vocab.cpp`, "set attributes by model/tokenizer/architecture name"), so Phi-4 GGUFs don't get it.

| Input | HF tokens | llama.cpp tokens |
|---|---|---|
| `<|user|>\nWhat is 2+2?<|end|>` | `<|user|> What Ġis …` (9) | `<|user|> Ċ What Ġis …` (10) |
| `<|system|>\n\nYou are helpful.<|end|>` | 6 | 7 |
| chat template, user content `"\n\nSummarise this pasted text:\n..."` | 11 | 12 |

Every system/user message that begins with a space or newline (pasted text, for example) reaches the model as a sequence it never saw in training.

### Suggested fix
Extend the name match to Phi-4 (`phi-4`, `phi4`), or better, have `convert_hf_to_gguf.py` record each added token's `lstrip`/`rstrip` in the GGUF so no name heuristics are needed.
