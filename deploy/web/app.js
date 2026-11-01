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

// Initial starter setup
function initDefaultBoard() {
  boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
  // White pieces row 7 & 6
  boardData[boardGrid - 1][0] = { name: "Dragoon", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][1] = { name: "FrostMage", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][2] = { name: "BoneLord", team: "brancas", stun: 0 };
  for (let c = 0; c < Math.min(boardGrid, 4); c++) {
    boardData[boardGrid - 2][c] = { name: "Bone", team: "brancas", stun: 0 };
  }

  // Black pieces row 0 & 1
  boardData[0][0] = { name: "Dragoon", team: "pretas", stun: 0 };
  boardData[0][1] = { name: "FrostMage", team: "pretas", stun: 0 };
  boardData[0][2] = { name: "BoneLord", team: "pretas", stun: 0 };
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

function startClock() {
  if (clockInterval) clearInterval(clockInterval);
  clockInterval = setInterval(() => {
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

      // Selected highlight
      if (selectedSquare && selectedSquare.r === r && selectedSquare.c === c) {
        ctx.fillStyle = "rgba(255, 255, 0, 0.45)";
        ctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
      }

      // Piece rendering
      const piece = boardData[r][c];
      if (piece) {
        const cx = c * squareSize + squareSize / 2;
        const cy = r * squareSize + squareSize / 2;
        const radius = squareSize * 0.4;

        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = piece.team === "brancas" ? "#ffffff" : "#222222";
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#444";
        ctx.stroke();

        // Stun aura
        if (piece.stun > 0) {
          ctx.beginPath();
          ctx.arc(cx, cy, radius + 3, 0, Math.PI * 2);
          ctx.strokeStyle = "#00c8ff";
          ctx.lineWidth = 3;
          ctx.stroke();
        }

        // Piece symbol
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
    // Attempt move
    const fromR = selectedSquare.r;
    const fromC = selectedSquare.c;
    const piece = boardData[fromR][fromC];

    boardData[r][c] = piece;
    boardData[fromR][fromC] = null;
    selectedSquare = null;

    currentTurn = currentTurn === "white" ? "black" : "white";
    drawBoard();
    updateClockDisplays();
  }
});

// Navigation Tabs
document.getElementById("tabPlay").addEventListener("click", () => {
  document.getElementById("playPanel").style.display = "block";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
});

document.getElementById("tabPuzzles").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "block";
  document.getElementById("leaderboardPanel").style.display = "none";
  loadPuzzles();
});

document.getElementById("tabLeaderboard").addEventListener("click", async () => {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "block";
  loadLeaderboard();
});

document.getElementById("opponentSelect").addEventListener("change", (e) => {
  const roomGroup = document.getElementById("roomCodeGroup");
  roomGroup.style.display = e.target.value === "online_room" ? "block" : "none";
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
