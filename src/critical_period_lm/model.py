"""A small decoder-only transformer in MLX.

Not part of the freeze corpus: this is implementation, and it may be fixed or optimised
while runs are in flight. What is frozen is that every condition in the grid shares one
configuration — the architecture is never tuned per condition, and the config hash written
into each run record is what proves it.

Deliberately unremarkable: RMSNorm, RoPE, causal attention, GELU MLP, tied embeddings.
Nothing here should be interesting enough to explain a result.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten


@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 4096
    d_model: int = 256
    n_layers: int = 8
    n_heads: int = 8
    d_ff: int = 1024
    seq_len: int = 256
    rope_base: float = 10_000.0

    def __post_init__(self) -> None:
        if self.d_model % self.n_heads:
            raise ValueError("d_model must be divisible by n_heads")

    def as_dict(self) -> dict:
        return asdict(self)


class Attention(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.n_heads = config.n_heads
        self.head_dim = config.d_model // config.n_heads
        self.scale = self.head_dim**-0.5
        self.qkv = nn.Linear(config.d_model, 3 * config.d_model, bias=False)
        self.out = nn.Linear(config.d_model, config.d_model, bias=False)
        self.rope = nn.RoPE(self.head_dim, base=config.rope_base)

    def __call__(self, x: mx.array) -> mx.array:
        batch, seq, _ = x.shape
        qkv = self.qkv(x).reshape(batch, seq, 3, self.n_heads, self.head_dim)
        q, k, v = (qkv[:, :, i].transpose(0, 2, 1, 3) for i in range(3))
        q, k = self.rope(q), self.rope(k)
        attended = mx.fast.scaled_dot_product_attention(
            q, k, v, scale=self.scale, mask="causal"
        )
        return self.out(attended.transpose(0, 2, 1, 3).reshape(batch, seq, -1))


class Block(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.attn_norm = nn.RMSNorm(config.d_model)
        self.attn = Attention(config)
        self.mlp_norm = nn.RMSNorm(config.d_model)
        self.up = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.down = nn.Linear(config.d_ff, config.d_model, bias=False)

    def __call__(self, x: mx.array) -> mx.array:
        x = x + self.attn(self.attn_norm(x))
        return x + self.down(nn.gelu(self.up(self.mlp_norm(x))))


class Transformer(nn.Module):
    """Tied-embedding decoder-only language model."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.blocks = [Block(config) for _ in range(config.n_layers)]
        self.final_norm = nn.RMSNorm(config.d_model)

    def __call__(self, tokens: mx.array) -> mx.array:
        x = self.embedding(tokens)
        for block in self.blocks:
            x = block(x)
        return self.embedding.as_linear(self.final_norm(x))

    def loss(self, inputs: mx.array, targets: mx.array) -> mx.array:
        """Mean cross-entropy in nats per token, which is the registered endpoint unit."""
        return nn.losses.cross_entropy(self(inputs), targets, reduction="mean")

    @property
    def n_params(self) -> int:
        return sum(p.size for _, p in tree_flatten(self.parameters()))

    @property
    def n_params_non_embedding(self) -> int:
        return self.n_params - self.embedding.weight.size
