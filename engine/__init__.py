"""Engine initialization and cross-cutting legality/replay guards."""

from __future__ import annotations

import os
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


def _install_frostmage_nevada_rules() -> None:
    """Nevada is a selectable area spell; it does not require an enemy target."""
    from engine import pieces

    cls = pieces.FrostMage
    method = cls.__dict__.get("get_valid_spells")
    if method is None or getattr(method, "_redwar_nevada_rules", False):
        return

    @wraps(method)
    def nevada_targets(self, r, c, board, tile_effects=None):
        if not self.can_act():
            return []
        spells = []
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) > 3:
                    continue
                focus_r, focus_c = r + dr, c + dc
                if not (0 <= focus_r < pieces.LINHAS and 0 <= focus_c < pieces.COLUNAS):
                    continue
                if tile_effects and tile_effects[focus_r][focus_c] and tile_effects[focus_r][focus_c].get("type") == "ice":
                    continue
                spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})
        return spells

    nevada_targets._redwar_nevada_rules = True
    setattr(cls, "get_valid_spells", nevada_targets)


def _install_replay_capture_guard() -> None:
    """Capture the first live action and finalize the completed live game."""
    from engine.game_state import GameState

    make_action = GameState.make_action
    if not getattr(make_action, "_redwar_replay_capture_guard", False):

        @wraps(make_action)
        def guarded_make(self, *args, **kwargs):
            is_simulation = bool(kwargs.get("is_simulation", False))
            if not is_simulation:
                from tools.replay.storage import capture_initial
                capture_initial(self)
            return make_action(self, *args, **kwargs)

        guarded_make._redwar_replay_capture_guard = True
        GameState.make_action = guarded_make

    execute_action = GameState.execute_action
    if getattr(execute_action, "_redwar_replay_finalize_guard", False):
        return

    @wraps(execute_action)
    def guarded_execute(self, *args, **kwargs):
        try:
            result = execute_action(self, *args, **kwargs)
        except Exception as exc:
            try:
                from tools.replay.live_observability import record_attempt
                record_attempt(self, args, kwargs, "rejected", str(exc))
            except Exception:
                pass
            raise
        try:
            from tools.replay.live_observability import record_attempt
            record_attempt(self, args, kwargs, "accepted", None)
        except Exception:
            pass
        if self.game_over:
            from tools.replay.storage import finalize_completed_game
            game_id = finalize_completed_game(self)
            if game_id:
                try:
                    from tools.replay.live_observability import persist_attempts
                    persist_attempts(self, game_id)
                except Exception:
                    pass
        return result

    guarded_execute._redwar_replay_finalize_guard = True
    GameState.execute_action = guarded_execute


_install_spell_silence_guard()
_install_frostmage_nevada_rules()
_install_replay_capture_guard()
