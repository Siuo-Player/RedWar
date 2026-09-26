from pathlib import Path


MAIN = Path(__file__).resolve().parents[1] / "main.py"


def test_battle_ui_exposes_surrender_control_and_routes_to_authoritative_action():
    source = MAIN.read_text(encoding="utf-8")

    assert "self.btn_surrender = pygame.Rect" in source
    assert "if self.btn_surrender.collidepoint(pos)" in source
    assert 'self._execute_action_with_sound({"type": "surrender", "actor_team": current_team})' in source
    assert "self._execute_action_with_sound({\"type\": \"surrender\", \"actor_team\": current_team})" in source
    assert 'label = "Desistir" if enabled else "Desistir (turno IA)"' in source
