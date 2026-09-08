from ai.evaluator import avaliador_mestre

from engine.legal_actions import legal_actions, to_legacy_dicts


def get_all_moves_for_analysis(gs):
    """Return the complete legal action space in the UI-compatible dict shape."""
    return to_legacy_dicts(legal_actions(gs))


def _action_sort_key(action):
    """Stable tie-break key so equal evaluations never depend on randomness."""
    return (
        str(action.get("type", "")),
        tuple(action.get("start", ())),
        tuple(action.get("end", ())),
        str(action.get("spell_name") or ""),
        str(action.get("spawn_name") or ""),
        tuple(tuple(position) for position in action.get("area", ())),
    )


def analisar_posicao_continuamente(gs, max_depth=6):
    """Evaluate the complete legal action space at each analysis iteration.

    ``max_depth`` is retained for UI/API compatibility. This routine is still a
    one-ply evaluator; the previous implementation incorrectly called this
    iterative deepening while also injecting random tie-breaking noise.
    """
    acoes = get_all_moves_for_analysis(gs)
    if not acoes:
        yield 0, []
        return

    for action in acoes:
        action["score"] = 0

    for depth in range(1, max_depth + 1):
        for action in acoes:
            gs_clone = gs.fast_clone()
            gs_clone.execute_action(action)
            action["score"] = -avaliador_mestre(gs_clone)

        acoes.sort(
            key=lambda action: (-action["score"], _action_sort_key(action))
        )
        yield depth, acoes[:5]
