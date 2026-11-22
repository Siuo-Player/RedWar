"""Regression tests for the canonical 30-unit Hero Academy catalogue."""

import json
from pathlib import Path


from engine.actions import GameAction
from engine.game_state import GameState
from engine.hero_academy import HeroAcademy
from engine.legal_actions import legal_actions
from engine.pieces import criar_peca_por_nome


ROOT = Path(__file__).parents[1]
HERO_CONFIG_PATH = ROOT / "engine" / "heroes_config.json"
CATALOGUE_PATH = ROOT / "deploy" / "web" / "hero_academy_lessons.json"


def _catalogue():
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def _build_state(lesson):
    state = GameState(rows=8, cols=8)
    for entry in lesson["pieces"]:
        r, c = entry["r"], entry["c"]
        assert 0 <= r < 8 and 0 <= c < 8
        assert state.board[r][c] is None, f"duplicate academy square {(r, c)}"
        piece = criar_peca_por_nome(entry["name"], entry["team"])
        piece.stun_timer = entry.get("stun", 0)
        state.board[r][c] = piece
    state.white_to_move = True
    return state


def _canonical_solution(lesson):
    solution = lesson["solution"]
    payload = {
        "type": solution["type"],
        "start": [solution["fromR"], solution["fromC"]],
        "end": [solution["toR"], solution["toC"]],
    }
    for key in ("area", "spell_name", "spawn_name"):
        if key in solution:
            payload[key] = solution[key]
    return GameAction.from_dict(payload)


def test_catalogue_covers_exactly_the_configured_roster():
    config = json.loads(HERO_CONFIG_PATH.read_text(encoding="utf-8"))
    catalogue = _catalogue()
    lessons = catalogue["lessons"]

    assert catalogue["schema_version"] == 1
    assert len(lessons) == 30
    assert len({lesson["hero_id"] for lesson in lessons}) == 30
    assert {lesson["hero_id"] for lesson in lessons} == {
        name.lower() for name in config
    }


def test_lessons_distinguish_draftable_heroes_from_non_draftable_units():
    config = json.loads(HERO_CONFIG_PATH.read_text(encoding="utf-8"))
    lessons = {lesson["hero_id"]: lesson for lesson in _catalogue()["lessons"]}

    for name, definition in config.items():
        lesson = lessons[name.lower()]
        is_draftable = bool(definition.get("draftable", True))
        assert lesson["draftable"] is is_draftable
        expected_category = (
            "hero" if is_draftable
            else "obstacle" if name == "StoneWall"
            else "summoned_unit"
        )
        assert lesson["unit_category"] == expected_category


def test_every_lesson_has_complete_portuguese_teaching_content_and_board():
    config = json.loads(HERO_CONFIG_PATH.read_text(encoding="utf-8"))
    for lesson in _catalogue()["lessons"]:
        assert lesson["hero_name"] in config
        assert len(lesson["title"].strip()) >= 8
        assert len(lesson["lore"].strip()) >= 40
        assert len(lesson["ability"].strip()) >= 20
        assert len(lesson["objective"].strip()) >= 20
        assert len(lesson["explanation"].strip()) >= 30
        assert lesson["pieces"]
        assert "type" in lesson["solution"]
        assert {"fromR", "fromC", "toR", "toC"} <= set(lesson["solution"])


def test_every_academy_solution_is_legal_in_the_canonical_engine():
    for lesson in _catalogue()["lessons"]:
        state = _build_state(lesson)
        solution = _canonical_solution(lesson)
        assert solution in legal_actions(state), (
            f"{lesson['hero_id']} has a non-legal solution: {solution.to_dict()}"
        )


def test_python_academy_loads_the_same_complete_catalogue():
    academy = HeroAcademy()
    lessons = academy.list_lessons()

    assert len(lessons) == 30
    assert {lesson.hero_id for lesson in lessons} == {
        name.lower()
        for name in json.loads(HERO_CONFIG_PATH.read_text(encoding="utf-8"))
    }
    assert academy.get_lesson("stonewall").draftable is False
    assert academy.get_lesson("stonewall").unit_category == "obstacle"


def test_solution_verification_checks_action_type_not_only_coordinates():
    academy = HeroAcademy()
    lesson = academy.get_lesson("paladin")
    solution = dict(lesson.solution_moves[0])

    assert academy.verify_solution("paladin", solution)[0] is True

    wrong_action = dict(solution)
    wrong_action["type"] = "surrender"
    assert academy.verify_solution("paladin", wrong_action)[0] is False


def test_unknown_and_malformed_lesson_attempts_are_rejected():
    academy = HeroAcademy()
    assert academy.verify_solution("not-a-unit", {"type": "move"})[0] is False
    assert academy.verify_solution("paladin", {"from": [True, 0], "to": [1, 0]})[0] is False


def test_web_academy_loads_the_shared_catalogue_and_builds_the_selector():
    app_js = (ROOT / "deploy" / "web" / "app.js").read_text(encoding="utf-8")
    html = (ROOT / "deploy" / "web" / "index.html").read_text(encoding="utf-8")

    assert 'fetch("hero_academy_lessons.json")' in app_js or "fetch('hero_academy_lessons.json')" in app_js
    assert "const HERO_LESSONS = {" not in app_js
    selector = html.split('id="heroSelect"', 1)[1].split("</select>", 1)[0]
    assert "<option" not in selector


def test_every_solution_uses_the_declared_actor_and_exact_action_metadata():
    for lesson in _catalogue()["lessons"]:
        solution = lesson["solution"]
        state = _build_state(lesson)
        actor = state.board[solution["fromR"]][solution["fromC"]]
        assert actor is not None
        assert actor.name == lesson["actor_name"]
        assert actor.team == "brancas"
        if solution["type"] == "spell":
            assert solution.get("spell_name")
        if solution["type"] == "spawn":
            assert solution.get("spawn_name")


def test_catalogue_has_27_selectable_heroes_and_three_unit_entries():
    catalogue = _catalogue()
    assert sum(1 for lesson in catalogue["lessons"] if lesson["draftable"]) == 27
    assert {
        lesson["hero_id"] for lesson in catalogue["lessons"] if not lesson["draftable"]
    } == {"bone", "ghoul", "stonewall"}


def test_web_rules_cover_nightshade_ghost_orthogonal_movement():
    app_js = (ROOT / "deploy" / "web" / "app.js").read_text(encoding="utf-8")
    assert 'Nightshade: {\n    move: { type: "orthogonal", steps: 4, ghost: true }' in app_js


def test_web_academy_allows_legal_ally_spell_targets():
    app_js = (ROOT / "deploy" / "web" / "app.js").read_text(encoding="utf-8")
    assert 'act => act.r === r && act.c === c && act.type === "spell"' in app_js
    assert "&& !alliedSpellTarget" in app_js


def test_catalogue_loader_does_not_enter_academy_mode_on_page_boot():
    app_js = (ROOT / "deploy" / "web" / "app.js").read_text(encoding="utf-8")
    loader_start = app_js.index("async function loadAcademyCurriculum")
    loader_end = app_js.index("\nfunction ", loader_start + 10)
    loader_body = app_js[loader_start:loader_end]
    assert "loadAcademyLesson(selector.value)" not in loader_body


def test_valkyrie_academy_teaches_declared_three_step_ghost_movement():
    catalogue = _catalogue()
    lesson = next(item for item in catalogue["lessons"] if item["hero_id"] == "valkyrie")
    assert lesson["solution"]["type"] == "move"
    assert (lesson["solution"]["fromR"], lesson["solution"]["fromC"]) == (5, 3)
    assert (lesson["solution"]["toR"], lesson["solution"]["toC"]) == (2, 3)
    assert "três casas" in lesson["ability"].lower()
    assert "atravessa" in lesson["ability"].lower()
    assert "issue #679" not in lesson["ability"].lower()
    app_js = (ROOT / "deploy" / "web" / "app.js").read_text(encoding="utf-8")
    start = app_js.index("Valkyrie: {", app_js.index("const HERO_RULES = {"))
    block = app_js[start:start + 240]
    assert 'move: { type: "adjacent", steps: 3, ghost: true }' in block
