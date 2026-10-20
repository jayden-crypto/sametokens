<!-- file at https://github.com/huggingface/tokenizers.js/issues/new (the tokenizer engine transformers.js 4.x uses) -->
# `AddedToken.rstrip`/`lstrip` use `trimStart()`/`trimEnd()`, which strip U+FEFF; the Rust tokenizer keeps it

### Versions
transformers.js 4.3.0 (@huggingface/tokenizers 0.2.0), compared with HF tokenizers 0.23.2.

### Problem description
For added tokens with `rstrip: true` (e.g. Phi-4-mini's chat role tokens `<|user|>`, `<|assistant|>`, and `<|tag|>`), `encode_text` strips the neighbouring text with `String.prototype.trimStart()` (and `trimEnd()` for `lstrip`). JavaScript's trim set includes U+FEFF (ZERO WIDTH NO-BREAK SPACE / BOM); the Rust implementation strips `char::is_whitespace`, which does not.

```js
const tok = await AutoTokenizer.from_pretrained("microsoft/Phi-4-mini-instruct");
tok.encode("<|tag|>﻿", { add_special_tokens: false });
// JS:   [200028]
// Rust: [200028, 5574]   ("<|tag|>", "ï»¿")
```

### Suggested fix
Strip with an explicit Unicode `White_Space` class (e.g. `/^[\p{White_Space}]+/u`) instead of `trimStart()`/`trimEnd()`, to match Rust's `char::is_whitespace`.
