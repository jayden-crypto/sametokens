"""Fuzz inputs aimed at the places tokenizers historically disagree.

Strings are built from fragments drawn from pools of known trouble spots
(whitespace runs, digit groups, contractions, Unicode normalisation forms,
emoji sequences, right-to-left scripts, special tokens glued to text...) and
joined with random separators. Small, dense strings find bugs fastest and
shrink to readable reproducers.
"""

from __future__ import annotations

import random

WHITESPACE = [" ", "  ", "   ", "\t", "\n", "\n\n", "\n\n\n", "\r\n", " \n", "\n ", " ", "　",
              " ", "​", "﻿", " \t ", "\x0b", "\x0c"]
DIGITS = ["1", "12", "123", "1234", "12345", "1234567", "3.14159", "1,000,000", "0.5", "-42", "1e10",
          "２０２６", "١٢٣", "½", "²"]
WORDS = ["hello", "Hello", "HELLO", "world", "the", "The", "tokenizer", "don't", "I'm", "we'll",
         "'s", "'LL", "’s", "can’t", "x", "a", "Z", "naïve", "über", "Straße", "İstanbul", "ǅ"]
CODE = ["def f(x):", "    return", "\treturn x", "{\"a\": 1}", "</s>", "<s>", "[INST]", "<b>", "&amp;",
        "if (a&&b) {", "x == y", "->", "=>", "::", "#!/bin/sh", "/* */", "`code`", "```", "____", "====", "...."]
UNICODE = [
    "é", "é", "ñ", "ñ", "Å", "Å", "ﬁ", "Ⅻ", "①",          # NFC/NFD/NFKC pairs
    "😀", "👩‍👩‍👧", "👍🏽", "🇮🇳", "🏳️‍🌈", "❤️", "1️⃣",       # emoji sequences
    "日本語", "中文", "한국어", "ภาษาไทย", "हिन्दी", "தமிழ்", "مرحبا", "שלום",   # scripts
    "‎", "‏", "‮", "‌", "‍", "­", "̀",        # bidi/zero-width/combining
    "Ω", "Ω", "µ", "μ", "ı", "ﬀ", "ǈ", "𝔘𝔫𝔦𝔠𝔬𝔡𝔢", "\U0001f9ec",
]
REPEATS = ["a" * 40, "ab" * 25, " " * 17, "\n" * 9, "!" * 13, "." * 33, "😀" * 6, "-" * 64]
SEPARATORS = ["", " ", "", "\n", "  ", "\t"]


class StringGen:
    def __init__(self, rng: random.Random, special_tokens: list[str]):
        self.rng = rng
        self.special = [t for t in special_tokens if t] or ["<|endoftext|>"]

    def fragment(self) -> str:
        pool = self.rng.choices(
            [WHITESPACE, DIGITS, WORDS, CODE, UNICODE, REPEATS, self.special],
            weights=[3, 2, 3, 2, 4, 1, 2])[0]
        return self.rng.choice(pool)

    def text(self) -> str:
        parts = [self.fragment() for _ in range(self.rng.randint(1, 6))]
        out = parts[0]
        for p in parts[1:]:
            out += self.rng.choice(SEPARATORS) + p
        return out
