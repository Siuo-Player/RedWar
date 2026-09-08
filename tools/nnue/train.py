from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
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


def _grouped_validation_split(
    rows: list[dict[str, Any]], validation_fraction: float
) -> tuple[list[int], list[int]]:
    """Split by exact position identity so duplicate RWENs cannot cross the boundary."""
    if not 0.0 < validation_fraction < 1.0:
        raise DatasetError("validation_fraction must be between 0 and 1")

    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        key = str(row["rwen"]).strip()
        groups.setdefault(key, []).append(index)

    ranked_groups = sorted(
        groups.items(),
        key=lambda item: hashlib.sha256(item[0].encode("utf-8")).hexdigest(),
    )
    target = max(1, int(round(len(rows) * validation_fraction)))
    target = min(target, len(rows) - 1) if len(rows) > 1 else target

    validation: list[int] = []
    validation_group_count = max(1, len(ranked_groups) // 100)
    for group_index, (_key, indices) in enumerate(ranked_groups):
        remaining_groups = len(ranked_groups) - group_index - 1
        if not validation:
            take_group = True
        elif len(validation) < target and remaining_groups >= 1:
            take_group = True
        else:
            take_group = len(validation) < target and group_index < validation_group_count

        if take_group:
            validation.extend(indices)
        if len(validation) >= target and len(validation) < len(rows):
            break

    validation_set = set(validation)
    train = [index for index in range(len(rows)) if index not in validation_set]
    validation = sorted(validation_set)

    if not train or not validation:
        raise DatasetError("unable to construct non-empty grouped train/validation split")

    overlap = {str(rows[i]["rwen"]).strip() for i in train} & {
        str(rows[i]["rwen"]).strip() for i in validation
    }
    if overlap:
        raise DatasetError("grouped validation split leaked duplicate RWEN positions")

    return train, validation


def _require_torch():
    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise SystemExit(
            "NNUE training requires optional PyTorch. Install it separately with: pip install torch"
        ) from exc
    return torch, nn


def train(
    dataset: str,
    output: str,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
    max_seconds: float | None = None,
    validation_fraction: float = 0.1,
) -> None:
    torch, nn = _require_torch()
    torch.manual_seed(seed)
    random.seed(seed)
    started = time.monotonic()

    rows = _load_rows(dataset)
    features = [active_features(str(row["rwen"])) for row in rows]
    targets = [float(row["score"]) for row in rows]
    if any(len(left) == 0 or len(right) == 0 for left, right in features):
        raise DatasetError("every position must produce features for both perspectives")

    train_rows, valid_rows = _grouped_validation_split(rows, validation_fraction)
    print(
        f"dataset_rows={len(rows)} unique_positions={len({str(row['rwen']).strip() for row in rows})} "
        f"train_rows={len(train_rows)} validation_rows={len(valid_rows)} "
        f"validation_fraction={validation_fraction:.3f}"
    )

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

    completed_epochs = 0
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
        completed_epochs = epoch
        print(
            f"epoch={epoch} train_loss={train_loss/max(1,len(train_rows)):.3f} "
            f"validation_loss={validation_loss:.3f} elapsed={time.monotonic()-started:.1f}s"
        )

        if max_seconds is not None and time.monotonic() - started >= max_seconds:
            print(f"time limit reached after {completed_epochs} epochs")
            break

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
    print(f"trained model written to {output} after {completed_epochs} epochs")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the optional RedWar NNUE model")
    parser.add_argument("dataset")
    parser.add_argument("--output", default="data/nnue/ares.nnue")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=20260823)
    parser.add_argument("--max-seconds", type=float, default=None)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    args = parser.parse_args()
    train(
        args.dataset,
        args.output,
        args.epochs,
        args.batch_size,
        args.lr,
        args.seed,
        args.max_seconds,
        args.validation_fraction,
    )


if __name__ == "__main__":
    main()
