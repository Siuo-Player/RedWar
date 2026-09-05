from tools.replay.interaction_state import (
    InteractionContext,
    InteractionState,
    derive_interaction_state,
)


def test_interaction_state_baseline_progression():
    assert derive_interaction_state(InteractionContext()) is InteractionState.IDLE
    assert derive_interaction_state(
        InteractionContext(selected_hero=(6, 0))
    ) is InteractionState.SELECTED_HERO
    assert derive_interaction_state(
        InteractionContext(selected_hero=(6, 0), hovered_cell=(5, 0))
    ) is InteractionState.HOVERED_CELL
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0), hovered_cell=(5, 0), destination=(5, 0)
        )
    ) is InteractionState.SELECTED_DESTINATION
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0),
            hovered_cell=(5, 0),
            destination=(5, 0),
            action_count=2,
        )
    ) is InteractionState.ACTION_CHOICE
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0),
            destination=(5, 0),
            action_count=1,
            confirmation_required=True,
        )
    ) is InteractionState.ACTION_CONFIRMATION


def test_terminal_modes_take_precedence_over_transient_context():
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0),
            destination=(5, 0),
            action_count=2,
            game_over=True,
        )
    ) is InteractionState.GAME_OVER
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0),
            destination=(5, 0),
            enemy_turn=True,
        )
    ) is InteractionState.ENEMY_TURN
    assert derive_interaction_state(
        InteractionContext(
            selected_hero=(6, 0),
            destination=(5, 0),
            game_over=True,
            enemy_turn=True,
            replay_analysis=True,
        )
    ) is InteractionState.REPLAY_ANALYSIS


def test_context_is_immutable():
    context = InteractionContext(selected_hero=(6, 0))
    assert context.selected_hero == (6, 0)
    try:
        context.selected_hero = (5, 0)  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError("InteractionContext must remain immutable")
