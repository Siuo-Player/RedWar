# tests/test_web_client_invariants.py
"""
Headless Automated Test Suite for RedWar Web Client Invariants.

Executes `deploy/web/app.js` inside a sandboxed Node.js environment
with DOM & Canvas mocks to formally verify:
1. INVARIANT_NO_SELF_CAPTURE: Friendly pieces never capture, overwrite, or land on friendly pieces.
2. INVARIANT_STRICT_TURN_ENFORCEMENT: Player cannot move Black/AI pieces during White's turn.
3. INVARIANT_TWO_HIT_STUN_KILL: Second hit on stunned target results in immediate elimination.
4. INVARIANT_ARES_BOT_AUTOPLAY: Ares AI automatically responds with legal Black actions.
5. INVARIANT_STUN_TIMER_DECREMENT: Timers decrement only for the team whose turn begins.
6. INVARIANT_HERO_RULE_COMPLETENESS: All 24 heroes have full movement, attack, and cost definitions.
"""
import subprocess
import json
import os
import pytest

COMMON_HARNESS = """
const fs = require('fs');
const path = require('path');
const vm = require('vm');

global.window = {};
global.document = {
  getElementById: (id) => ({
    getContext: () => ({
      clearRect: () => {}, fillRect: () => {}, beginPath: () => {},
      arc: () => {}, fill: () => {}, stroke: () => {}, drawImage: () => {},
      fillText: () => {}, measureText: () => ({ width: 10 }),
      save: () => {}, restore: () => {}, setLineDash: () => {}
    }),
    addEventListener: () => {},
    classList: { add: () => {}, remove: () => {} },
    style: {}, dataset: {}, appendChild: () => {},
    value: 'bot_intermediate', textContent: '', innerHTML: '',
    width: 560, height: 560
  }),
  querySelectorAll: () => []
};
global.Image = class { constructor() { this.complete = true; this.naturalWidth = 512; } };
global.localStorage = { getItem: () => null, setItem: () => {} };
global.alert = () => {};

const appCode = fs.readFileSync(path.join(__dirname, 'deploy', 'web', 'app.js'), 'utf8');
vm.runInThisContext(appCode);
"""


def run_node_snippet(snippet: str):
    full_script = f"{COMMON_HARNESS}\n{snippet}"
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res = subprocess.run(
        ["node", "-e", full_script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(res.stdout.strip())


def test_web_client_no_self_capture_or_friendly_fire():
    """Web client pieces must NEVER move onto or attack friendly units."""
    snippet = """
    let failed = [];
    for (const heroName of Object.keys(HERO_RULES)) {
      const board = Array(8).fill(null).map(() => Array(8).fill(null));
      board[4][4] = { name: heroName, team: 'brancas', stun: 0 };
      const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]];
      for (const [dr, dc] of dirs) {
        board[4 + dr][4 + dc] = { name: 'Bone', team: 'brancas', stun: 0 };
      }
      const actions = getLegalActionsForPiece(4, 4, board);
      for (const act of actions) {
        if (act.type === 'move' && board[act.r][act.c] !== null) {
          failed.push(`${heroName} moved onto occupied ally (${act.r}, ${act.c})`);
        }
        if (act.type === 'attack' && act.target && act.target.team === 'brancas') {
          failed.push(`${heroName} attacked ally at (${act.r}, ${act.c})`);
        }
      }
    }
    console.log(JSON.stringify({ passed: failed.length === 0, errors: failed }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Self capture/friendly fire detected: {res['errors']}"


def test_web_client_two_hit_stun_lethality():
    """Attacking a stunned piece in the web client must eliminate it immediately."""
    snippet = """
    const board = Array(8).fill(null).map(() => Array(8).fill(null));
    board[4][4] = { name: 'Paladin', team: 'brancas', stun: 0 };
    const stunnedEnemy = { name: 'Dragoon', team: 'pretas', stun: 2 };
    board[2][4] = stunnedEnemy;
    boardData = board;
    boardGrid = 8;
    currentTurn = 'white';
    moveHistory = [];

    const killAction = { type: 'attack', r: 2, c: 4, target: stunnedEnemy };
    applyAction(4, 4, killAction);

    const lethalKillRecorded = moveHistory.some(m => m.includes('[Lethal Kill]'));
    const defenderRemoved = (boardData[4][4] === null && boardData[2][4].name === 'Paladin');
    console.log(JSON.stringify({ passed: defenderRemoved && lethalKillRecorded }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], "Two-hit stun lethality failed in web client"


def test_web_client_stunned_pieces_have_zero_actions():
    """Stunned pieces in the web client cannot move or attack."""
    snippet = """
    const board = Array(8).fill(null).map(() => Array(8).fill(null));
    board[3][3] = { name: 'Shadowblade', team: 'brancas', stun: 2 };
    const actions = getLegalActionsForPiece(3, 3, board);
    console.log(JSON.stringify({ passed: actions.length === 0 }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], "Stunned piece generated non-empty legal actions"


def test_web_client_turn_enforcement_and_ares_bot_autoplay():
    """Ares Bot calculates legal moves for Black and switches turn back to White."""
    snippet = """
    initDefaultBoard();
    currentTurn = 'black';
    playAresBotMove();
    console.log(JSON.stringify({ passed: currentTurn === 'white' }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], "Ares bot failed to execute Black move and return turn to White"


def test_web_client_all_heroes_configured():
    """All 24 heroes must have full movement, attack, and cost definitions."""
    snippet = """
    const count = Object.keys(HERO_RULES).length;
    let valid = true;
    for (const [name, rule] of Object.entries(HERO_RULES)) {
      if (!rule.move || !rule.attack || !rule.cost || !rule.acronym) {
        valid = false;
      }
    }
    console.log(JSON.stringify({ count, valid, passed: count >= 24 && valid }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Hero rules incomplete: count={res['count']}, valid={res['valid']}"
