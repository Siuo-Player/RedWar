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
        method = getattr(cls, "get_valid_spells", None)
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
                        and source.can_act()
                        and max(abs(r - ir), abs(c - ic)) <= radius
                    ):
                        return []
            return _method(self, r, c, board, tile_effects)

        guarded._redwar_silence_guard = True
        setattr(cls, "get_valid_spells", guarded)


def _install_frostmage_nevada_rules() -> None:
    """Nevada is a selectable area spell and does not require an enemy target."""
    from engine import pieces
    from engine.config import COLUNAS, LINHAS

    cls = pieces.FrostMage
    method = cls.__dict__.get("get_valid_spells")
    if method is None or getattr(method, "_redwar_nevada_rules", False):
        return

    @wraps(method)
    def nevada_targets(self, r, c, board, tile_effects=None, _method=method):
        if not self.can_act():
            return []

        radius = int(pieces.HERO_DEFS.get("Inquisitor", {}).get("aura_radius", 2))
        for ir in range(LINHAS):
            for ic in range(COLUNAS):
                source = board[ir][ic]
                if (
                    source
                    and source.name == "Inquisitor"
                    and source.team != self.team
                    and source.can_act()
                    and max(abs(r - ir), abs(c - ic)) <= radius
                ):
                    return []

        spells = []
        for dr in range(-3, 4):
            for dc in range(-3, 4):
                if abs(dr) + abs(dc) > 3:
                    continue
                focus_r, focus_c = r + dr, c + dc
                if not (0 <= focus_r < LINHAS and 0 <= focus_c < COLUNAS):
                    continue
                if focus_r == r and focus_c == c:
                    continue
                if (
                    tile_effects
                    and tile_effects[focus_r][focus_c]
                    and tile_effects[focus_r][focus_c].get("type") == "ice"
                ):
                    continue
                spells.append({"target": (focus_r, focus_c), "spell_type": "nevada"})
        return spells

    nevada_targets._redwar_nevada_rules = True
    setattr(cls, "get_valid_spells", nevada_targets)


def _install_replay_capture_guard() -> None:
    """Capture and finalize real live games while excluding simulations."""
    from engine.game_state import GameState

    make_action = GameState.make_action
    if not getattr(make_action, "_redwar_replay_capture_guard", False):

        @wraps(make_action)
        def guarded_make(self, *args, **kwargs):
            is_simulation = bool(kwargs.get("is_simulation", False))
            if not is_simulation:
                from tools.replay.storage import capture_initial
                capture_initial(self)
            result = make_action(self, *args, **kwargs)
            if not is_simulation and self.game_over:
                from tools.replay.storage import finalize_completed_game
                finalize_completed_game(self)
            return result

        guarded_make._redwar_replay_capture_guard = True
        GameState.make_action = guarded_make


def _install_direct_spell_silence_rule() -> None:
    """Keep direct GameState spell execution aligned with spell generation."""
    from engine.config import COLUNAS, LINHAS
    from engine.game_state import GameState
    from engine.game_state import HERO_DEFS

    method = GameState._is_silenced_piece
    if getattr(method, "_redwar_direct_silence_rule", False):
        return

    @wraps(method)
    def guarded(self, piece, row, col, _method=method):
        for r in range(LINHAS):
            for c in range(COLUNAS):
                source = self.board[r][c]
                if (
                    source
                    and source.team != piece.team
                    and source.name == "Inquisitor"
                    and source.can_act()
                    and max(abs(row - r), abs(col - c)) <= int(HERO_DEFS.get("Inquisitor", {}).get("aura_radius", 2))
                ):
                    return True
        return False

    guarded._redwar_direct_silence_rule = True
    GameState._is_silenced_piece = guarded


def _install_authoritative_execute_legality_guard() -> None:
    """Reject actions that are not in the canonical current legal action space."""
    from engine.actions import ActionType, normalize_action
    from engine.game_state import GameState
    from engine.legal_actions import legal_actions

    execute_action = GameState.execute_action
    if getattr(execute_action, "_redwar_authoritative_legality_guard", False):
        return

    @wraps(execute_action)
    def guarded_execute(self, acao_dict, _execute_action=execute_action):
        action = normalize_action(acao_dict)
        available = legal_actions(self)

        if action.type == ActionType.STUN and not action.area:
            # Legacy STUN payloads historically omitted the derived AOE. Resolve
            # that compatibility form to the unique canonical action before the
            # legality check, without changing GameAction equality semantics.
            compatible = [
                candidate
                for candidate in available
                if candidate.type == action.type
                and candidate.start == action.start
                and candidate.end == action.end
                and candidate.spawn_name == action.spawn_name
                and candidate.spell_name == action.spell_name
            ]
            if len(compatible) == 1:
                action = compatible[0]

        if action not in set(available):
            raise ValueError(f"illegal action for current position: {action.to_dict()}")

        return _execute_action(self, action)

    guarded_execute._redwar_authoritative_legality_guard = True
    GameState.execute_action = guarded_execute


_install_spell_silence_guard()
_install_frostmage_nevada_rules()
_install_replay_capture_guard()
_install_direct_spell_silence_rule()
_install_authoritative_execute_legality_guard()
