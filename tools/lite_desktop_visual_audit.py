from __future__ import annotations

import sys
from pathlib import Path

import pygame


root = Path(sys.argv[1])
paths = sorted(root.glob("*.png"))
if not paths:
    raise SystemExit("no UI evidence PNGs were produced")

pygame.init()
try:
    for path in paths:
        surface = pygame.image.load(str(path)).convert()
        raw = pygame.image.tostring(surface, "RGB")
        if surface.get_width() < 100 or surface.get_height() < 100:
            raise SystemExit(f"{path.name}: implausibly small surface")
        values = raw[::max(1, len(raw) // 4096)]
        if not values:
            raise SystemExit(f"{path.name}: empty pixel sample")
        spread = max(values) - min(values)
        unique = len(set(values))
        print(
            f"ui_scene={path.name} "
            f"size={surface.get_width()}x{surface.get_height()} "
            f"sample_spread={spread} unique_bytes={unique}"
        )
        if spread < 20 or unique < 8:
            raise SystemExit(f"{path.name}: screenshot appears visually empty")
finally:
    pygame.quit()
