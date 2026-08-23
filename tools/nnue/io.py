from __future__ import annotations

import struct
from pathlib import Path
from typing import Sequence

MAGIC = b"RWNUE002"
VERSION = 2
HEADER = struct.Struct("<8sIIHHiii")


class ModelFormatError(ValueError):
    pass


def _pack_int32(values: Sequence[int]) -> bytes:
    return struct.pack(f"<{len(values)}i", *(int(v) for v in values))


def _pack_int16(values: Sequence[int]) -> bytes:
    checked = [int(v) for v in values]
    if any(v < -32768 or v > 32767 for v in checked):
        raise ModelFormatError("int16 weight out of range")
    return struct.pack(f"<{len(checked)}h", *checked)


def _read_many(data: bytes, offset: int, fmt: str, count: int) -> tuple[list[int], int]:
    item_size = struct.calcsize(fmt)
    end = offset + item_size * count
    if end > len(data):
        raise ModelFormatError("truncated NNUE model")
    return list(struct.unpack(f"<{count}{fmt}", data[offset:end])), end


def write_model(
    path: str | Path,
    *,
    features: int,
    accumulator: int,
    hidden: int,
    accumulator_scale: int,
    hidden_scale: int,
    output_scale: int,
    bias1: Sequence[int],
    weights1: Sequence[int],
    bias2: Sequence[int],
    weights2: Sequence[int],
    bias3: int,
    weights3: Sequence[int],
) -> None:
    if min(accumulator_scale, hidden_scale, output_scale) <= 0:
        raise ModelFormatError("quantization scales must be positive")
    if len(bias1) != accumulator:
        raise ModelFormatError("bias1 length mismatch")
    if len(weights1) != features * accumulator:
        raise ModelFormatError("weights1 length mismatch")
    if len(bias2) != hidden:
        raise ModelFormatError("bias2 length mismatch")
    if len(weights2) != accumulator * 2 * hidden:
        raise ModelFormatError("weights2 length mismatch")
    if len(weights3) != hidden:
        raise ModelFormatError("weights3 length mismatch")

    blob = bytearray(
        HEADER.pack(
            MAGIC,
            VERSION,
            int(features),
            int(accumulator),
            int(hidden),
            int(accumulator_scale),
            int(hidden_scale),
            int(output_scale),
        )
    )
    blob.extend(_pack_int32(bias1))
    blob.extend(_pack_int16(weights1))
    blob.extend(_pack_int32(bias2))
    blob.extend(_pack_int16(weights2))
    blob.extend(struct.pack("<i", int(bias3)))
    blob.extend(_pack_int16(weights3))

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(blob)


def read_model(path: str | Path) -> dict[str, object]:
    data = Path(path).read_bytes()
    if len(data) < HEADER.size:
        raise ModelFormatError("truncated NNUE header")

    magic, version, features, accumulator, hidden, acc_scale, hidden_scale, output_scale = HEADER.unpack_from(data, 0)
    if magic != MAGIC or version != VERSION:
        raise ModelFormatError("unsupported NNUE model format")

    offset = HEADER.size
    bias1, offset = _read_many(data, offset, "i", accumulator)
    weights1, offset = _read_many(data, offset, "h", features * accumulator)
    bias2, offset = _read_many(data, offset, "i", hidden)
    weights2, offset = _read_many(data, offset, "h", accumulator * 2 * hidden)
    bias3_values, offset = _read_many(data, offset, "i", 1)
    weights3, offset = _read_many(data, offset, "h", hidden)

    if offset != len(data):
        raise ModelFormatError("trailing bytes in NNUE model")

    return {
        "version": version,
        "features": features,
        "accumulator": accumulator,
        "hidden": hidden,
        "accumulator_scale": acc_scale,
        "hidden_scale": hidden_scale,
        "output_scale": output_scale,
        "bias1": bias1,
        "weights1": weights1,
        "bias2": bias2,
        "weights2": weights2,
        "bias3": bias3_values[0],
        "weights3": weights3,
    }
