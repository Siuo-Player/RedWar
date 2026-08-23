from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from tools.nnue.features import FEATURE_COUNT, active_features
from tools.nnue.io import write_model


class DatasetError(ValueError):
    pass


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or "rwen" not in row or "score" not in row:
            raise DatasetError(f"Line {lineno}: expected {{rwen, score}}")
        rows.append(row)
    if not rows:
        raise DatasetError("dataset is empty")
    return rows


def _require_torch():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise SystemExit(
            "NNUE training requires optional PyTorch. Install it separately with: pip install torch"
        ) from exc
    return torch, nn


def train(dataset: str, output: str, epochs: int, batch_size: int, lr: float, seed: int) -> None:
    torch, nn = _require_torch()
    torch.manual_seed(seed)
    random.seed(seed)

    rows = _load_rows(dataset)
    features = [active_features(str(row["rwen"])) for row in rows]
    targets = [float(row["score"]) for row in rows]
    if any(len(left) == 0 or len(right) == 0 for left, right in features):
        raise DatasetError("every position must produce features for both perspectives")

    split = max(1, int(len(rows) * 0.9))
    train_rows = list(range(split))
    valid_rows = list(range(split, len(rows))) or train_rows[:1]

    class NNUE(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.embedding = nn.Embedding(FEATURE_COUNT, 128)
            self.hidden = nn.Linear(256, 32)
            self.output = nn.Linear(32, 1)

        def forward(self, ids0, mask0, ids1, mask1):
            a0 = (self.embedding(ids0) * mask0.unsqueeze(-1)).sum(dim=1)
            a1 = (self.embedding(ids1) * mask1.unsqueeze(-1)).sum(dim=1)
            hidden = torch.clamp(self.hidden(torch.cat((a0, a1), dim=1)), 0.0, 127.0)
            return self.output(hidden).squeeze(1)

    model = NNUE()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
    loss_fn = nn.SmoothL1Loss()

    def make_batch(indices):
        max0 = max(len(features[i][0]) for i in indices)
        max1 = max(len(features[i][1]) for i in indices)
        ids0 = torch.zeros((len(indices), max0), dtype=torch.long)
        ids1 = torch.zeros((len(indices), max1), dtype=torch.long)
        mask0 = torch.zeros((len(indices), max0))
        mask1 = torch.zeros((len(indices), max1))
        y = torch.tensor([targets[i] for i in indices], dtype=torch.float32)
        for row_no, idx in enumerate(indices):
            f0, f1 = features[idx]
            ids0[row_no, : len(f0)] = torch.tensor(f0, dtype=torch.long)
            ids1[row_no, : len(f1)] = torch.tensor(f1, dtype=torch.long)
            mask0[row_no, : len(f0)] = 1.0
            mask1[row_no, : len(f1)] = 1.0
        return ids0, mask0, ids1, mask1, y

    for epoch in range(1, epochs + 1):
        random.shuffle(train_rows)
        model.train()
        train_loss = 0.0
        for start in range(0, len(train_rows), batch_size):
            batch = train_rows[start : start + batch_size]
            ids0, mask0, ids1, mask1, y = make_batch(batch)
            optimizer.zero_grad(set_to_none=True)
            pred = model(ids0, mask0, ids1, mask1)
            loss = loss_fn(pred, y)
            loss.backward()
            optimizer.step()
            train_loss += float(loss.item()) * len(batch)

        model.eval()
        with torch.no_grad():
            ids0, mask0, ids1, mask1, y = make_batch(valid_rows)
            validation_loss = float(loss_fn(model(ids0, mask0, ids1, mask1), y).item())
        print(
            f"epoch={epoch} train_loss={train_loss/max(1,len(train_rows)):.3f} "
            f"validation_loss={validation_loss:.3f}"
        )

    state = model.state_dict()
    acc_scale = 64
    hidden_scale = 64
    output_scale = 64

    embedding = state["embedding.weight"].detach().cpu().reshape(-1).tolist()
    hidden_bias = state["hidden.bias"].detach().cpu().reshape(-1).tolist()
    output_weight = state["output.weight"].detach().cpu().reshape(-1).tolist()
    output_bias = state["output.bias"].detach().cpu().reshape(-1).tolist()

    # PyTorch stores Linear weights as [hidden][input], while the C++ runtime
    # stores them as [input][hidden] for contiguous hidden-neuron evaluation.
    hidden_matrix = state["hidden.weight"].detach().cpu()
    hidden_weight = hidden_matrix.t().reshape(-1).tolist()

    quant = lambda values, scale: [int(round(float(v) * scale)) for v in values]
    write_model(
        output,
        features=FEATURE_COUNT,
        accumulator=128,
        hidden=32,
        accumulator_scale=acc_scale,
        hidden_scale=hidden_scale,
        output_scale=output_scale,
        bias1=quant([0.0] * 128, acc_scale),
        weights1=quant(embedding, acc_scale),
        bias2=quant(hidden_bias, hidden_scale),
        weights2=quant(hidden_weight, hidden_scale),
        bias3=int(round(float(output_bias[0]) * output_scale)),
        weights3=quant(output_weight, output_scale),
    )
    print(f"trained model written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the optional RedWar NNUE model")
    parser.add_argument("dataset")
    parser.add_argument("--output", default="data/nnue/ares.nnue")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=20260823)
    args = parser.parse_args()
    train(args.dataset, args.output, args.epochs, args.batch_size, args.lr, args.seed)


if __name__ == "__main__":
    main()
