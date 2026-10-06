from __future__ import annotations

import math
import sys
import wave
from pathlib import Path


path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(f"recording not found: {path}")

with wave.open(str(path), "rb") as wav:
    frames = wav.readframes(wav.getnframes())
    sample_width = wav.getsampwidth()
    channels = wav.getnchannels()
    rate = wav.getframerate()

if sample_width != 2 or channels != 1:
    raise SystemExit(f"unexpected audio format: width={sample_width}, channels={channels}")

samples = memoryview(frames).cast("h")
if not samples:
    raise SystemExit("audio recording is empty")

peak = max(abs(int(sample)) for sample in samples)
active = sum(1 for sample in samples if int(sample) != 0)
ratio = active / len(samples)

print(f"audio_probe rate={rate} samples={len(samples)} peak={peak} active_ratio={ratio:.4f}")

if peak < 500:
    raise SystemExit(f"captured audio is effectively silent: peak={peak}")
if ratio < 0.01:
    raise SystemExit(f"captured audio is too sparse: active_ratio={ratio:.4f}")
