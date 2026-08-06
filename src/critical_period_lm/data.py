"""Corpus preparation: download TinyStories, fit a BPE tokenizer, encode to token arrays.

Not part of the freeze corpus. What the freeze needs from this module is a manifest: the
digests of the tokenizer and of both token arrays, recorded before the first registered
run so that a later change to the corpus cannot pass unnoticed.

The validation split is the dataset's own held-out file, not a slice carved out of the
training text. It is never subjected to a deficit and never used for a selection decision.

Usage:

    python -m critical_period_lm.data prepare
    python -m critical_period_lm.data prepare --train-mb 50   # quick pipeline check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import requests
from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

BASE_URL = "https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main"
TRAIN_FILE = "TinyStories-train.txt"
VALID_FILE = "TinyStories-valid.txt"

END_OF_STORY = "<|endoftext|>"
DEFAULT_VOCAB_SIZE = 4096

# Fitting BPE on the whole corpus is slow and buys nothing at this vocabulary size, so the
# tokenizer is fit on a prefix. The prefix size is recorded in the manifest.
TOKENIZER_SAMPLE_BYTES = 32 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(name: str, dest: Path, max_bytes: int | None = None) -> Path:
    """Fetch a corpus file, optionally only its first `max_bytes`.

    TinyStories is a shuffled collection of independent short stories, so a prefix is a
    sample rather than a biased excerpt. The prefix is cut at the last complete story so
    that no truncated fragment enters training.
    """
    if dest.exists():
        print(f"{dest.name} already present ({dest.stat().st_size / 1e6:.0f} MB)")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Range": f"bytes=0-{max_bytes - 1}"} if max_bytes else {}
    response = requests.get(f"{BASE_URL}/{name}", headers=headers, stream=True, timeout=120)
    response.raise_for_status()

    written = 0
    partial = dest.with_suffix(dest.suffix + ".partial")
    with partial.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1 << 20):
            handle.write(chunk)
            written += len(chunk)
            print(f"\r  {name}: {written / 1e6:.0f} MB", end="", file=sys.stderr)
    print(file=sys.stderr)

    # Trim the trailing partial story by inspecting only the tail, so that a multi-gigabyte
    # corpus never has to be held in memory to be truncated.
    if max_bytes:
        tail_size = min(1 << 20, written)
        with partial.open("rb") as handle:
            handle.seek(written - tail_size)
            tail = handle.read()
        cut = tail.rfind(END_OF_STORY.encode())
        if cut > 0:
            os.truncate(partial, written - tail_size + cut + len(END_OF_STORY))

    partial.rename(dest)
    return dest


def fit_tokenizer(text_path: Path, vocab_size: int, dest: Path) -> Tokenizer:
    """Byte-level BPE fit on the training text only."""
    sample = text_path.with_name("tokenizer-sample.txt")
    with text_path.open("r", encoding="utf-8") as handle:
        sample.write_text(handle.read(TOKENIZER_SAMPLE_BYTES), encoding="utf-8")

    tokenizer = Tokenizer(models.BPE(unk_token=None))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    tokenizer.train(
        [str(sample)],
        trainers.BpeTrainer(
            vocab_size=vocab_size,
            special_tokens=[END_OF_STORY],
            initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
            show_progress=False,
        ),
    )
    sample.unlink()
    tokenizer.save(str(dest))
    return tokenizer


READ_CHUNK_BYTES = 32 * 1024 * 1024


def encode(tokenizer: Tokenizer, text_path: Path, dest: Path) -> np.ndarray:
    """Encode a corpus file to a flat uint16 array of token ids.

    Streamed by story boundary: the file is read in chunks and a trailing partial story is
    carried into the next chunk, so peak memory stays near the chunk size rather than the
    corpus size. A 2 GB corpus would not fit in memory as a decoded string plus a list of
    per-story arrays, and finding that out during a long run is not the moment to find it.
    """
    eot = tokenizer.token_to_id(END_OF_STORY)
    total_bytes = text_path.stat().st_size
    pieces: list[np.ndarray] = []
    read_bytes = 0

    def flush(stories: list[str]) -> None:
        batch = [s for s in stories if s.strip()]
        if not batch:
            return
        ids = [np.array(e.ids + [eot], dtype=np.uint16) for e in tokenizer.encode_batch(batch)]
        pieces.append(np.concatenate(ids))

    with text_path.open("r", encoding="utf-8") as handle:
        remainder = ""
        while True:
            chunk = handle.read(READ_CHUNK_BYTES)
            if not chunk:
                break
            read_bytes += len(chunk)
            stories = (remainder + chunk).split(END_OF_STORY)
            remainder = stories.pop()
            flush(stories)
            print(f"\r  encoding {read_bytes / 1e6:.0f}/{total_bytes / 1e6:.0f} MB",
                  end="", file=sys.stderr)
        flush([remainder])
    print(file=sys.stderr)

    tokens = np.concatenate(pieces)
    np.save(dest, tokens)
    return tokens


def prepare(train_mb: int, vocab_size: int, data_dir: Path = DATA_DIR) -> dict:
    data_dir.mkdir(parents=True, exist_ok=True)
    train_txt = download(TRAIN_FILE, data_dir / TRAIN_FILE, train_mb * 1024 * 1024)
    valid_txt = download(VALID_FILE, data_dir / VALID_FILE)

    tokenizer_path = data_dir / "tokenizer.json"
    if tokenizer_path.exists():
        tokenizer = Tokenizer.from_file(str(tokenizer_path))
        print("tokenizer already present")
    else:
        print(f"fitting BPE, vocab {vocab_size}")
        tokenizer = fit_tokenizer(train_txt, vocab_size, tokenizer_path)

    train_npy, valid_npy = data_dir / "train.npy", data_dir / "valid.npy"
    train_tokens = (
        np.load(train_npy) if train_npy.exists() else encode(tokenizer, train_txt, train_npy)
    )
    valid_tokens = (
        np.load(valid_npy) if valid_npy.exists() else encode(tokenizer, valid_txt, valid_npy)
    )

    manifest = {
        "vocab_size": tokenizer.get_vocab_size(),
        "tokenizer_sample_bytes": TOKENIZER_SAMPLE_BYTES,
        "train_text_bytes": train_txt.stat().st_size,
        "train_tokens": int(train_tokens.size),
        "valid_tokens": int(valid_tokens.size),
        "tokenizer_sha256": sha256_file(tokenizer_path),
        "train_sha256": sha256_file(train_npy),
        "valid_sha256": sha256_file(valid_npy),
    }
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_tokens(data_dir: Path = DATA_DIR) -> tuple[np.ndarray, np.ndarray]:
    return np.load(data_dir / "train.npy"), np.load(data_dir / "valid.npy")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare"])
    parser.add_argument("--train-mb", type=int, default=200)
    parser.add_argument("--vocab-size", type=int, default=DEFAULT_VOCAB_SIZE)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()

    manifest = prepare(args.train_mb, args.vocab_size, args.data_dir)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
