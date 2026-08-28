"""Engine initialization and cross-cutting legality/replay guards."""

from __future__ import annotations

from functools import wraps


def _install_spell_silence_guard() -> None:
    """Make every concrete spell generator obey the authoritative silence rule."""
    from engine import pieces
    from engine.config import COLUNAS, LINHAS

    hero_defs = pieces.HERO_DEFS
    radius = int(hero_defs.get("Inquisitor", {}).get("aura_radius", 2))

    for cls in pieces.TODAS_AS_PECAS:
        method = cls.__dict__.get("get_valid_spells")
        if method is None or getattr(method, "_redwar_silence_guard", False):
            continue

        @wraps(method)
        def guarded(self, r, c, board, tile_effects=None, _method=method):
            if not self.can_act():
                return []
            for ir in range(LINHAS):
                for ic in range(COLUNAS):
                    source = board[ir][ic]
                    if (
                        source
                        and source.name == "Inquisitor"
                        and source.team != self.team
                        and max(abs(r - ir), abs(c - ic)) <= radius
                    ):
                        return []
            return _method(self, r, c, board, tile_effects)

        guarded._redwar_silence_guard = True
        setattr(cls, "get_valid_spells", guarded)


def _install_replay_capture_guard() -> None:
    """Capture the battle-start state on the first real action, not simulations."""
    from engine.game_state import GameState

    method = GameState.make_action
    if getattr(method, "_redwar_replay_capture_guard", False):
        return

    @wraps(method)
    def guarded(self, *args, **kwargs):
        is_simulation = bool(kwargs.get("is_simulation", False))
        if not is_simulation:
            from tools.replay.storage import capture_initial
            capture_initial(self)
        return method(self, *args, **kwargs)

    guarded._redwar_replay_capture_guard = True
    GameState.make_action = guarded


_install_spell_silence_guard()
_install_replay_capture_guard()
