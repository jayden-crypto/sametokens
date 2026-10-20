<!-- file at https://github.com/ggml-org/llama.cpp/issues/new?template=... (Eval bug) -->
# Eval bug: Qwen2-family tokenizer ignores the NFC normalizer, so decomposed (NFD) text is tokenized out of distribution

### Name and Version
llama.cpp 0c1e570 (Oct 1 2026), via llama-cpp-python 0.3.36; also reproduced in Ollama 0.33.0 with `qwen2.5:3b`.

### Problem description
Qwen2 / Qwen2.5 / Qwen3 / DeepSeek-R1-Distill-Qwen `tokenizer.json` declares `"normalizer": {"type": "NFC"}`, and Qwen's original Python tokenizer also NFC-normalizes before BPE. llama.cpp doesn't apply it. Text containing decomposed characters (e.g. `e` + U+0301, common in text from macOS file names, some keyboards and copy-paste) gets split into base letters and combining marks, which the model never saw in training.

| Text (NFD form) | HF tokens | llama.cpp tokens | Ollama `prompt_eval_count` |
|---|---|---|---|
| `Tôi muốn đặt một bàn cho hai người vào tối nay.` | 13 | 46 | 46 |
| `Crème brûlée à la française, très appréciée.` | 13 | 27 | 27 |
| `Å` (A + U+030A) | 1 (`Ãħ`) | 3 (`A`,`Ì`,`Ĭ`) | – |

### Impact (Qwen2.5-3B-Instruct, the GGUF Ollama serves)
I asked the model to translate 16 sentences written with decomposed accents, wrapped in Qwen's chat template, once with HF's tokens and once with llama.cpp's. The greedy reply changed in 15 of 16, and several became wrong. For example, "Tôi muốn đặt một bàn cho hai người vào tối nay." is translated as "I want to reserve a table for two people…" with HF tokens, but as "To enter the room without knocking is rude to people." with llama.cpp's.

### Steps to reproduce
```python
import unicodedata
from transformers import AutoTokenizer
from llama_cpp import Llama
# python convert_hf_to_gguf.py <Qwen/Qwen2.5-3B-Instruct snapshot> --vocab-only --outfile qwen2.5-vocab.gguf
hf = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
lc = Llama(model_path="qwen2.5-vocab.gguf", vocab_only=True, verbose=False)
s = unicodedata.normalize("NFD", "Tôi muốn đặt một bàn cho hai người vào tối nay.")
print(len(hf.encode(s, add_special_tokens=False)), len(lc.tokenize(s.encode(), add_bos=False, special=True)))  # 13 46
```

### Suggested fix
Store the normalizer type in GGUF at conversion (e.g. `tokenizer.ggml.normalizer = "nfc"`) and apply NFC in the BPE path before pre-tokenization (`unicode_cpts_normalize_nfc` alongside the existing NFD helper).

---
Found with differential tokenizer fuzzing (HF tokenizers vs llama.cpp vs transformers.js) and minimised automatically.
