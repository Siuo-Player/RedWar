# tests/test_hero_academy.py
"""
Test suite for Hero Academy (Academia de Heróis) interactive tutorial puzzles and lore.
"""
import pytest
from engine.hero_academy import HeroAcademy, AcademyLesson


def test_hero_academy_roster_completeness():
    academy = HeroAcademy()
    lessons = academy.list_lessons()
    assert len(lessons) >= 6

    # Verify key heroes are present
    hero_ids = [l.hero_id for l in lessons]
    for expected in ["paladin", "shadowblade", "stormcaller", "dragoon", "frostmage", "bonelord"]:
        assert expected in hero_ids


def test_lesson_structure_and_lore():
    academy = HeroAcademy()
    lesson = academy.get_lesson("shadowblade")
    assert lesson is not None
    assert lesson.hero_name == "Shadowblade"
    assert "fantasma" in lesson.ability_description.lower() or "atravessa" in lesson.ability_description.lower()
    assert len(lesson.lore) > 20
    assert len(lesson.solution_moves) >= 1
    assert len(lesson.post_solve_explanation) > 10


def test_interactive_puzzle_validation():
    academy = HeroAcademy()
    # Test valid solution for Paladin
    paladin_lesson = academy.get_lesson("paladin")
    first_solution = paladin_lesson.solution_moves[0]
    
    is_valid, feedback = academy.verify_solution("paladin", first_solution)
    assert is_valid is True
    assert "Excelente" in feedback or "Correto" in feedback or "Vitória" in feedback

    # Test invalid move
    is_valid, feedback = academy.verify_solution("paladin", {"from": (0, 0), "to": (1, 1)})
    assert is_valid is False
    assert "Tenta novamente" in feedback or "Incorreto" in feedback


def test_all_lessons_have_valid_initial_state():
    academy = HeroAcademy()
    for lesson in academy.list_lessons():
        assert len(lesson.initial_board) > 0
        assert "white" in lesson.initial_board
        assert "black" in lesson.initial_board
        assert len(lesson.solution_moves) > 0
