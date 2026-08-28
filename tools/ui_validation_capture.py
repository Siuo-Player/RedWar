from pathlib import Path

import pygame

from tools.ui_validation import SCENES, scene_path


def save_scene(surface: pygame.Surface, output_dir: str | Path, scene: str) -> Path:
    """Save an already-rendered scene using the canonical validation name."""
    if not isinstance(surface, pygame.Surface):
        raise TypeError("surface must be a pygame.Surface")
    if scene not in SCENES:
        raise ValueError(f"unknown validation scene: {scene}")

    path = scene_path(output_dir, scene)
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))
    return path
