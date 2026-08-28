from pathlib import Path

import pygame
import pytest

from tools.ui_validation_capture import save_scene


def test_save_scene_writes_expected_png(tmp_path: Path):
    pygame.init()
    try:
        surface = pygame.Surface((32, 24))
        surface.fill((12, 34, 56))
        output = save_scene(surface, tmp_path, "battle_idle")
        assert output == tmp_path / "battle_idle.png"
        assert output.exists()
        assert output.stat().st_size > 0
    finally:
        pygame.quit()


def test_save_scene_rejects_invalid_surface(tmp_path: Path):
    with pytest.raises(TypeError):
        save_scene(object(), tmp_path, "battle_idle")


def test_save_scene_rejects_unknown_scene(tmp_path: Path):
    pygame.init()
    try:
        surface = pygame.Surface((4, 4))
        with pytest.raises(ValueError):
            save_scene(surface, tmp_path, "unknown")
    finally:
        pygame.quit()
