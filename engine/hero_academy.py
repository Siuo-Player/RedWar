"""Canonical Hero Academy backed by the shared browser/Python lesson catalogue."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CATALOGUE_PATH = (
    Path(__file__).resolve().parents[1]
    / "deploy"
    / "web"
    / "hero_academy_lessons.json"
)
HERO_CONFIG_PATH = Path(__file__).resolve().with_name("heroes_config.json")


@dataclass
class AcademyLesson:
    hero_id: str
    hero_name: str
    title: str
    lore: str
    ability_description: str
    puzzle_objective: str
    initial_board: dict[str, list[dict[str, Any]]]
    solution_moves: list[dict[str, Any]]
    post_solve_explanation: str
    draftable: bool = True
    unit_category: str = "hero"
    actor_name: str | None = None


def _solution_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert the versioned catalogue action to the public legacy move shape."""
    result: dict[str, Any] = {
        "type": raw["type"],
        "from": (raw["fromR"], raw["fromC"]),
        "to": (raw["toR"], raw["toC"]),
    }
    for key in ("spell_name", "spawn_name", "area"):
        if key in raw:
            result[key] = raw[key]
    return result


def _action_from_attempt(move: dict[str, Any]):
    """Normalize a user attempt without coercing booleans or malformed coordinates."""
    from engine.actions import GameAction

    if not isinstance(move, dict):
        raise TypeError("move must be an object")
    action_type = move.get("type")
    start = move.get("from", move.get("start"))
    end = move.get("to", move.get("end"))
    if start is None or end is None:
        raise ValueError("move requires source and destination")
    payload: dict[str, Any] = {
        "type": action_type,
        "start": start,
        "end": end,
    }
    for key in ("spell_name", "spawn_name", "area"):
        if key in move:
            payload[key] = move[key]
    return GameAction.from_dict(payload)


def _solution_action(solution: dict[str, Any]):
    from engine.actions import GameAction

    payload: dict[str, Any] = {
        "type": solution["type"],
        "start": [solution["fromR"], solution["fromC"]],
        "end": [solution["toR"], solution["toC"]],
    }
    for key in ("spell_name", "spawn_name", "area"):
        if key in solution:
            payload[key] = solution[key]
    return GameAction.from_dict(payload)


def _build_initial_state(raw_lesson: dict[str, Any]):
    from engine.game_state import GameState
    from engine.pieces import criar_peca_por_nome

    state = GameState(rows=8, cols=8)
    for entry in raw_lesson["pieces"]:
        row, col = entry["r"], entry["c"]
        if (
            isinstance(row, bool) or not isinstance(row, int)
            or isinstance(col, bool) or not isinstance(col, int)
            or not (0 <= row < 8 and 0 <= col < 8)
        ):
            raise ValueError(f"Invalid lesson coordinate for {raw_lesson['hero_id']}")
        if state.board[row][col] is not None:
            raise ValueError(f"Duplicate lesson square {(row, col)}")
        piece = criar_peca_por_nome(entry["name"], entry["team"])
        stun = entry.get("stun", 0)
        if isinstance(stun, bool) or not isinstance(stun, int) or stun < 0:
            raise ValueError(f"Invalid stun value for {raw_lesson['hero_id']}")
        piece.stun_timer = stun
        state.board[row][col] = piece
    state.white_to_move = True
    return state


class HeroAcademy:
    """Loads a single versioned curriculum consumed by both Python and Web."""

    def __init__(self, catalogue_path: Path | None = None):
        self.catalogue_path = catalogue_path or CATALOGUE_PATH
        self._raw_lessons: dict[str, dict[str, Any]] = {}
        self._lessons: dict[str, AcademyLesson] = {}
        self._build_curriculum()

    def _build_curriculum(self) -> None:
        try:
            catalogue = json.loads(self.catalogue_path.read_text(encoding="utf-8"))
            hero_config = json.loads(HERO_CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Unable to load the canonical Hero Academy catalogue") from exc

        if not isinstance(catalogue, dict) or catalogue.get("schema_version") != 1:
            raise RuntimeError("Unsupported Hero Academy catalogue schema version")
        entries = catalogue.get("lessons")
        if not isinstance(entries, list):
            raise RuntimeError("Hero Academy catalogue must contain a lessons array")

        expected_ids = {name.lower() for name in hero_config}
        actual_ids = [entry.get("hero_id") for entry in entries if isinstance(entry, dict)]
        if len(actual_ids) != len(entries) or len(set(actual_ids)) != len(actual_ids):
            raise RuntimeError("Hero Academy catalogue contains malformed or duplicate lessons")
        if set(actual_ids) != expected_ids:
            missing = sorted(expected_ids - set(actual_ids))
            unexpected = sorted(set(actual_ids) - expected_ids)
            raise RuntimeError(
                f"Hero Academy roster mismatch; missing={missing}, unexpected={unexpected}"
            )

        for entry in entries:
            hero_id = entry["hero_id"]
            hero_name = entry.get("hero_name")
            if hero_name not in hero_config or hero_name.lower() != hero_id:
                raise RuntimeError(f"Invalid hero identity in lesson {hero_id!r}")
            draftable = bool(hero_config[hero_name].get("draftable", True))
            if entry.get("draftable") is not draftable:
                raise RuntimeError(f"Draftability mismatch for {hero_name}")
            expected_category = (
                "hero" if draftable
                else "obstacle" if hero_name == "StoneWall"
                else "summoned_unit"
            )
            if entry.get("unit_category") != expected_category:
                raise RuntimeError(f"Unit category mismatch for {hero_name}")

            required_text = ("title", "lore", "ability", "objective", "explanation")
            for field in required_text:
                value = entry.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise RuntimeError(f"Lesson {hero_name} is missing {field}")
            if not isinstance(entry.get("pieces"), list) or not entry["pieces"]:
                raise RuntimeError(f"Lesson {hero_name} has no initial pieces")
            _solution_action(entry["solution"])
            _build_initial_state(entry)
            self._raw_lessons[hero_id] = entry
            self._lessons[hero_id] = AcademyLesson(
                hero_id=hero_id,
                hero_name=hero_name,
                title=entry["title"],
                lore=entry["lore"],
                ability_description=entry["ability"],
                puzzle_objective=entry["objective"],
                initial_board={
                    "white": [
                        {"name": p["name"], "pos": (p["r"], p["c"]), "stun": p.get("stun", 0)}
                        for p in entry["pieces"] if p["team"] == "brancas"
                    ],
                    "black": [
                        {"name": p["name"], "pos": (p["r"], p["c"]), "stun": p.get("stun", 0)}
                        for p in entry["pieces"] if p["team"] == "pretas"
                    ],
                },
                solution_moves=[_solution_dict(entry["solution"])],
                post_solve_explanation=entry["explanation"],
                draftable=draftable,
                unit_category=expected_category,
                actor_name=entry.get("actor_name", hero_name),
            )

    def list_lessons(self) -> list[AcademyLesson]:
        """Return all 30 lessons in the canonical catalogue order."""
        return list(self._lessons.values())

    def get_lesson(self, hero_id: str) -> AcademyLesson | None:
        """Fetch a lesson by the lower-case configured unit identifier."""
        if not isinstance(hero_id, str):
            return None
        return self._lessons.get(hero_id.lower())

    def verify_solution(self, hero_id: str, move: dict[str, Any]) -> tuple[bool, str]:
        """Accept only the exact canonical action that is legal in the lesson position."""
        lesson = self.get_lesson(hero_id)
        if lesson is None:
            return False, "Lição não encontrada."
        raw = self._raw_lessons[lesson.hero_id]
        try:
            attempted = _action_from_attempt(move)
            expected = _solution_action(raw["solution"])
            if attempted != expected:
                return False, "Lance incorreto. Confirma o tipo de ação e as casas escolhidas."

            from engine.legal_actions import legal_actions

            state = _build_initial_state(raw)
            if attempted not in legal_actions(state):
                return False, "A solução desta lição não é uma ação legal nesta posição."
        except (KeyError, TypeError, ValueError, IndexError):
            return False, "Lance inválido. Verifica a peça, a ação e as coordenadas."
        return True, lesson.post_solve_explanation
