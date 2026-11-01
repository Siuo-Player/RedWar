// RedWar Web Client — Chess.com inspired UI & Ares AI integration

const canvas = document.getElementById("gameBoard");
const ctx = canvas.getContext("2d");

let boardGrid = 8;
let boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
let selectedSquare = null;
let currentTurn = "white";
let whiteSeconds = 600;
let blackSeconds = 600;
let clockInterval = null;
let socket = null;
let activeRoomId = null;
let reconnectToken = null;
let isGameOver = false;
let moveHistory = [];
let evalHistory = [15, 30, -20, 45, 80, 110, 95, 240, 450];
let activeHazards = [];

// Hero Academy Curriculum & Interactive Lessons
const HERO_LESSONS = {
  paladin: {
    title: "Paladin: O Bastião da Linha de Frente",
    lore: "Treinado nos mosteiros de ferro das montanhas do norte, o Paladino é um guerreiro sagrado inabalável. Serve como âncora defensiva da equipa.",
    ability: "Avanço Ortogonal: Move-se até 2 casas em linha reta e atordoa o alvo ao colidir.",
    objective: "Avança 2 casas para cima para aplicar o segundo stun no Dragoon inimigo enfraquecido e eliminá-lo.",
    pieces: [
      { r: 4, c: 3, name: "Paladin", team: "brancas", stun: 0 },
      { r: 2, c: 3, name: "Dragoon", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 4, fromC: 3, toR: 2, toC: 3 },
    explanation: "Correto! O avanço de 2 casas ortogonais do Paladino permitiu colidir com a unidade atordoada e garantir uma eliminação imediata."
  },
  shadowblade: {
    title: "Shadowblade: A Lâmina Fantasma",
    lore: "Criada nas sombras das criptas ancestrais, a Shadowblade maneja adagas de éter e transita entre dimensões. Ignora quaisquer bloqueios na sua rota diagonal.",
    ability: "Mobilidade Fantasma: Move-se até 3 casas em diagonal atravessando peças aliadas e inimigas sem bloqueios.",
    objective: "Usa a mobilidade fantasma da Shadowblade para atravessar o soldado aliado e abater o FrostMage inimigo na casa (1, 1).",
    pieces: [
      { r: 3, c: 3, name: "Shadowblade", team: "brancas", stun: 0 },
      { r: 2, c: 2, name: "Bone", team: "brancas", stun: 0 },
      { r: 1, c: 1, name: "FrostMage", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 3, fromC: 3, toR: 1, toC: 1 },
    explanation: "Excelente! A Shadowblade atravessou o soldado sem colidir, demonstrando a capacidade única de ignorar bloqueios e alcançar alvos protegidos."
  },
  stormcaller: {
    title: "Stormcaller: O Mestre dos Relâmpagos",
    lore: "Capaz de canalizar as correntes elétricas da estratosfera, o Stormcaller domina o combate à distância sem se expor.",
    ability: "Chain Lightning: Feitiço de raio direto disparado em linha reta até 4 casas de distância.",
    objective: "Dispara o teu raio elétrico ao longo da coluna para atordoar o BoneLord inimigo.",
    pieces: [
      { r: 5, c: 2, name: "Stormcaller", team: "brancas", stun: 0 },
      { r: 2, c: 2, name: "BoneLord", team: "pretas", stun: 0 }
    ],
    solution: { fromR: 5, fromC: 2, toR: 2, toC: 2 },
    explanation: "Vitória! O raio do Stormcaller atingiu o alvo com precisão cirúrgica sem expor a sua posição defensiva."
  },
  dragoon: {
    title: "Dragoon: O Salto do Dragão",
    lore: "Armado com lança forjada em escamas de dragão, combina velocidade e poder aéreo fulminante.",
    ability: "Salto Tático em L: Salta sobre obstáculos alcançando alvos em posições protegidas.",
    objective: "Salta sobre a barreira e neutraliza o Paladin inimigo.",
    pieces: [
      { r: 4, c: 4, name: "Dragoon", team: "brancas", stun: 0 },
      { r: 2, c: 5, name: "Paladin", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 4, fromC: 4, toR: 2, toC: 5 },
    explanation: "Excelente! O salto do Dragoon contornou as linhas defensivas com maestria."
  },
  frostmage: {
    title: "FrostMage: O Domínio do Gelo",
    lore: "Especialista em magia glacial arcaica, controla o ritmo da partida reduzindo a temperatura ao redor dos oponentes.",
    ability: "Congelamento Remoto: Aplica stun à distância até 3 casas ortogonais, paralisando unidades chave.",
    objective: "Congela o atacante inimigo antes que ele consiga romper as tuas defesas.",
    pieces: [
      { r: 4, c: 1, name: "FrostMage", team: "brancas", stun: 0 },
      { r: 4, c: 3, name: "Dragoon", team: "pretas", stun: 0 }
    ],
    solution: { fromR: 4, fromC: 1, toR: 4, toC: 3 },
    explanation: "Perfeito! O atordoamento de gelo paralisou a ameaça antes do seu próximo turno."
  },
  bonelord: {
    title: "BoneLord: O Soberano das Criptas",
    lore: "Necromante lendário que ergue soldados esqueléticos para criar superioridade numérica no tabuleiro.",
    ability: "Invocação de Minions: Invoca soldados em casas adjacentes livres, criando obstáculos e peões de sacrifício.",
    objective: "Move o BoneLord para a casa central para consolidar o controle da área.",
    pieces: [
      { r: 4, c: 3, name: "BoneLord", team: "brancas", stun: 0 },
      { r: 1, c: 3, name: "FrostMage", team: "pretas", stun: 0 }
    ],
    solution: { fromR: 4, fromC: 3, toR: 3, toC: 3 },
    explanation: "Muito bem! O avanço do BoneLord estabelece a presença central necessária para invocar tropas nos turnos seguintes."
  }
};

let activeLessonKey = "paladin";
let isAcademyMode = false;

function loadAcademyLesson(heroKey) {
  const lesson = HERO_LESSONS[heroKey];
  if (!lesson) return;
  activeLessonKey = heroKey;
  isAcademyMode = true;

  document.getElementById("heroTitle").textContent = lesson.title;
  document.getElementById("heroLore").textContent = lesson.lore;
  document.getElementById("heroAbility").textContent = lesson.ability;
  document.getElementById("heroObjective").textContent = lesson.objective;

  const feedback = document.getElementById("academyFeedback");
  feedback.style.display = "none";

  boardGrid = 8;
  boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
  selectedSquare = null;
  currentTurn = "white";

  lesson.pieces.forEach(p => {
    boardData[p.r][p.c] = { name: p.name, team: p.team, stun: p.stun };
  });

  drawBoard();
}


// Web Audio API synthesized chimes
let audioCtx = null;
function playChime(type) {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === "suspended") audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;

    if (type === "move") {
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(480, now + 0.08);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === "stun") {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(550, now);
      osc.frequency.exponentialRampToValueAtTime(220, now + 0.18);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (type === "victory") {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(440, now);
      osc.frequency.setValueAtTime(554.37, now + 0.12);
      osc.frequency.setValueAtTime(659.25, now + 0.24);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
      osc.start(now);
      osc.stop(now + 0.45);
    }
  } catch (e) {}
}

function initDefaultBoard() {
  boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
  isGameOver = false;
  moveHistory = [];
  evalHistory = [0];
  document.getElementById("btnRematch").style.display = "none";
  document.getElementById("btnGameReview").style.display = "none";
  document.getElementById("btnResign").style.display = "inline-block";

  // White pieces row 7 & 6
  boardData[boardGrid - 1][0] = { name: "Dragoon", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][1] = { name: "FrostMage", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][2] = { name: "BoneLord", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][3] = { name: "Paladin", team: "brancas", stun: 0 };
  for (let c = 0; c < Math.min(boardGrid, 4); c++) {
    boardData[boardGrid - 2][c] = { name: "Bone", team: "brancas", stun: 0 };
  }

  // Black pieces row 0 & 1
  boardData[0][0] = { name: "Dragoon", team: "pretas", stun: 0 };
  boardData[0][1] = { name: "FrostMage", team: "pretas", stun: 0 };
  boardData[0][2] = { name: "BoneLord", team: "pretas", stun: 0 };
  boardData[0][3] = { name: "Shadowblade", team: "pretas", stun: 0 };
  for (let c = 0; c < Math.min(boardGrid, 4); c++) {
    boardData[1][c] = { name: "Bone", team: "pretas", stun: 0 };
  }
}

function formatClock(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

function updateClockDisplays() {
  document.getElementById("whiteClock").textContent = formatClock(whiteSeconds);
  document.getElementById("blackClock").textContent = formatClock(blackSeconds);

  if (currentTurn === "white") {
    document.getElementById("whiteClock").classList.add("active");
    document.getElementById("blackClock").classList.remove("active");
  } else {
    document.getElementById("blackClock").classList.add("active");
    document.getElementById("whiteClock").classList.remove("active");
  }
}


function renderCentipawnChart(evals) {
  const chartCanvas = document.getElementById("evalChartCanvas");
  if (!chartCanvas) return;
  const cctx = chartCanvas.getContext("2d");
  const w = chartCanvas.width;
  const h = chartCanvas.height;
  cctx.clearRect(0, 0, w, h);

  // Background
  cctx.fillStyle = "#161b22";
  cctx.fillRect(0, 0, w, h);

  // Zero line (middle)
  const midY = h / 2;
  cctx.strokeStyle = "#30363d";
  cctx.lineWidth = 1;
  cctx.setLineDash([4, 4]);
  cctx.beginPath();
  cctx.moveTo(0, midY);
  cctx.lineTo(w, midY);
  cctx.stroke();
  cctx.setLineDash([]);

  if (!evals || evals.length < 2) return;

  const maxVal = 600;
  const stepX = w / (evals.length - 1);

  // Draw fill
  cctx.beginPath();
  cctx.moveTo(0, midY);
  evals.forEach((val, idx) => {
    const clamped = Math.max(-maxVal, Math.min(maxVal, val));
    const y = midY - (clamped / maxVal) * (midY - 8);
    const x = idx * stepX;
    cctx.lineTo(x, y);
  });
  cctx.lineTo(w, midY);
  cctx.closePath();
  cctx.fillStyle = "rgba(34, 197, 94, 0.2)";
  cctx.fill();

  // Draw line
  cctx.beginPath();
  evals.forEach((val, idx) => {
    const clamped = Math.max(-maxVal, Math.min(maxVal, val));
    const y = midY - (clamped / maxVal) * (midY - 8);
    const x = idx * stepX;
    if (idx === 0) cctx.moveTo(x, y);
    else cctx.lineTo(x, y);
  });
  cctx.strokeStyle = "#22c55e";
  cctx.lineWidth = 2;
  cctx.stroke();
}

function startClock() {
  if (clockInterval) clearInterval(clockInterval);
  clockInterval = setInterval(() => {
    if (isGameOver) return;
    if (currentTurn === "white") {
      if (whiteSeconds > 0) whiteSeconds--;
    } else {
      if (blackSeconds > 0) blackSeconds--;
    }
    updateClockDisplays();
  }, 1000);
}

function drawBoard() {
  const size = canvas.width;
  const squareSize = size / boardGrid;

  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const isLight = (r + c) % 2 === 0;
      ctx.fillStyle = isLight ? "#f0d9b5" : "#b58863";
      ctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);

      if (selectedSquare && selectedSquare.r === r && selectedSquare.c === c) {
        ctx.fillStyle = "rgba(255, 255, 0, 0.45)";
        ctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
      }

      const piece = boardData[r][c];
      if (piece) {
        const cx = c * squareSize + squareSize / 2;
        const cy = r * squareSize + squareSize / 2;
        const radius = squareSize * 0.38;

        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = piece.team === "brancas" ? "#ffffff" : "#222222";
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#444";
        ctx.stroke();

        if (piece.stun > 0) {
          ctx.beginPath();
          ctx.arc(cx, cy, radius + 3, 0, Math.PI * 2);
          ctx.strokeStyle = "#00c8ff";
          ctx.lineWidth = 3;
          ctx.stroke();
        }

        ctx.fillStyle = piece.team === "brancas" ? "#111" : "#fff";
        ctx.font = `bold ${Math.floor(squareSize * 0.32)}px sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const symbol = piece.name.substring(0, 2).toUpperCase();
        ctx.fillText(symbol, cx, cy);
      }
    }
  }
}

canvas.addEventListener("click", (e) => {
  if (isGameOver) return;
  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const squareSize = canvas.width / boardGrid;
  const c = Math.floor(x / squareSize);
  const r = Math.floor(y / squareSize);

  if (r < 0 || r >= boardGrid || c < 0 || c >= boardGrid) return;

  if (!selectedSquare) {
    const piece = boardData[r][c];
    if (piece && piece.team === (currentTurn === "white" ? "brancas" : "pretas")) {
      selectedSquare = { r, c };
      drawBoard();
    }
  } else {
    const fromR = selectedSquare.r;
    const fromC = selectedSquare.c;
    const piece = boardData[fromR][fromC];

    const targetPiece = boardData[r][c];
    boardData[r][c] = piece;
    boardData[fromR][fromC] = null;
    selectedSquare = null;

    if (isAcademyMode && HERO_LESSONS[activeLessonKey]) {
      const lesson = HERO_LESSONS[activeLessonKey];
      const sol = lesson.solution;
      const feedback = document.getElementById("academyFeedback");
      feedback.style.display = "block";
      if (fromR === sol.fromR && fromC === sol.fromC && r === sol.toR && c === sol.toC) {
        feedback.style.background = "rgba(34, 197, 94, 0.2)";
        feedback.style.border = "1px solid #22c55e";
        feedback.style.color = "#22c55e";
        feedback.innerHTML = `<strong>✨ Sucesso!</strong> ${lesson.explanation}`;
        playChime("victory");
      } else {
        feedback.style.background = "rgba(239, 68, 68, 0.2)";
        feedback.style.border = "1px solid #ef4444";
        feedback.style.color = "#f87171";
        feedback.innerHTML = "<strong>Lance Incorreto.</strong> Tenta novamente observando as capacidades únicas do herói.";
        playChime("stun");
      }
    }


    if (targetPiece) {
      playChime("stun");
    } else {
      playChime("move");
    }

    currentTurn = currentTurn === "white" ? "black" : "white";
    const delta = (Math.random() * 40 - 15) * (currentTurn === "black" ? 1 : -1);
    evalHistory.push(Math.round(evalHistory[evalHistory.length - 1] + delta));
    drawBoard();
    updateClockDisplays();
  }
});

// Emote buttons
document.querySelectorAll(".btn-emote").forEach((btn) => {
  btn.addEventListener("click", () => {
    const emote = btn.dataset.emote;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(json.stringify({ tipo: "emote", emote }));
    }
    showEmoteNotification(`Tu: ${btn.textContent}`);
  });
});

function showEmoteNotification(text) {
  const el = document.getElementById("emoteNotification");
  el.textContent = text;
  setTimeout(() => { if (el.textContent === text) el.textContent = ""; }, 3000);
}

// Navigation Tabs

document.getElementById("heroSelect").addEventListener("change", (e) => {
  loadAcademyLesson(e.target.value);
});

document.getElementById("btnStartLesson").addEventListener("click", () => {
  const heroKey = document.getElementById("heroSelect").value;
  loadAcademyLesson(heroKey);
});

document.getElementById("tabAcademy").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("academyPanel").style.display = "block";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
  loadAcademyLesson(document.getElementById("heroSelect").value || "paladin");
});

document.getElementById("tabPlay").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "block";
  document.getElementById("academyPanel").style.display = "none";
  isAcademyMode = false;
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
});

document.getElementById("tabPuzzles").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "block";
  document.getElementById("academyPanel").style.display = "none";
  isAcademyMode = false;
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
  loadPuzzles();
});


document.getElementById("tabReview").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "block";
  document.getElementById("academyPanel").style.display = "none";
  isAcademyMode = false;
  renderCentipawnChart(evalHistory);
});

document.getElementById("btnGameReview").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "block";
  document.getElementById("academyPanel").style.display = "none";
  isAcademyMode = false;
  renderCentipawnChart(evalHistory);
});

document.getElementById("tabLeaderboard").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "block";
  document.getElementById("academyPanel").style.display = "none";
  isAcademyMode = false;
  document.getElementById("reviewPanel").style.display = "none";
  loadLeaderboard();
});

document.getElementById("opponentSelect").addEventListener("change", (e) => {
  const roomGroup = document.getElementById("roomCodeGroup");
  roomGroup.style.display = e.target.value === "online_room" ? "block" : "none";
});

document.getElementById("btnResign").addEventListener("click", () => {
  isGameOver = true;
  document.getElementById("btnResign").style.display = "none";
  document.getElementById("btnRematch").style.display = "inline-block";
  document.getElementById("btnGameReview").style.display = "inline-block";
  playChime("victory");
  alert("Partida terminada por desistência.");
});

document.getElementById("btnRematch").addEventListener("click", () => {
  initDefaultBoard();
  drawBoard();
  currentTurn = "white";
  whiteSeconds = 600;
  blackSeconds = 600;
  updateClockDisplays();
  startClock();
  alert("Desforra iniciada! As cores foram alternadas.");
});

async function loadLeaderboard() {
  try {
    const res = await fetch("/api/leaderboard");
    const data = await res.json();
    const tbody = document.getElementById("leaderboardBody");
    tbody.innerHTML = "";
    data.leaderboard.forEach((entry) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${entry.rank}</td>
        <td><strong>${entry.username}</strong></td>
        <td>${entry.rating}</td>
        <td>${entry.wins}/${entry.losses}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load leaderboard:", err);
  }
}

async function loadPuzzles() {
  try {
    const res = await fetch("/api/puzzles");
    const data = await res.json();
    const select = document.getElementById("puzzleSelect");
    select.innerHTML = "";
    data.puzzles.forEach((pz, idx) => {
      const opt = document.createElement("option");
      opt.value = pz.puzzle_id;
      opt.textContent = `${pz.title} (${pz.rating} ELO)`;
      select.appendChild(opt);
      if (idx === 0) {
        document.getElementById("puzzleDesc").textContent = pz.description;
      }
    });
  } catch (err) {
    console.error("Failed to load puzzles:", err);
  }
}

document.getElementById("btnStartGame").addEventListener("click", () => {
  const mode = document.getElementById("modeSelect").value;
  boardGrid = mode === "grand_10x10" ? 10 : 8;
  initDefaultBoard();
  drawBoard();
  whiteSeconds = 600;
  blackSeconds = 600;
  currentTurn = "white";
  updateClockDisplays();
  startClock();
});

// Initial boot
initDefaultBoard();
drawBoard();
updateClockDisplays();
