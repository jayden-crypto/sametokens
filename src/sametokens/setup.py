"""Recreate the local artifacts a fresh clone needs (all git-ignored):

  models/<name>/   tokenizer + chat-template files from the Hugging Face Hub (no weights)
  third_party/     llama.cpp's converter, at the commit llama-cpp-python bundles
  gguf/<name>.gguf vocab-only GGUFs produced by that converter

so llama.cpp is tested on exactly what a user converting the model would get.
"""

from __future__ import annotations

import json
import subprocess
import sys

from .runtimes import GGUF, MODELS, ROOT

# The llama.cpp commit vendored by llama-cpp-python 0.3.36 (pinned in uv.lock). If you
# upgrade llama-cpp-python, update this so converter and runtime stay in sync.
LLAMA_CPP_COMMIT = "0c1e57098bba43ac29e6e3b677cdceebdd22334f"
TOKENIZER_FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "config.json",
                   "generation_config.json", "chat_template.jinja", "tokenizer.model"]


def download_tokenizers() -> None:
    from huggingface_hub import hf_hub_download, list_repo_files
    for name, spec in json.loads((ROOT / "models.json").read_text()).items():
        available = set(list_repo_files(spec["repo"]))
        for f in TOKENIZER_FILES:
            if f in available and not (MODELS / name / f).exists():
                hf_hub_download(spec["repo"], f, local_dir=MODELS / name)
        print(f"  tokenizer files: {name}")


def fetch_converter() -> None:
    dest = ROOT / "third_party" / "llama.cpp"
    if (dest / "convert_hf_to_gguf.py").exists():
        return
    dest.parent.mkdir(exist_ok=True)

    def git(*args):
        subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    git("remote", "add", "origin", "https://github.com/ggml-org/llama.cpp")
    git("sparse-checkout", "set", "--no-cone", "/convert_hf_to_gguf.py", "/conversion", "/gguf-py")
    git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", LLAMA_CPP_COMMIT)
    git("checkout", "-q", "FETCH_HEAD")
    print(f"  llama.cpp converter @ {LLAMA_CPP_COMMIT[:9]}")


def convert_all() -> None:
    GGUF.mkdir(exist_ok=True)
    converter = ROOT / "third_party" / "llama.cpp" / "convert_hf_to_gguf.py"
    for name in json.loads((ROOT / "models.json").read_text()):
        out = GGUF / f"{name}.gguf"
        if out.exists():
            continue
        proc = subprocess.run([sys.executable, str(converter), str(MODELS / name), "--vocab-only",
                               "--outfile", str(out)], capture_output=True, text=True)
        if proc.returncode:
            raise RuntimeError(f"conversion failed for {name}:\n{proc.stderr[-2000:]}")
        print(f"  gguf: {name} ({out.stat().st_size // 1024} KB)")


def setup() -> None:
    print("downloading tokenizer files...")
    download_tokenizers()
    print("fetching llama.cpp converter...")
    fetch_converter()
    print("converting to vocab-only GGUF...")
    convert_all()
    if not (ROOT / "js" / "node_modules").exists():
        print("installing transformers.js...")
        subprocess.run(["npm", "install", "--silent"], cwd=ROOT / "js", check=True)
    print("ready.")
