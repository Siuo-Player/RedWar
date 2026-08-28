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


def _install_rwen_serialization_compat() -> None:
    """Preserve the legacy GameState RWEN contract used by Arena/differential tools."""
    from engine.config import COLUNAS, LINHAS
    from engine.game_state import GameState

    if getattr(GameState, "to_rwen", None) is not None:
        return

    def to_rwen(self) -> str:
        lines = []
        for r in range(LINHAS):
            cells = []
            for c in range(COLUNAS):
                piece = self.board[r][c]
                effect = self.tile_effects[r][c]

                if not piece:
                    piece_str = "."
                else:
                    team = "W" if piece.team == "brancas" else "B"
                    name = piece.name.replace(" ", "")
                    lifespan = str(piece.lifespan) if getattr(piece, "lifespan", None) is not None else "N"
                    cooldown = str(getattr(piece, "spawn_cooldown", 0))
                    piece_str = f"{team}_{name}_{piece.stun_timer}_{lifespan}_{cooldown}"

                if not effect:
                    effect_str = "."
                else:
                    effect_team = "W" if effect.get("team") == "brancas" else "B"
                    effect_str = f"{effect_team}_{effect.get('type', 'none')}_{effect.get('timer', 0)}"

                cells.append(f"{piece_str}:{effect_str}")
            lines.append(",".join(cells))

        turn = "W" if self.white_to_move else "B"
        return f"{'/'.join(lines)} {turn} {self.turns_without_capture}"

    GameState.to_rwen = to_rwen


_install_spell_silence_guard()
_install_frostmage_nevada_rules()
_install_replay_capture_guard()
_install_rwen_serialization_compat()
