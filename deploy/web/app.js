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
document.getElementById("tabPlay").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "block";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
});

document.getElementById("tabPuzzles").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "block";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
  loadPuzzles();
});


document.getElementById("tabReview").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "block";
  renderCentipawnChart(evalHistory);
});

document.getElementById("btnGameReview").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "block";
  renderCentipawnChart(evalHistory);
});

document.getElementById("tabLeaderboard").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "block";
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
