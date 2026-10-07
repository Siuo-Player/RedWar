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
    """Evaluate the legal action space once and expose compatible depth iterations.

    ``max_depth`` is retained for UI/API compatibility. This routine remains a
    one-ply evaluator, so increasing ``max_depth`` must not repeat the same
    evaluation work. Each requested iteration yields the same deterministically
    ordered top-five analysis for the current position.
    """
    acoes = get_all_moves_for_analysis(gs)
    if not acoes:
        yield 0, []
        return

    if max_depth < 1:
        return

    for action in acoes:
        action["score"] = 0

    for action in acoes:
        gs_clone = gs.fast_clone()
        gs_clone.execute_action(action)
        action["score"] = -avaliador_mestre(gs_clone)

    acoes.sort(
        key=lambda action: (-action["score"], _action_sort_key(action))
    )
    top_actions = acoes[:5]

    for depth in range(1, max_depth + 1):
        yield depth, top_actions
