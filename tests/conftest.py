import pytest

from tools.replay import interaction


@pytest.fixture(autouse=True)
def _minimal_controller_without_surface(monkeypatch):
    """Keep non-rendering controller doubles independent from pygame surfaces."""
    original = interaction._encyclopedia_button_rect

    def safe_button_rect(controller):
        if not hasattr(controller, "ecra"):
            import pygame
            return pygame.Rect(-1, -1, 0, 0)
        return original(controller)

    monkeypatch.setattr(interaction, "_encyclopedia_button_rect", safe_button_rect)
