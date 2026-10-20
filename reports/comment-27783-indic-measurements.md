<!-- comment for https://github.com/ggml-org/llama.cpp/issues/27783 (combining-mark discussion) -->
Some numbers on the combining-mark (`\p{M}`) mismatch discussed here and in #28054, in case they help decide whether to follow the reference tokenizer. HF `tokenizers` vs llama.cpp 0c1e570, vocab-only GGUFs from `convert_hf_to_gguf.py`:

| Sentence | gpt-oss-20b HF → llama.cpp | Phi-4-mini HF → llama.cpp |
|---|---|---|
| Hindi `नमस्ते दुनिया, आप कैसे हैं? मैं ठीक हूँ।` | 14 → 25 | 14 → 25 |
| Tamil `வணக்கம் உலகம், நீங்கள் எப்படி இருக்கிறீர்கள்?` | 13 → 28 | 13 → 28 |
| Bengali `হ্যালো বিশ্ব, আপনি কেমন আছেন?` | 11 → 16 | 11 → 16 |
| Thai `สวัสดีชาวโลก คุณสบายดีไหม` | 12 → 15 | 12 → 15 |
| English control sentence | identical | identical |

In random fuzzing about 3.8% of mixed-script strings mismatch for gpt-oss and 17% for Phi-4-mini, the latter mostly because of the separate `rstrip` issue. Every Indic sentence I tried mismatched, so for these scripts the model sees out-of-distribution token sequences on essentially every prompt.
