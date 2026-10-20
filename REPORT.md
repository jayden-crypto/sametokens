# sametokens report

Reference: Hugging Face tokenizers 0.23.2 / transformers 5.18.0. Runtimes: llama.cpp via llama-cpp-python 0.3.36 (llama.cpp 0c1e570, Oct 1 2026), transformers.js 4.3.0. 3,000 fuzzed strings per model x runtime.

## Share of fuzzed strings tokenized differently from the reference

| Model | llama.cpp | transformers.js |
|---|---|---|
| qwen2.5 | 7.2% | 0 |
| qwen3 | 7.2% | 0 |
| llama3.2 | 0 | 0 |
| gemma3 | 3.6% | 0 |
| mistral-v0.3 | 31.5% | 0 |
| phi4-mini | 17.4% | 0.2% |
| deepseek-r1 | 7.0% | 0 |
| gpt-oss | 3.8% | 0 |
| smollm3 | 0 | 0 |

## Minimised findings

| Model | Runtime | Hits | Minimal input | Reference pieces | Runtime pieces | Cause | Status |
|---|---|---|---|---|---|---|---|
| qwen2.5 | llama.cpp | 67 | `'é'` | `Ã©` | `e Ìģ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen2.5 | llama.cpp | 58 | `'Å'` | `Ãħ` | `A Ì Ĭ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen2.5 | llama.cpp | 46 | `'ñ'` | `Ã±` | `n Ì ĥ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen2.5 | llama.cpp | 44 | `'</s>'` | `</ s >` | `</s>` | llama.cpp promotes the plain-text token `</s>` to a control/EOG token | new |
| qwen3 | llama.cpp | 67 | `'é'` | `Ã©` | `e Ìģ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen3 | llama.cpp | 58 | `'Å'` | `Ãħ` | `A Ì Ĭ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen3 | llama.cpp | 46 | `'ñ'` | `Ã±` | `n Ì ĥ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| qwen3 | llama.cpp | 44 | `'</s>'` | `</ s >` | `</s>` | llama.cpp promotes the plain-text token `</s>` to a control/EOG token | new |
| gemma3 | llama.cpp | 109 | `'<image_soft_token>'` | `<image_soft_token>` | `< image _ soft _ token >` | `<image_soft_token>` not parsed as special in text (images are inserted by the runtime) | [likely intentional](https://github.com/ggml-org/llama.cpp/issues/12876) |
| mistral-v0.3 | llama.cpp | 325 | `' '` | `▁` | `▁▁` | Hugging Face tokenizer.json disagrees with the original SentencePiece model (leading spaces); llama.cpp matches SentencePiece | not a runtime bug |
| mistral-v0.3 | llama.cpp | 296 | `'<s>٢'` | `<s> <0xD9> <0xA2>` | `<s> ▁ <0xD9> <0xA2>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 113 | `'<s>1'` | `<s> 1` | `<s> ▁ 1` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 92 | `'<s>2'` | `<s> 2` | `<s> ▁ 2` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 65 | `'<s>ا'` | `<s> ا` | `<s> ▁ ا` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 14 | `'[control_8]🏽'` | `[control_8] 🏽` | `[control_8] ▁ 🏽` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 10 | `'[control_8]\ufeff'` | `[control_8] ﻿` | `[control_8] ▁ ﻿` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 6 | `'<s>\n'` | `<s> <0x0A>` | `<s> ▁ <0x0A>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 4 | `'[control_70]\u200d'` | `[control_70] ‍` | `[control_70] ▁ ‍` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 3 | `'[control_9]̀'` | `[control_9] ̀` | `[control_9] ▁ ̀` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 3 | `'[control_8]\x0b'` | `[control_8] ` | `[control_8] ▁ ` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 2 | `'[control_9]😀'` | `[control_9] 😀` | `[control_9] ▁ 😀` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 2 | `'[INST]\u202e'` | `[INST] <0xE2> <0x80> <0xAE>` | `[INST] ▁ <0xE2> <0x80> <0xAE>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_9]🇳'` | `[control_9] <0xF0> <0x9F> <0x87> <0xB3>` | `[control_9] ▁ <0xF0> <0x9F> <0x87> <0xB3` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'<s>b'` | `<s> b` | `<s> ▁b` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_35]\u200d'` | `[control_35] ‍` | `[control_35] ▁ ‍` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_13]\u202e'` | `[control_13] <0xE2> <0x80> <0xAE>` | `[control_13] ▁ <0xE2> <0x80> <0xAE>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_8]̀'` | `[control_8] ̀` | `[control_8] ▁ ̀` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_8]்'` | `[control_8] ்` | `[control_8] ▁ ்` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[control_8]\u2009'` | `[control_8] <0xE2> <0x80> <0x89>` | `[control_8] ▁ <0xE2> <0x80> <0x89>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[INST]👍'` | `[INST] 👍` | `[INST] ▁ 👍` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'<s>🇳'` | `<s> <0xF0> <0x9F> <0x87> <0xB3>` | `<s> ▁ <0xF0> <0x9F> <0x87> <0xB3>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'<s>👩'` | `<s> <0xF0> <0x9F> <0x91> <0xA9>` | `<s> ▁ <0xF0> <0x9F> <0x91> <0xA9>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| mistral-v0.3 | llama.cpp | 1 | `'[INST]̊'` | `[INST] <0xCC> <0x8A>` | `[INST] ▁ <0xCC> <0x8A>` | SentencePiece dummy prefix after special tokens; HF and SentencePiece-based tooling disagree | [reference ambiguous](https://github.com/ggml-org/llama.cpp/issues/23840) |
| phi4-mini | llama.cpp | 348 | `'<|tag|>\t'` | `<|tag|>` | `<|tag|> ĉ` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 47 | `'மிழ'` | `à®®à®¿à®´` | `à®® à®¿à®´` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | llama.cpp | 37 | `'दी'` | `à¤¦à¥Ģ` | `à¤¦ à¥Ģ` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | llama.cpp | 32 | `'<|end|> '` | `<|end|>` | `<|end|> Ġ` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 18 | `'<|tag|>\n'` | `<|tag|>` | `<|tag|> Ċ` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 11 | `'न्'` | `à¤¨à¥į` | `à¤¨ à¥į` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | llama.cpp | 10 | `'ம்'` | `à®®à¯į` | `à®® à¯į` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | llama.cpp | 9 | `'<|end|>\u2009'` | `<|end|>` | `<|end|> âĢī` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 4 | `'̃<m'` | `Ìĥ <m` | `Ìĥ < m` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | llama.cpp | 4 | `'<|tag|>\x0b'` | `<|tag|>` | `<|tag|> ċ` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 2 | `'<|tag|>\u3000'` | `<|tag|>` | `<|tag|> ãĢĢ` | llama.cpp ignores `rstrip` on Phi-4's special tokens (heuristic only matches 'phi-3') | new |
| phi4-mini | llama.cpp | 1 | `'️<s'` | `ï¸ı <s` | `ï¸ı < s` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| phi4-mini | transformers.js | 3 | `'<|tag|>\ufeff'` | `<|tag|> ï»¿` | `<|tag|>` | transformers.js `rstrip` uses JavaScript's \s (includes U+FEFF), unlike Rust | new |
| phi4-mini | transformers.js | 2 | `'<|assistant|>\ufeff'` | `<|assistant|> ï»¿` | `<|assistant|>` | transformers.js `rstrip` uses JavaScript's \s (includes U+FEFF), unlike Rust | new |
| phi4-mini | transformers.js | 2 | `'<|user|>\ufeff'` | `<|user|> ï»¿` | `<|user|>` | transformers.js `rstrip` uses JavaScript's \s (includes U+FEFF), unlike Rust | new |
| deepseek-r1 | llama.cpp | 63 | `'Å'` | `Ãħ` | `A Ì Ĭ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| deepseek-r1 | llama.cpp | 60 | `'é'` | `Ã©` | `e Ìģ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| deepseek-r1 | llama.cpp | 47 | `'</s>'` | `</ s >` | `</s>` | llama.cpp promotes the plain-text token `</s>` to a control/EOG token | new |
| deepseek-r1 | llama.cpp | 40 | `'ñ'` | `Ã±` | `n Ì ĥ` | llama.cpp skips the NFC normalizer declared in tokenizer.json | new |
| gpt-oss | llama.cpp | 48 | `'மிழ'` | `à®®à®¿à®´` | `à®® à®¿à®´` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| gpt-oss | llama.cpp | 38 | `'दी'` | `à¤¦à¥Ģ` | `à¤¦ à¥Ģ` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| gpt-oss | llama.cpp | 15 | `'ம்'` | `à®®à¯į` | `à®® à¯į` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| gpt-oss | llama.cpp | 10 | `'न्'` | `à¤¨à¥į` | `à¤¨ à¥į` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| gpt-oss | llama.cpp | 2 | `"்'s"` | `à¯į 's` | `à¯į ' s` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |
| gpt-oss | llama.cpp | 1 | `'️<s'` | `ï¸ı <s` | `ï¸ı < s` | GPT-4o/o200k pre-tokenizer regex drops \p{M}: combining marks split from letters (Indic scripts) | [known](https://github.com/ggml-org/llama.cpp/issues/27783) |

## Chat templates: Python jinja2 vs transformers.js (@huggingface/jinja)

144/144 renders identical across 9 models x 8 conversations x add_generation_prompt on/off.

## Impact: Qwen2.5-3B (Ollama's GGUF) translating NFD text, reference vs llama.cpp tokens

Same weights, same prompt text, only the tokenization differs. The greedy reply changed in 15/16 sentences; the first reply token changed in 11/16.

| Sentence | Tokens (ref → llama.cpp) | KL(first reply token) | Reply with reference tokens | Reply with llama.cpp tokens |
|---|---|---|---|---|
| Xin chào thế giới, hôm nay bạn khỏe không? | 45 → 66 | 0.65 | Hello world, are you well today? | Hello morning, did you eat today? |
| Tôi muốn đặt một bàn cho hai người vào tối nay. | 46 → 79 | 3.46 | I want to reserve a table for two people for tonight. | To enter the room without knocking is rude to people.   Note: The orig |
| Cảm ơn bạn rất nhiều vì đã giúp đỡ tôi. | 46 → 75 | 13.14 | Thank you very much for helping me. | Cam on ban raît nhieu viêt giúp tôi.   This is the translation of the  |
| Hà Nội là thủ đô của Việt Nam. | 42 → 61 | 2.12 | Hà Nội is the capital of Vietnam. | Ha Noi is the French name for Hanoi, the capital city of Vietnam. The  |
| Le café était délicieux, mais l'addition était trop élevée. | 50 → 62 | 0.00 | The coffee was delicious, but the bill was too high. | The coffee was delicious, but the bill was too expensive. |
| Où est la gare la plus proche, s'il vous plaît ? | 50 → 53 | 3.11 | Please translate to English: "Where is the nearest train station, plea | "Where is the nearest train station, please?" |
| Crème brûlée à la française, très appréciée. | 46 → 60 | 1.22 | French crème brûlée, very appreciated. | "Creème brûlée à la française, très appréciée." |
| Mañana iré a la estación con mi señora. | 46 → 52 | 12.66 | Tomorrow I will go to the station with my lady.   Note: The term "mi s | The provided text appears to be in a mix of Portuguese and Quechua lan |
| ¿Dónde está el baño? Necesito ayuda urgente. | 48 → 52 | 1.00 | Where is the bathroom? I need urgent help. | The translation of the given Spanish and Portuguese mixed sentence to  |
| Ärger über die Größe der Bücher in München. | 44 → 59 | 0.31 | Anger over the size of books in Munich. | Anger over the size of the books in Munich.   Note: The original text  |
| Die Brücke über den Fluss ist für Fußgänger gesperrt. | 51 → 60 | 0.00 | The bridge over the river is closed for pedestrians. | The bridge over the river is closed for pedestrians. |
| São Paulo é a maior cidade do Brasil, não é? | 45 → 53 | 0.89 | São Paulo is the largest city in Brazil, isn't it? | São Paulo is the largest city in Brazil, isn't it? |
| Příliš žluťoučký kůň úpěl ďábelské ódy. | 61 → 78 | 3.95 | The literal Czech phrase "Příliš žluťoučký kůň úpěl | The translation of the Czech text "Příliš žluťouč |
| Zażółć gęślą jaźń, proszę bardzo. | 49 → 62 | 1.70 | "Zażółć gęślą jaźń" is a Polish phrase, and its English translation is | Here, the text appears to be in Polish with diacritical marks. Transla |
| Çok güzel bir gün, değil mi? | 41 → 53 | 3.42 | "Çok güzel bir gün, değil mi?" translates to "Isn't it a nice day?" in | A very beautiful day, right? |
| Ångström och smörgåsbord är svenska ord. | 48 → 58 | 1.48 | "Ångström och smörgåsbord är svenska ord." translates to:  "Ångström | "Ångström och smörgåsbord are Swedish words."   Note |

## Ollama (qwen2.5:3b) prompt token counts

| Input | Reference | llama.cpp | Ollama |
|---|---|---|---|
| NFC: Xin chào thế giới, hôm nay bạn khỏe không? | 13 | 13 | 13 |
| NFD: Xin chào thế giới, hôm nay bạn khỏe không? | 13 | 34 | 34 |
| NFC: Tôi muốn đặt một bàn cho hai người vào tối nay. | 13 | 13 | 13 |
| NFD: Tôi muốn đặt một bàn cho hai người vào tối nay. | 13 | 46 | 46 |
| NFC: Le café était délicieux, mais l'addition était trop élevée. | 17 | 17 | 17 |
| NFD: Le café était délicieux, mais l'addition était trop élevée. | 17 | 29 | 29 |
| NFC: Où est la gare la plus proche, s'il vous plaît ? | 17 | 17 | 17 |
| NFD: Où est la gare la plus proche, s'il vous plaît ? | 17 | 21 | 21 |
| html strikethrough | 10 | 8 | 8 |
| eos lookalike | 5 | 4 | 4 |
| control | 10 | 10 | 10 |
