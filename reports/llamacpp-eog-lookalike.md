<!-- file at https://github.com/ggml-org/llama.cpp/issues/new (Eval bug) -->
# Eval bug: `</s>` in the EOG list (added for PaddleOCR) turns Qwen2's plain-text `</s>` token into a control/EOG token

### Name and Version
llama.cpp 0c1e570 (Oct 1 2026). Also observed in Ollama 0.33.0 (`qwen2.5:3b`).

### Problem description
#18825 (PaddleOCR-VL support, commit 237958db3, Feb 2026) added `t.first == "</s>"` to the end-of-generation token list in `llama_vocab::impl::load`. In the Qwen2 vocabulary `</s>` (id 128247) is an ordinary BPE token, not an EOS. At load llama.cpp now logs:

```
load: control-looking token: 128247 '</s>' was not control-type; this is probably a bug in the model. its type will be overridden
print_info: EOG token             = 128247 '</s>'
```

Consequences for every Qwen2/2.5/3 and DeepSeek-R1-Distill-Qwen GGUF:
- User text containing `</s>` (HTML strikethrough `<s>…</s>`, XML) is tokenized as a single control token, while HF tokenizes it as `</`, `s`, `>`. `Hello </s> world` is 5 tokens with HF and 4 in llama.cpp and Ollama.
- Token 128247 is treated as end-of-generation.

### Steps to reproduce
```python
from llama_cpp import Llama
lc = Llama(model_path="qwen2.5-vocab.gguf", vocab_only=True, verbose=False)   # from convert_hf_to_gguf.py --vocab-only
print(lc.tokenize(b"</s>", add_bos=False, special=True))   # [128247]   HF: [522, 82, 29]
```

### Suggested fix
Apply the `</s>` EOG override only to the architecture that needs it (PaddleOCR), or only when `</s>` is the vocab's declared EOS/added token, rather than to any vocab containing that string.
