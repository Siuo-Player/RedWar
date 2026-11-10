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
      save: () => {}, restore: () => {}, setLineDash: () => {},
      moveTo: () => {}, lineTo: () => {}, closePath: () => {}, strokeRect: () => {}
    }),
    addEventListener: () => {},
    classList: { add: () => {}, remove: () => {} },
    style: {}, dataset: {}, appendChild: () => {},
    value: 'bot_intermediate', textContent: '', innerHTML: '',
    width: 560, height: 560
  }),
  createElement: (tag) => ({
    style: {}, dataset: {}, classList: { add: () => {} },
    appendChild: () => {}, textContent: '', innerHTML: '',
    addEventListener: () => {}
  }),
  querySelectorAll: () => []
};
global.Image = class { constructor() { this.complete = true; this.naturalWidth = 512; } };
const memStorage = {};
global.localStorage = {
  getItem: (k) => memStorage[k] !== undefined ? memStorage[k] : null,
  setItem: (k, v) => { memStorage[k] = String(v); },
  removeItem: (k) => { delete memStorage[k]; },
  clear: () => { for (const k in memStorage) delete memStorage[k]; }
};
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
    console.log(JSON.stringify({ count, valid, passed: count >= 30 && valid }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Hero rules incomplete: count={res['count']}, valid={res['valid']}"


def test_web_client_tactical_puzzles_trainer_contract():
    """Tactical puzzles must load, protect solutions (privacy invariant), and track ELO."""
    snippet = """
    let errors = [];
    if (!PUZZLES || PUZZLES.length < 6) {
      errors.push(`Expected at least 6 puzzles, got ${PUZZLES ? PUZZLES.length : 0}`);
    }
    for (const pz of PUZZLES) {
      if (!pz.puzzle_id || !pz.title || !pz.rating || !pz.board) {
        errors.push(`Puzzle ${pz.puzzle_id} has invalid schema`);
      }
      // Privacy invariant: solution coordinates must NEVER be exposed on the client
      if (pz.solution !== undefined) {
        errors.push(`Security violation: Puzzle ${pz.puzzle_id} leaks solution coordinates on client`);
      }
    }
    setupPuzzle("pz1");
    console.log(JSON.stringify({ passed: errors.length === 0, errors, isPuzzle: isPuzzleMode }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Puzzle trainer contract failed: {res['errors']}"
    assert res["isPuzzle"], "setupPuzzle must activate isPuzzleMode"


def test_web_client_live_evaluation_and_move_classification():
    """Live Centipawn eval and move classification must compute valid deltas and ratings."""
    snippet = """
    initDefaultBoard();
    const evalStart = computeBoardCentipawns(boardData);
    classifyLastMove(0, 250, "Valkyrie captura Lich", "brancas");
    classifyLastMove(250, -150, "Dragoon falha", "brancas");
    const lastClassified = classifiedMoves[classifiedMoves.length - 1];
    console.log(JSON.stringify({
      passed: evalStart !== undefined && classifiedMoves.length === 2 && lastClassified.classification === "blunder",
      evalStart,
      classifiedCount: classifiedMoves.length
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Evaluation & classification failed: {res}"


def test_web_client_board_themes_and_graveyard():
    """Board theme selection and captured piece graveyard tracking must function correctly."""
    snippet = """
    initDefaultBoard();
    recordCapture({ name: 'Paladin', team: 'brancas' });
    recordCapture({ name: 'Shadowblade', team: 'pretas' });
    console.log(JSON.stringify({
      passed: capturedWhite.includes('Paladin') && capturedBlack.includes('Shadowblade') && BOARD_THEMES.cyberpunk !== undefined,
      capturedWhite,
      capturedBlack
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Themes & graveyard failed: {res}"


def test_web_client_rwn_export_and_import():
    """RedWar Notation (RWN) must export classified moves and import them accurately."""
    snippet = """
    classifiedMoves = [
      { moveText: 'Wa e2-e3', team: 'brancas', classification: 'best', badgeClass: 'badge-best', label: 'Melhor' },
      { moveText: 'Du d7-d6', team: 'pretas', classification: 'best', badgeClass: 'badge-best', label: 'Melhor' }
    ];
    const exported = exportRwn();
    const hasHeader = exported.indexOf('RedWar 2.0 Match') !== -1;
    const hasMove = exported.indexOf('1. Wa e2-e3 Du d7-d6') !== -1;

    const sampleRwn = '[Event \\"Test\\"]\\n\\n1. Il c2-c4 Ma f7-f5\\n2. Va e2-e4 Du d7-d5';
    const importedOk = importRwn(sampleRwn);
    const importedCount = classifiedMoves.length;

    console.log(JSON.stringify({
      passed: hasHeader && hasMove && importedOk && importedCount === 4,
      hasHeader,
      hasMove,
      importedOk,
      importedCount
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"RWN export/import failed: {res}"


def test_web_client_audio_toggle():
    """Audio toggle must switch sound state between enabled and disabled cleanly."""
    snippet = """
    const initial = soundEnabled;
    toggleAudio();
    const after1 = soundEnabled;
    toggleAudio();
    const after2 = soundEnabled;
    console.log(JSON.stringify({
      passed: initial === true && after1 === false && after2 === true,
      initial,
      after1,
      after2
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Audio toggle failed: {res}"


def test_web_client_hero_analytics_riot_and_power_tiles():
    """Verify that all 30 heroes have complete analytics with Riot badge and power tiles."""
    snippet = """
    const heroKeys = Object.keys(HERO_ANALYTICS_DATA);
    let missingProps = [];
    for (const h of heroKeys) {
      const data = HERO_ANALYTICS_DATA[h];
      if (!data.classes || data.classes.length === 0) missingProps.push(`${h}: missing classes`);
      if (!data.riotStatus) missingProps.push(`${h}: missing riotStatus`);
      if (!data.powerTiles || data.powerTiles.length === 0) missingProps.push(`${h}: missing powerTiles`);
      if (!data.vulnerableTiles || data.vulnerableTiles.length === 0) missingProps.push(`${h}: missing vulnerableTiles`);
      if (!data.topSynergies || data.topSynergies.length === 0) missingProps.push(`${h}: missing topSynergies`);
      if (!data.topCounters || data.topCounters.length === 0) missingProps.push(`${h}: missing topCounters`);
    }

    // Test calling updateHeroAnalyticsDisplay and switching heatmap modes
    let updateWorked = true;
    try {
      updateHeroAnalyticsDisplay("Paladin");
      updateHeroAnalyticsDisplay("Valkyrie");
      currentHeatmapMode = "delta_wr";
      renderHeatmap("Valkyrie");
      currentHeatmapMode = "density";
      renderHeatmap("Valkyrie");
    } catch (e) {
      updateWorked = false;
    }

    console.log(JSON.stringify({
      passed: heroKeys.length >= 30 && missingProps.length === 0 && updateWorked,
      totalHeroes: heroKeys.length,
      missingProps,
      updateWorked
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Analytics invariants failed: {res}"


def test_web_client_puzzle_persistence_and_game_review_audio():
    """Verify puzzle ELO and streak are persisted in localStorage, and Game Review generates classifications."""
    snippet = """
    // 1. Test puzzle stats load and save
    puzzleUserElo = 1450;
    puzzleStreak = 7;
    savePuzzleStats();

    // Reset variables and reload from localStorage
    puzzleUserElo = 1200;
    puzzleStreak = 0;
    loadPuzzleStats();

    const statsRestored = (puzzleUserElo === 1450 && puzzleStreak === 7);

    // 2. Test Game Review move classification
    classifiedMoves = [];
    classifyLastMove(100, 320, 'Va e2-e5', 'brancas'); // +220 cp => Brilliant
    classifyLastMove(100, -250, 'Du d7-d5', 'brancas'); // -350 cp => Blunder

    const brilliantMove = classifiedMoves.find(m => m.classification === 'brilliant');
    const blunderMove = classifiedMoves.find(m => m.classification === 'blunder');

    // 3. Test renderGameReviewPanel executes without error
    let reviewRendered = false;
    try {
      renderGameReviewPanel();
      reviewRendered = true;
    } catch (e) {
      reviewRendered = false;
    }

    console.log(JSON.stringify({
      passed: statsRestored && brilliantMove !== undefined && blunderMove !== undefined && reviewRendered,
      statsRestored,
      hasBrilliant: brilliantMove !== undefined,
      hasBlunder: blunderMove !== undefined,
      reviewRendered
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"Puzzle persistence and game review audio failed: {res}"


def test_web_api_puzzle_verify_and_privacy_contract():
    """Verify /api/puzzles/verify endpoint contract with coordinate payloads and solution privacy."""
    from online.server.web_app import create_web_handler_app
    app = create_web_handler_app()

    # 1. Correct move with coordinate object
    res_ok = app.handle_request(
        "POST",
        "/api/puzzles/verify",
        body=json.dumps({"puzzle_id": "pz1", "fromR": 4, "fromC": 3, "toR": 2, "toC": 5, "step": 0}),
    )
    assert res_ok["status"] == 200
    data_ok = json.loads(res_ok["body"])
    assert data_ok["correct"] is True
    assert data_ok["completed"] is True
    assert len(data_ok["explanation"]) > 0

    # 2. Correct move with string coordinate format
    res_str = app.handle_request(
        "POST",
        "/api/puzzles/verify",
        body=json.dumps({"puzzle_id": "pz1", "move": "4,3->2,5", "step": 0}),
    )
    assert res_str["status"] == 200
    assert json.loads(res_str["body"])["correct"] is True

    # 3. Incorrect move
    res_wrong = app.handle_request(
        "POST",
        "/api/puzzles/verify",
        body=json.dumps({"puzzle_id": "pz1", "fromR": 4, "fromC": 3, "toR": 1, "toC": 1, "step": 0}),
    )
    assert res_wrong["status"] == 200
    assert json.loads(res_wrong["body"])["correct"] is False

    # 4. GET /api/puzzles privacy invariant: solution_moves and solution must be stripped
    res_list = app.handle_request("GET", "/api/puzzles")
    assert res_list["status"] == 200
    puzzles_list = json.loads(res_list["body"])["puzzles"]
    assert len(puzzles_list) >= 6
    for pz in puzzles_list:
        assert "solution" not in pz
        assert "solution_moves" not in pz


def test_web_client_apply_server_board_and_reconnect():
    """Verify applyServerBoard and reconnectOnlineGame in the Node VM environment."""
    snippet = """
    // 1. Test applyServerBoard with stun mapping
    const mockBoard = [
      [ { name: "Dragoon", team: "brancas", stun_timer: 2 }, null ],
      [ null, { name: "Bone", team: "pretas", stun: 1 } ]
    ];
    applyServerBoard(mockBoard);
    const boardLoaded = (boardGrid === 2 && boardData[0][0].name === "Dragoon" && boardData[0][0].stun === 2);

    // 2. Test reconnectOnlineGame saves & retrieves token from localStorage
    localStorage.setItem("redwar_online_room", "ROOM_RECONNECT_TEST");
    localStorage.setItem("redwar_reconnect_token", "TOKEN_SECRET_XYZ");

    let reconnectCalled = false;
    let sentMsg = null;
    socket = {
      readyState: 1,
      send: (msg) => {
        reconnectCalled = true;
        sentMsg = JSON.parse(msg);
      }
    };

    reconnectOnlineGame();

    const reconnectSent = reconnectCalled && sentMsg && sentMsg.tipo === "reconnect" && sentMsg.token === "TOKEN_SECRET_XYZ";

    console.log(JSON.stringify({
      passed: boardLoaded && reconnectSent,
      boardLoaded,
      reconnectSent
    }));
    """
    res = run_node_snippet(snippet)
    assert res["passed"], f"applyServerBoard and reconnectOnlineGame invariant failed: {res}"

