"""Unit tests for the fuzzer, plus regression tests pinning every confirmed finding.

If a pinned test starts failing after upgrading llama.cpp / transformers.js,
the bug was probably fixed upstream: update the report status.
"""

import unicodedata

import pytest

from sametokens.fuzz import label, shrink
from sametokens.runtimes import LlamaCpp, Reference, TransformersJS


def test_shrink_finds_minimal_failing_substring():
    fails = lambda s: "ab" in s  # noqa: E731
    assert shrink("xxxxaxxbxxabyyyy", fails) == "ab"


def test_label_spots_normalisation_and_specials():
    assert "not-NFC" in label("é", [])
    assert "special-token" in label("<|im_start|>x", ["<|im_start|>"])
    assert "leading-space" in label(" x", [])


@pytest.fixture(scope="module")
def tok():
    cache = {}

    def get(kind, model):
        key = (kind, model)
        if key not in cache:
            cache[key] = {"ref": Reference, "llama.cpp": LlamaCpp, "js": TransformersJS}[kind](model)
        return cache[key]
    return get


@pytest.mark.parametrize("model", ["qwen2.5", "llama3.2", "gemma3", "gpt-oss"])
def test_plain_english_agrees_everywhere(tok, model):
    s = "The quick brown fox jumps over the lazy dog. 12345"
    assert tok("llama.cpp", model).encode(s) == tok("ref", model).encode(s)
    assert tok("js", model).encode(s) == tok("ref", model).encode(s)


# --------------------------------------------------------------- pinned bugs
def test_llamacpp_qwen2_skips_nfc_normalisation(tok):
    s = unicodedata.normalize("NFD", "Tôi muốn đặt một bàn")
    ref, got = tok("ref", "qwen2.5").encode(s), tok("llama.cpp", "qwen2.5").encode(s)
    assert len(got) > 2 * len(ref)


def test_llamacpp_promotes_plain_eos_lookalike_to_control(tok):
    assert len(tok("ref", "qwen2.5").encode("</s>")) == 3
    assert len(tok("llama.cpp", "qwen2.5").encode("</s>")) == 1


def test_llamacpp_ignores_rstrip_on_phi4_role_tokens(tok):
    s = "<|user|>\nWhat is 2+2?<|end|>"
    assert tok("llama.cpp", "phi4-mini").encode(s) != tok("ref", "phi4-mini").encode(s)


def test_transformersjs_rstrip_treats_bom_as_whitespace(tok):
    s = "<|tag|>﻿"
    assert tok("js", "phi4-mini").encode(s) != tok("ref", "phi4-mini").encode(s)


def test_llamacpp_gpt4o_pretokenizer_splits_indic_marks(tok):  # known: ggml-org/llama.cpp#27783
    s = "नमस्ते दुनिया"
    assert tok("llama.cpp", "gpt-oss").encode(s) != tok("ref", "gpt-oss").encode(s)
