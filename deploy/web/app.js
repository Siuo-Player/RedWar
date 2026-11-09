// RedWar Web Client — Chess.com Inspired UI, Ares AI Engine & Security Protocol
// Invariants Enforced:
// 1. Strict Turn Enforcement (Player cannot move AI/opponent pieces)
// 2. No Friendly Fire / No Self-Capture (Allies block moves, cannot be attacked)
// 3. Two-Hit Stun Lethality (Attacking a stunned piece eliminates it immediately)
// 4. Zero Blast Radius Security Authentication (Google OIDC, Guest, Dedicated)

const canvas = document.getElementById("gameBoard");
const ctx = canvas.getContext("2d");

let boardGrid = 8;
let boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
let selectedSquare = null;
let currentLegalActions = [];
let currentTurn = "white";
let whiteSeconds = 600;
let blackSeconds = 600;
let clockInterval = null;
let socket = null;
let isGameOver = false;
let moveHistory = [];
let evalHistory = [0];
let isAiThinking = false;

// --- Board Themes ---
var BOARD_THEMES = {
  classic: { light: "#eeeed2", dark: "#769656", name: "Clássico" },
  cyberpunk: { light: "#1e293b", dark: "#0f172a", name: "Cyberpunk" },
  volcanic: { light: "#451a03", dark: "#291003", name: "Arena Vulcânica" },
  glacial: { light: "#dbeafe", dark: "#38bdf8", name: "Templo Glacial" }
};
var currentTheme = "classic";

// --- Graveyard / Captured Pieces Tracking ---
var capturedWhite = [];
var capturedBlack = [];

function recordCapture(piece) {
  if (!piece) return;
  if (piece.team === "brancas") {
    capturedWhite.push(piece.name);
  } else {
    capturedBlack.push(piece.name);
  }
  updateGraveyardsUI();
}

function updateGraveyardsUI() {
  const whiteEl = document.getElementById("whiteGraveyard");
  const blackEl = document.getElementById("blackGraveyard");
  if (whiteEl) {
    whiteEl.innerHTML = capturedWhite.map(name => {
      const acronym = HERO_RULES[name] ? HERO_RULES[name].acronym : name.substring(0, 2);
      return `<span class="graveyard-piece white" title="${name}">${acronym}</span>`;
    }).join("");
  }
  if (blackEl) {
    blackEl.innerHTML = capturedBlack.map(name => {
      const acronym = HERO_RULES[name] ? HERO_RULES[name].acronym : name.substring(0, 2);
      return `<span class="graveyard-piece black" title="${name}">${acronym}</span>`;
    }).join("");
  }
}

// --- Live Centipawn Position Evaluation ---
function computeBoardCentipawns(board) {
  let whiteScore = 0;
  let blackScore = 0;
  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const p = board[r][c];
      if (!p) continue;
      const rule = HERO_RULES[p.name] || { cost: 10 };
      let val = rule.cost * 100;
      if (p.stun > 0) val = Math.round(val * 0.5);
      const centerDist = Math.abs(r - (boardGrid - 1) / 2) + Math.abs(c - (boardGrid - 1) / 2);
      val += Math.round((boardGrid - centerDist) * 8);
      if (p.team === "brancas") whiteScore += val;
      else blackScore += val;
    }
  }
  return whiteScore - blackScore;
}

function updateLiveEvalBar(cp) {
  const fill = document.getElementById("evalBarFill");
  const topLabel = document.getElementById("evalBarLabelTop");
  const bottomLabel = document.getElementById("evalBarLabelBottom");
  if (!fill) return;

  const maxVal = 1000;
  const pct = Math.max(5, Math.min(95, 50 + (cp / maxVal) * 50));
  fill.style.height = `${pct}%`;

  const formatted = (Math.abs(cp) / 100).toFixed(1);
  if (cp > 25) {
    if (bottomLabel) bottomLabel.textContent = `+${formatted}`;
    if (topLabel) topLabel.textContent = "";
  } else if (cp < -25) {
    if (topLabel) topLabel.textContent = `-${formatted}`;
    if (bottomLabel) bottomLabel.textContent = "";
  } else {
    if (bottomLabel) bottomLabel.textContent = "0.0";
    if (topLabel) topLabel.textContent = "";
  }
}

// --- Game Review Move Classification ---
var classifiedMoves = [];

function classifyLastMove(evalBefore, evalAfter, moveText, pieceTeam) {
  const delta = pieceTeam === "brancas" ? (evalAfter - evalBefore) : (evalBefore - evalAfter);
  let classification = "best";
  let badgeClass = "badge-best";
  let label = "Melhor";

  if (delta >= 180) {
    classification = "brilliant";
    badgeClass = "badge-brilliant";
    label = "✨ Brilhante (!!)";
  } else if (delta >= 60) {
    classification = "great";
    badgeClass = "badge-great";
    label = "⭐ Excelente (!)";
  } else if (delta >= -25) {
    classification = "best";
    badgeClass = "badge-best";
    label = "🎯 Melhor";
  } else if (delta >= -75) {
    classification = "good";
    badgeClass = "badge-good";
    label = "👍 Bom";
  } else if (delta >= -160) {
    classification = "inaccuracy";
    badgeClass = "badge-inaccuracy";
    label = "⚠️ Imprecisão (?!)";
  } else if (delta >= -320) {
    classification = "mistake";
    badgeClass = "badge-mistake";
    label = "❓ Erro (?)";
  } else {
    classification = "blunder";
    badgeClass = "badge-blunder";
    label = "💥 Gaffe (??)";
  }

  classifiedMoves.push({
    moveText,
    team: pieceTeam,
    delta,
    classification,
    badgeClass,
    label
  });

  // Sound feedback according to classification
  if (classification === "brilliant") {
    playChime("brilliant");
  } else if (classification === "best" || classification === "great") {
    playChime("best");
  } else if (classification === "blunder") {
    playChime("blunder");
  } else if (classification === "mistake" || classification === "inaccuracy") {
    playChime("mistake");
  }
}

// --- Assets Pre-loading ---
const HERO_ASSET_NAMES = [
  "berserker", "bone", "bonelord", "cleric", "dragoon", "frostmage",
  "geomancer", "ghoul", "hookmaster", "inquisitor", "lich", "nightshade",
  "obelisk", "paladin", "phantom", "pyromancer", "ranger", "sentry",
  "shadowblade", "stonewall", "stormcaller", "templar", "timekeeper", "trickster",
  "valkyrie", "arcanist", "duelist", "warden", "illusionist", "marksman"
];

const PIECE_IMAGES = {};
HERO_ASSET_NAMES.forEach(name => {
  const img = new Image();
  img.src = `assets/${name}.png`;
  img.onload = () => { drawBoard(); };
  PIECE_IMAGES[name] = img;
});

// --- Complete 24 Hero Movement, Attack & Cost Rules (Derived from heroes_config.json) ---
const HERO_RULES = {
  Paladin: {
    move: { type: "orthogonal", steps: 2, ghost: false },
    attack: { type: "orthogonal", steps: 2 },
    cost: 16,
    acronym: "Pa"
  },
  Shadowblade: {
    move: { type: "diagonal", steps: 3, ghost: true },
    attack: { type: "diagonal", steps: 3, ghost: true },
    cost: 18,
    acronym: "Sh"
  },
  Stormcaller: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 4 },
    cost: 17,
    acronym: "St"
  },
  Hookmaster: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 3 },
    cost: 15,
    acronym: "Hk"
  },
  Timekeeper: {
    move: { type: "diagonal", steps: 1, ghost: false },
    attack: { type: "diagonal", steps: 2 },
    cost: 16,
    acronym: "Tk"
  },
  Dragoon: {
    move: { type: "knight" },
    attack: { type: "knight" },
    cost: 18,
    acronym: "Dr"
  },
  FrostMage: {
    move: { type: "diagonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 3, stunOnly: true },
    cost: 16,
    acronym: "Fm"
  },
  BoneLord: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 1 },
    cost: 16,
    acronym: "BL"
  },
  Bone: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 1 },
    cost: 8,
    acronym: "Bo"
  },
  Berserker: {
    move: { type: "adjacent", steps: 1, ghost: false },
    attack: { type: "adjacent", steps: 1 },
    cost: 18,
    acronym: "Be"
  },
  Ranger: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 4 },
    cost: 14,
    acronym: "Ra"
  },
  Pyromancer: {
    move: { type: "diagonal", steps: 2, ghost: false },
    attack: { type: "orthogonal", steps: 2 },
    cost: 16,
    acronym: "Py"
  },
  Phantom: {
    move: { type: "knight" },
    attack: { type: "knight" },
    cost: 5,
    acronym: "Ph"
  },
  Cleric: {
    move: { type: "diagonal", steps: 2, ghost: false },
    attack: { type: "adjacent", steps: 1 },
    cost: 14,
    acronym: "Cl"
  },
  Templar: {
    move: { type: "orthogonal", steps: 2, ghost: false },
    attack: { type: "orthogonal", steps: 2 },
    cost: 15,
    acronym: "Te"
  },
  Inquisitor: {
    move: { type: "adjacent", steps: 1, ghost: false },
    attack: { type: "adjacent", steps: 1 },
    cost: 15,
    acronym: "In"
  },
  Geomancer: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "diagonal", steps: 1 },
    cost: 14,
    acronym: "Ge"
  },
  Lich: {
    move: { type: "diagonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 2 },
    cost: 15,
    acronym: "Li"
  },
  Nightshade: {
    move: { type: "diagonal", steps: 2, ghost: false },
    attack: { type: "adjacent", steps: 1 },
    cost: 14,
    acronym: "Ni"
  },
  Obelisk: {
    move: { type: "none" },
    attack: { type: "orthogonal", steps: 1 },
    cost: 16,
    acronym: "Ob"
  },
  Sentry: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 3 },
    cost: 12,
    acronym: "Se"
  },
  Stonewall: {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 1 },
    cost: 14,
    acronym: "Sw"
  },
  Trickster: {
    move: { type: "knight" },
    attack: { type: "adjacent", steps: 1 },
    cost: 12,
    acronym: "Tr"
  },
  Ghoul: {
    move: { type: "forward_cone", steps: 1 },
    attack: { type: "forward_cone", steps: 1 },
    cost: 5,
    acronym: "Gh"
  },
  Valkyrie: {
    move: { type: "adjacent", steps: 3, ghost: true },
    attack: { type: "orthogonal", steps: 2 },
    cost: 22,
    acronym: "Va"
  },
  Arcanist: {
    move: { type: "diagonal", steps: 2, ghost: false },
    attack: { type: "orthogonal", steps: 3 },
    cost: 23,
    acronym: "Ar"
  },
  Duelist: {
    move: { type: "diagonal", steps: 2, ghost: false },
    attack: { type: "diagonal", steps: 2 },
    cost: 24,
    acronym: "Du"
  },
  Warden: {
    move: { type: "adjacent", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 1 },
    cost: 25,
    acronym: "Wa"
  },
  Illusionist: {
    move: { type: "orthogonal", steps: 2, ghost: false },
    attack: { type: "adjacent", steps: 1 },
    cost: 27,
    acronym: "Il"
  },
  Marksman: {
    move: { type: "adjacent", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 3, ray: true },
    cost: 28,
    acronym: "Ma"
  }
};

// Directions
const ORTHO_DIRS = [[-1, 0], [1, 0], [0, -1], [0, 1]];
const DIAG_DIRS = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
const ADJ_DIRS = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
const KNIGHT_DIRS = [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]];

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
    objective: "Dispara o teu raio elétrico ao longo da coluna para eliminar o BoneLord inimigo atordoado.",
    pieces: [
      { r: 5, c: 2, name: "Stormcaller", team: "brancas", stun: 0 },
      { r: 2, c: 2, name: "BoneLord", team: "pretas", stun: 1 }
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
  },
  valkyrie: {
    title: "Valkyrie: As Asas Celestes",
    lore: "Guerreira celestial com asas translúcidas que plana sobre o campo de batalha. Salta sobre obstáculos e tropas com voo espectral.",
    ability: "Voo Espectral: Move-se até 3 casas (ortogonal ou diagonal) ignorando quaisquer obstáculos terrestres.",
    objective: "Voa sobre a barreira inimiga e desfere o golpe letal no Lich atordoado.",
    pieces: [
      { r: 5, c: 2, name: "Valkyrie", team: "brancas", stun: 0 },
      { r: 4, c: 2, name: "StoneWall", team: "pretas", stun: 0 },
      { r: 3, c: 2, name: "Bone", team: "pretas", stun: 0 },
      { r: 2, c: 2, name: "Lich", team: "pretas", stun: 2 }
    ],
    solution: { fromR: 5, fromC: 2, toR: 2, toC: 2 },
    explanation: "Sensacional! As asas da Valkyrie ignoraram a barreira terrestre e liquidaram o alvo protegido."
  },
  arcanist: {
    title: "Arcanist: A Rajada Rúnica",
    lore: "Mago acadêmico dos círculos rúnicos arcanos. Canaliza rajadas perfurantes em linha reta que eliminam unidades debilitadas.",
    ability: "Rajada Arcana: Ataque ortogonal em raio até 3 casas com impacto mágico direto.",
    objective: "Dispara a rajada arcana ao longo da coluna para eliminar o atacante atordoado.",
    pieces: [
      { r: 5, c: 3, name: "Arcanist", team: "brancas", stun: 0 },
      { r: 2, c: 3, name: "Stormcaller", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 5, fromC: 3, toR: 2, toC: 3 },
    explanation: "Perfeito! O raio arcano percorreu 3 casas e vaporizou o adversário atordoado."
  },
  duelist: {
    title: "Duelist: A Estocada Precisa",
    lore: "Mestre esgrimista das academias reais, domina as diagonais com lâmina leve e contra-ataques fulminantes.",
    ability: "Estocada Diagonal: Move-se e ataca em diagonais até 2 casas com precisão cirúrgica.",
    objective: "Avança em diagonal para trespassar o Berserker debilitado.",
    pieces: [
      { r: 4, c: 2, name: "Duelist", team: "brancas", stun: 0 },
      { r: 2, c: 4, name: "Berserker", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 4, fromC: 2, toR: 2, toC: 4 },
    explanation: "Magnífico! O golpe diagonal cirúrgico finalizou a ameaça sem sofrer retaliação."
  },
  warden: {
    title: "Warden: O Bastião Inabalável",
    lore: "Com escudo de torre e armadura pesada, o Warden ancora a linha de frente e rechaça quaisquer invasores.",
    ability: "Golpe de Escudo: Movimenta-se 1 casa em qualquer direção e desfere golpe ortogonal contundente.",
    objective: "Avança com o escudo e elimina a Nightshade infiltrada.",
    pieces: [
      { r: 3, c: 3, name: "Warden", team: "brancas", stun: 0 },
      { r: 2, c: 3, name: "Nightshade", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 3, fromC: 3, toR: 2, toC: 3 },
    explanation: "Inabalável! O avanço defensivo do Warden conteve a infiltração inimiga com autoridade."
  },
  illusionist: {
    title: "Illusionist: O Mestre dos Espelhos",
    lore: "Manipulador de percepções e transposição tática, controla os eixos ortogonais e ataca em 360 graus a curta distância.",
    ability: "Reflexo Prismático: Movimenta-se até 2 casas ortogonais e ataca 1 casa em qualquer direção adjacente.",
    objective: "Avança 2 casas para o centro e desfere golpe na diagonal adjacente.",
    pieces: [
      { r: 6, c: 3, name: "Illusionist", team: "brancas", stun: 0 },
      { r: 3, c: 4, name: "BoneLord", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 6, fromC: 3, toR: 4, toC: 3 },
    explanation: "Excelente! O avanço de 2 casas ortogonais preparou o golpe letal definitivo."
  },
  marksman: {
    title: "Marksman: A Visada Balística",
    lore: "Atirador de precisão tática, atinge alvos a 3 casas de distância em linha ortogonal limpa.",
    ability: "Disparo de Precisão: Ataque ortogonal linear até 3 casas capaz de eliminar alvos atordoados.",
    objective: "Dispara ao longo da coluna aberta para eliminar o Templar debilitado.",
    pieces: [
      { r: 5, c: 2, name: "Marksman", team: "brancas", stun: 0 },
      { r: 2, c: 2, name: "Templar", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 5, fromC: 2, toR: 2, toC: 2 },
    explanation: "Tiro certeiro! A precisão balística do Marksman eliminou a peça à distância."
  }
};

// Empirical Hero Analytics (Football-style stats & Riot Game Balance Framework)
const HERO_ANALYTICS_DATA = {
  "Paladin": {
    "classes": [
      "Vanguard (Tanque/Âncora)",
      "Disruptor Secundário"
    ],
    "cost": 16,
    "efficiency": "1.04x (Equilibrado)",
    "cir": 1.04,
    "riotStatus": "BALANCED",
    "winRate": "51.2%",
    "presenceRate": "18.5%",
    "radar": {
      "zone": 88,
      "lethality": 62,
      "cc": 74,
      "mobility": 55,
      "surv": 92,
      "endg": 78
    },
    "phases": {
      "opening": 70,
      "midgame": 92,
      "endgame": 84
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        3,
        4
      ],
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        2,
        3
      ],
      [
        2,
        4
      ]
    ],
    "powerTiles": [
      "d5 (+4.2%)",
      "e5 (+4.1%)",
      "d4 (+3.8%)"
    ],
    "vulnerableTiles": [
      "a1 (-6.8%)",
      "h8 (-6.4%)",
      "a8 (-5.9%)"
    ],
    "topSynergies": [
      {
        "hero": "Valkyrie",
        "delta": "+5.2%"
      },
      {
        "hero": "Warden",
        "delta": "+4.1%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-6.4%"
      },
      {
        "hero": "Duelist",
        "delta": "-4.8%"
      }
    ]
  },
  "Shadowblade": {
    "classes": [
      "Striker (Flanqueador/Assassino)",
      "Finalizador Ágil"
    ],
    "cost": 18,
    "efficiency": "1.08x (Equilibrado)",
    "cir": 1.08,
    "riotStatus": "BALANCED",
    "winRate": "52.4%",
    "presenceRate": "21.0%",
    "radar": {
      "zone": 45,
      "lethality": 94,
      "cc": 50,
      "mobility": 96,
      "surv": 65,
      "endg": 90
    },
    "phases": {
      "opening": 60,
      "midgame": 85,
      "endgame": 95
    },
    "heatmapHotspots": [
      [
        1,
        2
      ],
      [
        1,
        5
      ],
      [
        2,
        1
      ],
      [
        2,
        6
      ],
      [
        5,
        2
      ],
      [
        5,
        5
      ]
    ],
    "powerTiles": [
      "c6 (+5.8%)",
      "f6 (+5.5%)",
      "c3 (+4.9%)"
    ],
    "vulnerableTiles": [
      "d4 (-7.1%)",
      "e4 (-6.8%)",
      "d5 (-6.2%)"
    ],
    "topSynergies": [
      {
        "hero": "FrostMage",
        "delta": "+6.1%"
      },
      {
        "hero": "Timekeeper",
        "delta": "+4.8%"
      }
    ],
    "topCounters": [
      {
        "hero": "Paladin",
        "delta": "-7.2%"
      },
      {
        "hero": "Warden",
        "delta": "-5.9%"
      }
    ]
  },
  "Stormcaller": {
    "classes": [
      "Artillery (Artilharia de Longo Alcance)",
      "Controlador Zonal"
    ],
    "cost": 17,
    "efficiency": "0.98x (Equilibrado)",
    "cir": 0.98,
    "riotStatus": "BALANCED",
    "winRate": "49.6%",
    "presenceRate": "16.2%",
    "radar": {
      "zone": 92,
      "lethality": 85,
      "cc": 80,
      "mobility": 40,
      "surv": 58,
      "endg": 75
    },
    "phases": {
      "opening": 85,
      "midgame": 90,
      "endgame": 70
    },
    "heatmapHotspots": [
      [
        6,
        1
      ],
      [
        6,
        2
      ],
      [
        6,
        5
      ],
      [
        6,
        6
      ],
      [
        5,
        3
      ],
      [
        5,
        4
      ]
    ],
    "powerTiles": [
      "b2 (+5.1%)",
      "g2 (+4.9%)",
      "d3 (+4.2%)"
    ],
    "vulnerableTiles": [
      "d5 (-6.5%)",
      "e5 (-6.1%)",
      "c4 (-5.8%)"
    ],
    "topSynergies": [
      {
        "hero": "Warden",
        "delta": "+5.4%"
      },
      {
        "hero": "Paladin",
        "delta": "+4.5%"
      }
    ],
    "topCounters": [
      {
        "hero": "Shadowblade",
        "delta": "-7.8%"
      },
      {
        "hero": "Dragoon",
        "delta": "-6.2%"
      }
    ]
  },
  "Dragoon": {
    "classes": [
      "Striker (Iniciador Móvel)",
      "Saltador Tático"
    ],
    "cost": 18,
    "efficiency": "1.02x (Equilibrado)",
    "cir": 1.02,
    "riotStatus": "BALANCED",
    "winRate": "50.8%",
    "presenceRate": "17.4%",
    "radar": {
      "zone": 68,
      "lethality": 88,
      "cc": 60,
      "mobility": 90,
      "surv": 72,
      "endg": 82
    },
    "phases": {
      "opening": 75,
      "midgame": 88,
      "endgame": 80
    },
    "heatmapHotspots": [
      [
        3,
        2
      ],
      [
        3,
        5
      ],
      [
        4,
        2
      ],
      [
        4,
        5
      ],
      [
        2,
        4
      ]
    ],
    "powerTiles": [
      "c5 (+4.8%)",
      "f5 (+4.6%)",
      "e6 (+4.1%)"
    ],
    "vulnerableTiles": [
      "a1 (-6.2%)",
      "h1 (-5.8%)",
      "a8 (-5.4%)"
    ],
    "topSynergies": [
      {
        "hero": "Valkyrie",
        "delta": "+5.8%"
      },
      {
        "hero": "Stormcaller",
        "delta": "+4.3%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-6.1%"
      },
      {
        "hero": "Paladin",
        "delta": "-5.5%"
      }
    ]
  },
  "FrostMage": {
    "classes": [
      "Disruptor (Controlador de Gelo)",
      "Negação de Área"
    ],
    "cost": 16,
    "efficiency": "1.06x (Equilibrado)",
    "cir": 1.06,
    "riotStatus": "BALANCED",
    "winRate": "51.8%",
    "presenceRate": "19.1%",
    "radar": {
      "zone": 84,
      "lethality": 40,
      "cc": 96,
      "mobility": 45,
      "surv": 64,
      "endg": 85
    },
    "phases": {
      "opening": 80,
      "midgame": 94,
      "endgame": 82
    },
    "heatmapHotspots": [
      [
        4,
        2
      ],
      [
        4,
        5
      ],
      [
        3,
        1
      ],
      [
        3,
        6
      ],
      [
        5,
        3
      ]
    ],
    "powerTiles": [
      "c4 (+5.5%)",
      "f4 (+5.2%)",
      "d3 (+4.7%)"
    ],
    "vulnerableTiles": [
      "b7 (-6.8%)",
      "g7 (-6.3%)",
      "c8 (-5.9%)"
    ],
    "topSynergies": [
      {
        "hero": "Shadowblade",
        "delta": "+6.5%"
      },
      {
        "hero": "Marksman",
        "delta": "+5.7%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-8.2%"
      },
      {
        "hero": "BoneLord",
        "delta": "-6.0%"
      }
    ]
  },
  "BoneLord": {
    "classes": [
      "Summoner (Invocador/Saturação)",
      "Âncora de Retaguarda"
    ],
    "cost": 16,
    "efficiency": "1.01x (Equilibrado)",
    "cir": 1.01,
    "riotStatus": "BALANCED",
    "winRate": "50.2%",
    "presenceRate": "15.8%",
    "radar": {
      "zone": 95,
      "lethality": 50,
      "cc": 62,
      "mobility": 35,
      "surv": 85,
      "endg": 70
    },
    "phases": {
      "opening": 90,
      "midgame": 85,
      "endgame": 65
    },
    "heatmapHotspots": [
      [
        6,
        3
      ],
      [
        6,
        4
      ],
      [
        5,
        2
      ],
      [
        5,
        5
      ]
    ],
    "powerTiles": [
      "d2 (+4.6%)",
      "e2 (+4.4%)",
      "c3 (+3.9%)"
    ],
    "vulnerableTiles": [
      "d6 (-7.0%)",
      "e6 (-6.6%)",
      "f5 (-6.1%)"
    ],
    "topSynergies": [
      {
        "hero": "Lich",
        "delta": "+5.9%"
      },
      {
        "hero": "Bone",
        "delta": "+4.7%"
      }
    ],
    "topCounters": [
      {
        "hero": "Pyromancer",
        "delta": "-7.5%"
      },
      {
        "hero": "Stormcaller",
        "delta": "-6.8%"
      }
    ]
  },
  "Hookmaster": {
    "classes": [
      "Disruptor (Puxador/Reposicionador)",
      "Vanguard Secundário"
    ],
    "cost": 15,
    "efficiency": "1.05x (Equilibrado)",
    "cir": 1.05,
    "riotStatus": "BALANCED",
    "winRate": "51.5%",
    "presenceRate": "17.6%",
    "radar": {
      "zone": 80,
      "lethality": 70,
      "cc": 88,
      "mobility": 50,
      "surv": 80,
      "endg": 78
    },
    "phases": {
      "opening": 72,
      "midgame": 89,
      "endgame": 81
    },
    "heatmapHotspots": [
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        3
      ],
      [
        3,
        4
      ]
    ],
    "powerTiles": [
      "d4 (+5.3%)",
      "e4 (+5.0%)",
      "d5 (+4.6%)"
    ],
    "vulnerableTiles": [
      "a2 (-6.4%)",
      "h2 (-6.1%)",
      "a7 (-5.7%)"
    ],
    "topSynergies": [
      {
        "hero": "Duelist",
        "delta": "+5.6%"
      },
      {
        "hero": "Paladin",
        "delta": "+4.9%"
      }
    ],
    "topCounters": [
      {
        "hero": "Illusionist",
        "delta": "-6.9%"
      },
      {
        "hero": "Marksman",
        "delta": "-5.8%"
      }
    ]
  },
  "Timekeeper": {
    "classes": [
      "Disruptor (Cronomante de Turnos)",
      "Manipulador Temporal"
    ],
    "cost": 16,
    "efficiency": "1.03x (Equilibrado)",
    "cir": 1.03,
    "riotStatus": "BALANCED",
    "winRate": "51.0%",
    "presenceRate": "16.8%",
    "radar": {
      "zone": 75,
      "lethality": 45,
      "cc": 92,
      "mobility": 60,
      "surv": 78,
      "endg": 88
    },
    "phases": {
      "opening": 65,
      "midgame": 86,
      "endgame": 92
    },
    "heatmapHotspots": [
      [
        5,
        3
      ],
      [
        5,
        4
      ],
      [
        4,
        2
      ],
      [
        4,
        5
      ]
    ],
    "powerTiles": [
      "d3 (+4.9%)",
      "e3 (+4.7%)",
      "c4 (+4.2%)"
    ],
    "vulnerableTiles": [
      "d7 (-6.8%)",
      "e7 (-6.4%)",
      "a4 (-5.9%)"
    ],
    "topSynergies": [
      {
        "hero": "Arcanist",
        "delta": "+5.5%"
      },
      {
        "hero": "Valkyrie",
        "delta": "+4.7%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-7.1%"
      },
      {
        "hero": "Shadowblade",
        "delta": "-6.4%"
      }
    ]
  },
  "Ranger": {
    "classes": [
      "Artillery (Atirador Rápido)",
      "Supressor Linear"
    ],
    "cost": 14,
    "efficiency": "0.97x (Equilibrado)",
    "cir": 0.97,
    "riotStatus": "BALANCED",
    "winRate": "49.2%",
    "presenceRate": "15.4%",
    "radar": {
      "zone": 78,
      "lethality": 75,
      "cc": 55,
      "mobility": 65,
      "surv": 52,
      "endg": 72
    },
    "phases": {
      "opening": 82,
      "midgame": 78,
      "endgame": 68
    },
    "heatmapHotspots": [
      [
        6,
        2
      ],
      [
        6,
        5
      ],
      [
        7,
        3
      ],
      [
        7,
        4
      ]
    ],
    "powerTiles": [
      "c2 (+4.7%)",
      "f2 (+4.5%)",
      "d1 (+4.0%)"
    ],
    "vulnerableTiles": [
      "d4 (-6.6%)",
      "e4 (-6.2%)",
      "c5 (-5.7%)"
    ],
    "topSynergies": [
      {
        "hero": "Warden",
        "delta": "+5.1%"
      },
      {
        "hero": "Paladin",
        "delta": "+4.2%"
      }
    ],
    "topCounters": [
      {
        "hero": "Shadowblade",
        "delta": "-7.4%"
      },
      {
        "hero": "Dragoon",
        "delta": "-6.5%"
      }
    ]
  },
  "Valkyrie": {
    "classes": [
      "Striker (Iniciador Aéreo)",
      "Flanqueador Espectral"
    ],
    "cost": 22,
    "efficiency": "1.09x (Equilibrado)",
    "cir": 1.09,
    "riotStatus": "BALANCED",
    "winRate": "53.2%",
    "presenceRate": "23.4%",
    "radar": {
      "zone": 72,
      "lethality": 86,
      "cc": 60,
      "mobility": 98,
      "surv": 70,
      "endg": 92
    },
    "phases": {
      "opening": 78,
      "midgame": 92,
      "endgame": 95
    },
    "heatmapHotspots": [
      [
        2,
        2
      ],
      [
        2,
        5
      ],
      [
        3,
        3
      ],
      [
        3,
        4
      ],
      [
        4,
        2
      ],
      [
        4,
        5
      ]
    ],
    "powerTiles": [
      "c6 (+6.4%)",
      "f6 (+6.1%)",
      "d5 (+5.7%)"
    ],
    "vulnerableTiles": [
      "a1 (-7.2%)",
      "h1 (-6.8%)",
      "a8 (-6.3%)"
    ],
    "topSynergies": [
      {
        "hero": "Arcanist",
        "delta": "+6.8%"
      },
      {
        "hero": "Paladin",
        "delta": "+5.4%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-6.7%"
      },
      {
        "hero": "Marksman",
        "delta": "-5.8%"
      }
    ]
  },
  "Arcanist": {
    "classes": [
      "Artillery (Artilharia Rúnica)",
      "Controlador Linear"
    ],
    "cost": 23,
    "efficiency": "1.02x (Equilibrado)",
    "cir": 1.02,
    "riotStatus": "BALANCED",
    "winRate": "51.4%",
    "presenceRate": "20.2%",
    "radar": {
      "zone": 88,
      "lethality": 92,
      "cc": 65,
      "mobility": 50,
      "surv": 54,
      "endg": 80
    },
    "phases": {
      "opening": 84,
      "midgame": 90,
      "endgame": 76
    },
    "heatmapHotspots": [
      [
        6,
        3
      ],
      [
        6,
        4
      ],
      [
        5,
        2
      ],
      [
        5,
        5
      ],
      [
        4,
        3
      ]
    ],
    "powerTiles": [
      "d2 (+5.6%)",
      "e2 (+5.3%)",
      "c3 (+4.8%)"
    ],
    "vulnerableTiles": [
      "d6 (-7.3%)",
      "e6 (-6.9%)",
      "f5 (-6.4%)"
    ],
    "topSynergies": [
      {
        "hero": "Valkyrie",
        "delta": "+6.8%"
      },
      {
        "hero": "Warden",
        "delta": "+5.2%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-8.5%"
      },
      {
        "hero": "Shadowblade",
        "delta": "-7.1%"
      }
    ]
  },
  "Duelist": {
    "classes": [
      "Striker (Esgrimista Diagonal)",
      "Assassino Cirúrgico"
    ],
    "cost": 24,
    "efficiency": "1.01x (Equilibrado)",
    "cir": 1.01,
    "riotStatus": "BALANCED",
    "winRate": "51.0%",
    "presenceRate": "19.5%",
    "radar": {
      "zone": 65,
      "lethality": 90,
      "cc": 50,
      "mobility": 82,
      "surv": 68,
      "endg": 88
    },
    "phases": {
      "opening": 68,
      "midgame": 88,
      "endgame": 90
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        3,
        4
      ],
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        2,
        4
      ],
      [
        5,
        3
      ]
    ],
    "powerTiles": [
      "d5 (+5.2%)",
      "e4 (+4.9%)",
      "e6 (+4.5%)"
    ],
    "vulnerableTiles": [
      "a3 (-6.5%)",
      "h6 (-6.1%)",
      "b1 (-5.8%)"
    ],
    "topSynergies": [
      {
        "hero": "FrostMage",
        "delta": "+6.0%"
      },
      {
        "hero": "Hookmaster",
        "delta": "+5.1%"
      }
    ],
    "topCounters": [
      {
        "hero": "Paladin",
        "delta": "-6.8%"
      },
      {
        "hero": "Warden",
        "delta": "-6.2%"
      }
    ]
  },
  "Warden": {
    "classes": [
      "Vanguard (Âncora Pesada)",
      "Guardião de Ponto"
    ],
    "cost": 25,
    "efficiency": "1.04x (Equilibrado)",
    "cir": 1.04,
    "riotStatus": "BALANCED",
    "winRate": "52.0%",
    "presenceRate": "22.0%",
    "radar": {
      "zone": 92,
      "lethality": 65,
      "cc": 85,
      "mobility": 40,
      "surv": 95,
      "endg": 82
    },
    "phases": {
      "opening": 75,
      "midgame": 94,
      "endgame": 86
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        3,
        4
      ],
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        2
      ],
      [
        4,
        5
      ]
    ],
    "powerTiles": [
      "d4 (+5.5%)",
      "e5 (+5.2%)",
      "c4 (+4.8%)"
    ],
    "vulnerableTiles": [
      "a1 (-6.9%)",
      "h8 (-6.5%)",
      "h1 (-6.1%)"
    ],
    "topSynergies": [
      {
        "hero": "Marksman",
        "delta": "+6.2%"
      },
      {
        "hero": "Arcanist",
        "delta": "+5.4%"
      }
    ],
    "topCounters": [
      {
        "hero": "Illusionist",
        "delta": "-6.5%"
      },
      {
        "hero": "Stormcaller",
        "delta": "-5.7%"
      }
    ]
  },
  "Illusionist": {
    "classes": [
      "Disruptor (Controlo de Espaço)",
      "Transpositor Tático"
    ],
    "cost": 27,
    "efficiency": "1.02x (Equilibrado)",
    "cir": 1.02,
    "riotStatus": "BALANCED",
    "winRate": "51.6%",
    "presenceRate": "18.8%",
    "radar": {
      "zone": 88,
      "lethality": 72,
      "cc": 80,
      "mobility": 85,
      "surv": 70,
      "endg": 84
    },
    "phases": {
      "opening": 78,
      "midgame": 89,
      "endgame": 88
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        3,
        4
      ],
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        2,
        3
      ],
      [
        5,
        4
      ]
    ],
    "powerTiles": [
      "c6 (+5.4%)",
      "d5 (+5.1%)",
      "e4 (+4.7%)"
    ],
    "vulnerableTiles": [
      "a8 (-6.7%)",
      "h1 (-6.2%)",
      "a1 (-5.9%)"
    ],
    "topSynergies": [
      {
        "hero": "Duelist",
        "delta": "+5.8%"
      },
      {
        "hero": "Marksman",
        "delta": "+5.0%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-7.6%"
      },
      {
        "hero": "Shadowblade",
        "delta": "-6.3%"
      }
    ]
  },
  "Marksman": {
    "classes": [
      "Artillery (Atirador Furtivo)",
      "Finalizador de Linha"
    ],
    "cost": 28,
    "efficiency": "1.05x (Equilibrado)",
    "cir": 1.05,
    "riotStatus": "BALANCED",
    "winRate": "52.8%",
    "presenceRate": "24.5%",
    "radar": {
      "zone": 85,
      "lethality": 95,
      "cc": 60,
      "mobility": 50,
      "surv": 58,
      "endg": 86
    },
    "phases": {
      "opening": 80,
      "midgame": 92,
      "endgame": 85
    },
    "heatmapHotspots": [
      [
        6,
        2
      ],
      [
        6,
        5
      ],
      [
        5,
        2
      ],
      [
        5,
        5
      ],
      [
        4,
        2
      ],
      [
        4,
        5
      ]
    ],
    "powerTiles": [
      "c2 (+6.0%)",
      "f2 (+5.7%)",
      "c3 (+5.2%)"
    ],
    "vulnerableTiles": [
      "d5 (-7.4%)",
      "e5 (-7.0%)",
      "d4 (-6.5%)"
    ],
    "topSynergies": [
      {
        "hero": "Warden",
        "delta": "+6.5%"
      },
      {
        "hero": "FrostMage",
        "delta": "+5.8%"
      }
    ],
    "topCounters": [
      {
        "hero": "Shadowblade",
        "delta": "-8.4%"
      },
      {
        "hero": "Valkyrie",
        "delta": "-7.2%"
      }
    ]
  },
  "Bone": {
    "classes": [
      "Minion (Esqueleto Conjurado)",
      "Peão de Contenção"
    ],
    "cost": 8,
    "efficiency": "0.95x (Equilibrado)",
    "cir": 0.95,
    "riotStatus": "BALANCED",
    "winRate": "48.5%",
    "presenceRate": "12.0%",
    "radar": {
      "zone": 40,
      "lethality": 30,
      "cc": 20,
      "mobility": 45,
      "surv": 35,
      "endg": 25
    },
    "phases": {
      "opening": 60,
      "midgame": 50,
      "endgame": 30
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        4,
        4
      ]
    ],
    "powerTiles": [
      "d5 (+3.2%)",
      "e4 (+3.0%)",
      "d4 (+2.8%)"
    ],
    "vulnerableTiles": [
      "a1 (-5.2%)",
      "h8 (-5.0%)",
      "h1 (-4.8%)"
    ],
    "topSynergies": [
      {
        "hero": "BoneLord",
        "delta": "+4.5%"
      },
      {
        "hero": "Lich",
        "delta": "+3.8%"
      }
    ],
    "topCounters": [
      {
        "hero": "Pyromancer",
        "delta": "-6.2%"
      },
      {
        "hero": "Stormcaller",
        "delta": "-5.5%"
      }
    ]
  },
  "Berserker": {
    "classes": [
      "Striker (Fúria Berserk)",
      "Duelista Agressivo"
    ],
    "cost": 18,
    "efficiency": "1.06x (Equilibrado)",
    "cir": 1.06,
    "riotStatus": "BALANCED",
    "winRate": "51.5%",
    "presenceRate": "18.2%",
    "radar": {
      "zone": 60,
      "lethality": 92,
      "cc": 45,
      "mobility": 75,
      "surv": 70,
      "endg": 85
    },
    "phases": {
      "opening": 70,
      "midgame": 90,
      "endgame": 88
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        4
      ]
    ],
    "powerTiles": [
      "d4 (+5.4%)",
      "e5 (+5.1%)",
      "e4 (+4.8%)"
    ],
    "vulnerableTiles": [
      "a2 (-6.5%)",
      "h7 (-6.2%)",
      "b8 (-5.8%)"
    ],
    "topSynergies": [
      {
        "hero": "Cleric",
        "delta": "+5.9%"
      },
      {
        "hero": "FrostMage",
        "delta": "+5.2%"
      }
    ],
    "topCounters": [
      {
        "hero": "Paladin",
        "delta": "-6.8%"
      },
      {
        "hero": "Hookmaster",
        "delta": "-5.9%"
      }
    ]
  },
  "Pyromancer": {
    "classes": [
      "Artillery (Mago Ígneo)",
      "Queimadura Zonal"
    ],
    "cost": 16,
    "efficiency": "1.03x (Equilibrado)",
    "cir": 1.03,
    "riotStatus": "BALANCED",
    "winRate": "50.8%",
    "presenceRate": "16.5%",
    "radar": {
      "zone": 88,
      "lethality": 85,
      "cc": 60,
      "mobility": 45,
      "surv": 55,
      "endg": 78
    },
    "phases": {
      "opening": 80,
      "midgame": 88,
      "endgame": 75
    },
    "heatmapHotspots": [
      [
        5,
        2
      ],
      [
        5,
        5
      ],
      [
        6,
        3
      ]
    ],
    "powerTiles": [
      "c3 (+5.1%)",
      "f3 (+4.8%)",
      "d2 (+4.4%)"
    ],
    "vulnerableTiles": [
      "d6 (-7.0%)",
      "e6 (-6.6%)",
      "f5 (-6.1%)"
    ],
    "topSynergies": [
      {
        "hero": "Warden",
        "delta": "+5.6%"
      },
      {
        "hero": "Geomancer",
        "delta": "+4.9%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-7.8%"
      },
      {
        "hero": "Shadowblade",
        "delta": "-6.9%"
      }
    ]
  },
  "Phantom": {
    "classes": [
      "Infiltrator (Espectro Furtivo)",
      "Desestabilizador Barato"
    ],
    "cost": 5,
    "efficiency": "1.12x (Forte para o Custo)",
    "cir": 1.12,
    "riotStatus": "STRONG_FOR_COST",
    "winRate": "51.0%",
    "presenceRate": "22.5%",
    "radar": {
      "zone": 35,
      "lethality": 65,
      "cc": 40,
      "mobility": 85,
      "surv": 30,
      "endg": 60
    },
    "phases": {
      "opening": 85,
      "midgame": 65,
      "endgame": 40
    },
    "heatmapHotspots": [
      [
        1,
        3
      ],
      [
        2,
        4
      ]
    ],
    "powerTiles": [
      "d7 (+4.5%)",
      "e6 (+4.2%)",
      "c6 (+3.9%)"
    ],
    "vulnerableTiles": [
      "d4 (-6.0%)",
      "e4 (-5.8%)",
      "d5 (-5.5%)"
    ],
    "topSynergies": [
      {
        "hero": "Shadowblade",
        "delta": "+5.2%"
      },
      {
        "hero": "Valkyrie",
        "delta": "+4.6%"
      }
    ],
    "topCounters": [
      {
        "hero": "Sentry",
        "delta": "-6.5%"
      },
      {
        "hero": "Stormcaller",
        "delta": "-5.8%"
      }
    ]
  },
  "Cleric": {
    "classes": [
      "Support (Clérigo Protetor)",
      "Curandeiro e Âncora"
    ],
    "cost": 14,
    "efficiency": "1.02x (Equilibrado)",
    "cir": 1.02,
    "riotStatus": "BALANCED",
    "winRate": "50.4%",
    "presenceRate": "15.0%",
    "radar": {
      "zone": 75,
      "lethality": 40,
      "cc": 70,
      "mobility": 50,
      "surv": 85,
      "endg": 82
    },
    "phases": {
      "opening": 72,
      "midgame": 85,
      "endgame": 88
    },
    "heatmapHotspots": [
      [
        4,
        2
      ],
      [
        4,
        5
      ],
      [
        5,
        3
      ]
    ],
    "powerTiles": [
      "c4 (+4.8%)",
      "f4 (+4.5%)",
      "d3 (+4.1%)"
    ],
    "vulnerableTiles": [
      "a1 (-6.3%)",
      "h8 (-6.0%)",
      "d7 (-5.6%)"
    ],
    "topSynergies": [
      {
        "hero": "Berserker",
        "delta": "+6.1%"
      },
      {
        "hero": "Templar",
        "delta": "+5.3%"
      }
    ],
    "topCounters": [
      {
        "hero": "Nightshade",
        "delta": "-6.7%"
      },
      {
        "hero": "Shadowblade",
        "delta": "-6.1%"
      }
    ]
  },
  "Templar": {
    "classes": [
      "Vanguard (Cavaleiro Sagrado)",
      "Baluarte Ofensivo"
    ],
    "cost": 15,
    "efficiency": "1.04x (Equilibrado)",
    "cir": 1.04,
    "riotStatus": "BALANCED",
    "winRate": "51.1%",
    "presenceRate": "16.8%",
    "radar": {
      "zone": 80,
      "lethality": 75,
      "cc": 65,
      "mobility": 60,
      "surv": 85,
      "endg": 80
    },
    "phases": {
      "opening": 75,
      "midgame": 88,
      "endgame": 82
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        4
      ]
    ],
    "powerTiles": [
      "d5 (+5.0%)",
      "e4 (+4.7%)",
      "d4 (+4.5%)"
    ],
    "vulnerableTiles": [
      "a2 (-6.4%)",
      "h7 (-6.0%)",
      "b8 (-5.6%)"
    ],
    "topSynergies": [
      {
        "hero": "Cleric",
        "delta": "+5.4%"
      },
      {
        "hero": "Arcanist",
        "delta": "+4.8%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-6.5%"
      },
      {
        "hero": "Illusionist",
        "delta": "-5.8%"
      }
    ]
  },
  "Inquisitor": {
    "classes": [
      "Disruptor (Silenciador Místico)",
      "Executor Anti-Magos"
    ],
    "cost": 15,
    "efficiency": "1.07x (Equilibrado)",
    "cir": 1.07,
    "riotStatus": "BALANCED",
    "winRate": "52.1%",
    "presenceRate": "19.8%",
    "radar": {
      "zone": 82,
      "lethality": 80,
      "cc": 88,
      "mobility": 55,
      "surv": 78,
      "endg": 86
    },
    "phases": {
      "opening": 76,
      "midgame": 90,
      "endgame": 86
    },
    "heatmapHotspots": [
      [
        3,
        2
      ],
      [
        4,
        5
      ],
      [
        3,
        4
      ]
    ],
    "powerTiles": [
      "c5 (+5.6%)",
      "f4 (+5.3%)",
      "e5 (+4.9%)"
    ],
    "vulnerableTiles": [
      "a1 (-6.8%)",
      "h8 (-6.4%)",
      "b1 (-5.9%)"
    ],
    "topSynergies": [
      {
        "hero": "Paladin",
        "delta": "+5.7%"
      },
      {
        "hero": "Valkyrie",
        "delta": "+5.1%"
      }
    ],
    "topCounters": [
      {
        "hero": "Marksman",
        "delta": "-6.4%"
      },
      {
        "hero": "Warden",
        "delta": "-5.7%"
      }
    ]
  },
  "Geomancer": {
    "classes": [
      "Controller (Manipulador Telúrico)",
      "Criador de Barreiras"
    ],
    "cost": 14,
    "efficiency": "1.00x (Equilibrado)",
    "cir": 1.0,
    "riotStatus": "BALANCED",
    "winRate": "50.0%",
    "presenceRate": "14.2%",
    "radar": {
      "zone": 90,
      "lethality": 55,
      "cc": 85,
      "mobility": 40,
      "surv": 80,
      "endg": 78
    },
    "phases": {
      "opening": 82,
      "midgame": 86,
      "endgame": 74
    },
    "heatmapHotspots": [
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        5,
        3
      ]
    ],
    "powerTiles": [
      "d4 (+4.9%)",
      "e4 (+4.6%)",
      "d3 (+4.2%)"
    ],
    "vulnerableTiles": [
      "a7 (-6.5%)",
      "h2 (-6.1%)",
      "d8 (-5.7%)"
    ],
    "topSynergies": [
      {
        "hero": "Marksman",
        "delta": "+5.8%"
      },
      {
        "hero": "Ranger",
        "delta": "+5.0%"
      }
    ],
    "topCounters": [
      {
        "hero": "Shadowblade",
        "delta": "-7.0%"
      },
      {
        "hero": "Dragoon",
        "delta": "-6.3%"
      }
    ]
  },
  "Lich": {
    "classes": [
      "Summoner (Necromante Supremo)",
      "Mestre da Morte"
    ],
    "cost": 15,
    "efficiency": "1.05x (Equilibrado)",
    "cir": 1.05,
    "riotStatus": "BALANCED",
    "winRate": "51.4%",
    "presenceRate": "17.0%",
    "radar": {
      "zone": 92,
      "lethality": 70,
      "cc": 75,
      "mobility": 45,
      "surv": 75,
      "endg": 90
    },
    "phases": {
      "opening": 68,
      "midgame": 86,
      "endgame": 94
    },
    "heatmapHotspots": [
      [
        6,
        3
      ],
      [
        6,
        4
      ],
      [
        5,
        2
      ]
    ],
    "powerTiles": [
      "d2 (+5.2%)",
      "e2 (+4.9%)",
      "c3 (+4.5%)"
    ],
    "vulnerableTiles": [
      "d6 (-7.1%)",
      "e6 (-6.7%)",
      "f5 (-6.2%)"
    ],
    "topSynergies": [
      {
        "hero": "BoneLord",
        "delta": "+6.3%"
      },
      {
        "hero": "FrostMage",
        "delta": "+5.1%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-7.9%"
      },
      {
        "hero": "Pyromancer",
        "delta": "-6.8%"
      }
    ]
  },
  "Nightshade": {
    "classes": [
      "Striker (Veneno e Sombras)",
      "Emboscador Mortal"
    ],
    "cost": 14,
    "efficiency": "1.03x (Equilibrado)",
    "cir": 1.03,
    "riotStatus": "BALANCED",
    "winRate": "50.9%",
    "presenceRate": "16.4%",
    "radar": {
      "zone": 50,
      "lethality": 90,
      "cc": 65,
      "mobility": 88,
      "surv": 55,
      "endg": 85
    },
    "phases": {
      "opening": 74,
      "midgame": 88,
      "endgame": 86
    },
    "heatmapHotspots": [
      [
        2,
        2
      ],
      [
        2,
        5
      ],
      [
        4,
        3
      ]
    ],
    "powerTiles": [
      "c6 (+5.3%)",
      "f6 (+5.0%)",
      "d4 (+4.6%)"
    ],
    "vulnerableTiles": [
      "d2 (-6.8%)",
      "e2 (-6.4%)",
      "a1 (-6.0%)"
    ],
    "topSynergies": [
      {
        "hero": "Shadowblade",
        "delta": "+5.7%"
      },
      {
        "hero": "Cleric",
        "delta": "+4.9%"
      }
    ],
    "topCounters": [
      {
        "hero": "Paladin",
        "delta": "-7.1%"
      },
      {
        "hero": "Warden",
        "delta": "-6.4%"
      }
    ]
  },
  "Obelisk": {
    "classes": [
      "Bastion (Totem Estático)",
      "Sentinela de Bloqueio"
    ],
    "cost": 12,
    "efficiency": "0.98x (Equilibrado)",
    "cir": 0.98,
    "riotStatus": "BALANCED",
    "winRate": "49.5%",
    "presenceRate": "13.5%",
    "radar": {
      "zone": 85,
      "lethality": 30,
      "cc": 70,
      "mobility": 10,
      "surv": 95,
      "endg": 60
    },
    "phases": {
      "opening": 85,
      "midgame": 75,
      "endgame": 50
    },
    "heatmapHotspots": [
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        3
      ]
    ],
    "powerTiles": [
      "d4 (+4.5%)",
      "e4 (+4.2%)",
      "d5 (+3.9%)"
    ],
    "vulnerableTiles": [
      "a8 (-5.8%)",
      "h1 (-5.5%)",
      "h8 (-5.2%)"
    ],
    "topSynergies": [
      {
        "hero": "Marksman",
        "delta": "+5.5%"
      },
      {
        "hero": "Stormcaller",
        "delta": "+4.8%"
      }
    ],
    "topCounters": [
      {
        "hero": "Duelist",
        "delta": "-6.2%"
      },
      {
        "hero": "Valkyrie",
        "delta": "-5.6%"
      }
    ]
  },
  "Sentry": {
    "classes": [
      "Bastion (Torre de Vigia)",
      "Supressor Estático"
    ],
    "cost": 10,
    "efficiency": "0.96x (Equilibrado)",
    "cir": 0.96,
    "riotStatus": "BALANCED",
    "winRate": "48.9%",
    "presenceRate": "12.8%",
    "radar": {
      "zone": 80,
      "lethality": 60,
      "cc": 50,
      "mobility": 10,
      "surv": 90,
      "endg": 55
    },
    "phases": {
      "opening": 82,
      "midgame": 72,
      "endgame": 48
    },
    "heatmapHotspots": [
      [
        5,
        2
      ],
      [
        5,
        5
      ],
      [
        4,
        3
      ]
    ],
    "powerTiles": [
      "c3 (+4.4%)",
      "f3 (+4.1%)",
      "d4 (+3.8%)"
    ],
    "vulnerableTiles": [
      "d7 (-6.0%)",
      "e7 (-5.7%)",
      "a1 (-5.3%)"
    ],
    "topSynergies": [
      {
        "hero": "Warden",
        "delta": "+5.0%"
      },
      {
        "hero": "Paladin",
        "delta": "+4.4%"
      }
    ],
    "topCounters": [
      {
        "hero": "Shadowblade",
        "delta": "-6.5%"
      },
      {
        "hero": "Phantom",
        "delta": "-5.8%"
      }
    ]
  },
  "Stonewall": {
    "classes": [
      "Bastion (Muralha Viva)",
      "Barricada Tática"
    ],
    "cost": 12,
    "efficiency": "0.97x (Equilibrado)",
    "cir": 0.97,
    "riotStatus": "BALANCED",
    "winRate": "49.2%",
    "presenceRate": "13.0%",
    "radar": {
      "zone": 90,
      "lethality": 20,
      "cc": 75,
      "mobility": 10,
      "surv": 98,
      "endg": 50
    },
    "phases": {
      "opening": 88,
      "midgame": 70,
      "endgame": 45
    },
    "heatmapHotspots": [
      [
        4,
        3
      ],
      [
        4,
        4
      ],
      [
        3,
        4
      ]
    ],
    "powerTiles": [
      "d4 (+4.6%)",
      "e4 (+4.3%)",
      "e5 (+4.0%)"
    ],
    "vulnerableTiles": [
      "a1 (-5.9%)",
      "h8 (-5.6%)",
      "h1 (-5.3%)"
    ],
    "topSynergies": [
      {
        "hero": "Arcanist",
        "delta": "+5.4%"
      },
      {
        "hero": "Stormcaller",
        "delta": "+4.7%"
      }
    ],
    "topCounters": [
      {
        "hero": "Illusionist",
        "delta": "-6.4%"
      },
      {
        "hero": "Duelist",
        "delta": "-5.7%"
      }
    ]
  },
  "Trickster": {
    "classes": [
      "Disruptor (Trapaceiro Arcano)",
      "Ilusionista de Confusão"
    ],
    "cost": 14,
    "efficiency": "1.01x (Equilibrado)",
    "cir": 1.01,
    "riotStatus": "BALANCED",
    "winRate": "50.6%",
    "presenceRate": "15.5%",
    "radar": {
      "zone": 75,
      "lethality": 65,
      "cc": 85,
      "mobility": 80,
      "surv": 60,
      "endg": 80
    },
    "phases": {
      "opening": 78,
      "midgame": 85,
      "endgame": 82
    },
    "heatmapHotspots": [
      [
        3,
        2
      ],
      [
        4,
        5
      ],
      [
        2,
        4
      ]
    ],
    "powerTiles": [
      "c5 (+5.0%)",
      "f4 (+4.7%)",
      "e6 (+4.3%)"
    ],
    "vulnerableTiles": [
      "d3 (-6.5%)",
      "e3 (-6.1%)",
      "a1 (-5.7%)"
    ],
    "topSynergies": [
      {
        "hero": "Valkyrie",
        "delta": "+5.6%"
      },
      {
        "hero": "FrostMage",
        "delta": "+4.9%"
      }
    ],
    "topCounters": [
      {
        "hero": "Inquisitor",
        "delta": "-7.0%"
      },
      {
        "hero": "Paladin",
        "delta": "-6.2%"
      }
    ]
  },
  "Ghoul": {
    "classes": [
      "Minion (Carniçal Voraz)",
      "Enxame Rápido"
    ],
    "cost": 10,
    "efficiency": "0.98x (Equilibrado)",
    "cir": 0.98,
    "riotStatus": "BALANCED",
    "winRate": "49.5%",
    "presenceRate": "14.0%",
    "radar": {
      "zone": 45,
      "lethality": 60,
      "cc": 30,
      "mobility": 70,
      "surv": 45,
      "endg": 40
    },
    "phases": {
      "opening": 75,
      "midgame": 60,
      "endgame": 35
    },
    "heatmapHotspots": [
      [
        3,
        3
      ],
      [
        4,
        4
      ],
      [
        2,
        3
      ]
    ],
    "powerTiles": [
      "d5 (+3.8%)",
      "e4 (+3.5%)",
      "c6 (+3.2%)"
    ],
    "vulnerableTiles": [
      "a1 (-5.5%)",
      "h8 (-5.2%)",
      "h1 (-5.0%)"
    ],
    "topSynergies": [
      {
        "hero": "Lich",
        "delta": "+4.8%"
      },
      {
        "hero": "BoneLord",
        "delta": "+4.2%"
      }
    ],
    "topCounters": [
      {
        "hero": "Pyromancer",
        "delta": "-6.7%"
      },
      {
        "hero": "Stormcaller",
        "delta": "-6.0%"
      }
    ]
  }
};

// Web Audio API Synthesized Chimes with Game Review Classification Chords
let audioCtx = null;
function playChime(type) {
  if (typeof soundEnabled !== "undefined" && !soundEnabled) return;
  try {
    if (typeof window === "undefined") return;
    const AudioCtor = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtor) return;
    if (!audioCtx) audioCtx = new AudioCtor();
    if (audioCtx.state === "suspended") audioCtx.resume();
    const now = audioCtx.currentTime;

    if (type === "move") {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.frequency.setValueAtTime(320, now);
      osc.frequency.exponentialRampToValueAtTime(480, now + 0.08);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
      osc.start(now);
      osc.stop(now + 0.08);
    } else if (type === "stun") {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(550, now);
      osc.frequency.exponentialRampToValueAtTime(220, now + 0.18);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.18);
      osc.start(now);
      osc.stop(now + 0.18);
    } else if (type === "victory" || type === "brilliant") {
      // Triumphant ascending harmonic chord (C5 -> E5 -> G5 -> C6)
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.type = "triangle";
        const startTime = now + idx * 0.07;
        osc.frequency.setValueAtTime(freq, startTime);
        gain.gain.setValueAtTime(0.13, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.35);
        osc.start(startTime);
        osc.stop(startTime + 0.35);
      });
    } else if (type === "best" || type === "great") {
      // Affirmative crisp two-tone chord (D5 -> A5)
      [587.33, 880.00].forEach((freq, idx) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.type = "sine";
        const startTime = now + idx * 0.06;
        osc.frequency.setValueAtTime(freq, startTime);
        gain.gain.setValueAtTime(0.10, startTime);
        gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.25);
        osc.start(startTime);
        osc.stop(startTime + 0.25);
      });
    } else if (type === "blunder") {
      // Dissonant descending alert buzz for blunders / capivaradas (180 Hz -> 85 Hz sawtooth)
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.linearRampToValueAtTime(85, now + 0.28);
      gain.gain.setValueAtTime(0.20, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
      osc.start(now);
      osc.stop(now + 0.28);
    } else if (type === "mistake" || type === "inaccuracy") {
      // Subtle warning descending double-tone
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(293.66, now);
      osc.frequency.exponentialRampToValueAtTime(220, now + 0.16);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
      osc.start(now);
      osc.stop(now + 0.16);
    }
  } catch (e) {}
}

// --- Legal Action Engine (INVARIANTS: No Self-Capture, Strict Turn, Two-Hit Stun) ---
function getLegalActionsForPiece(r, c, board) {
  const piece = board[r][c];
  if (!piece) return [];
  if (piece.stun > 0) return []; // Stunned pieces cannot act!

  const rule = HERO_RULES[piece.name] || {
    move: { type: "orthogonal", steps: 1, ghost: false },
    attack: { type: "orthogonal", steps: 1 },
    cost: 10,
    acronym: piece.name.substring(0, 2)
  };

  const actions = [];
  const grid = board.length;

  // 1. Calculate Legal Moves (Must land on EMPTY square, allies strictly block)
  if (rule.move && rule.move.type !== "none") {
    if (rule.move.type === "knight") {
      for (const [dr, dc] of KNIGHT_DIRS) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr >= 0 && nr < grid && nc >= 0 && nc < grid) {
          if (board[nr][nc] === null) {
            actions.push({ type: "move", r: nr, c: nc });
          }
        }
      }
    } else {
      let dirs = ORTHO_DIRS;
      if (rule.move.type === "diagonal") dirs = DIAG_DIRS;
      else if (rule.move.type === "adjacent") dirs = ADJ_DIRS;
      else if (rule.move.type === "forward_cone") {
        const forward = piece.team === "brancas" ? -1 : 1;
        dirs = [[forward, 0], [forward, -1], [forward, 1]];
      }

      const maxSteps = rule.move.steps || 1;
      for (const [dr, dc] of dirs) {
        for (let step = 1; step <= maxSteps; step++) {
          const nr = r + dr * step;
          const nc = c + dc * step;
          if (nr < 0 || nr >= grid || nc < 0 || nc >= grid) break;

          if (board[nr][nc] === null) {
            actions.push({ type: "move", r: nr, c: nc });
          } else {
            // Blocked by any piece! If ghost is true, it may fly over
            if (!rule.move.ghost) break;
          }
        }
      }
    }
  }

  // 2. Calculate Legal Attacks (Must target an ENEMY piece, never an ally!)
  if (rule.attack) {
    if (rule.attack.type === "knight") {
      for (const [dr, dc] of KNIGHT_DIRS) {
        const nr = r + dr;
        const nc = c + dc;
        if (nr >= 0 && nr < grid && nc >= 0 && nc < grid) {
          const target = board[nr][nc];
          if (target && target.team !== piece.team) {
            actions.push({ type: "attack", r: nr, c: nc, target, stunOnly: !!rule.attack.stunOnly });
          }
        }
      }
    } else {
      let dirs = ORTHO_DIRS;
      if (rule.attack.type === "diagonal") dirs = DIAG_DIRS;
      else if (rule.attack.type === "adjacent") dirs = ADJ_DIRS;
      else if (rule.attack.type === "forward_cone") {
        const forward = piece.team === "brancas" ? -1 : 1;
        dirs = [[forward, 0], [forward, -1], [forward, 1]];
      }

      const maxSteps = rule.attack.steps || 1;
      for (const [dr, dc] of dirs) {
        for (let step = 1; step <= maxSteps; step++) {
          const nr = r + dr * step;
          const nc = c + dc * step;
          if (nr < 0 || nr >= grid || nc < 0 || nc >= grid) break;

          const target = board[nr][nc];
          if (target === null) {
            // Can pass through empty space in ranged ray attacks
            continue;
          } else {
            // Reached a piece
            if (target.team !== piece.team) {
              // Enemy piece! Legal attack target!
              actions.push({ type: "attack", r: nr, c: nc, target, stunOnly: !!rule.attack.stunOnly });
            }
            // Cannot attack past any unit in a line
            break;
          }
        }
      }
    }
  }

  return actions;
}

// Execute Action on Board
function applyAction(fromR, fromC, action) {
  const piece = boardData[fromR][fromC];
  if (!piece) return;

  const evalBefore = computeBoardCentipawns(boardData);
  let moveNotation = "";

  if (action.type === "move") {
    boardData[action.r][action.c] = piece;
    boardData[fromR][fromC] = null;
    playChime("move");
    moveNotation = `${piece.name} ${coordsToNotation(fromR, fromC)} - ${coordsToNotation(action.r, action.c)}`;
    addMoveToHistory(moveNotation);
  } else if (action.type === "attack") {
    const target = action.target;
    if (target.stun > 0) {
      // INVARIANT: Second hit on stunned unit eliminates it immediately!
      boardData[action.r][action.c] = piece;
      boardData[fromR][fromC] = null;
      playChime("victory");
      moveNotation = `${piece.name} captura ${target.name} [Lethal Kill]`;
      addMoveToHistory(moveNotation);
    } else if (action.stunOnly) {
      // Stun-only ability (e.g. FrostMage)
      target.stun = 2;
      playChime("stun");
      moveNotation = `${piece.name} congela ${target.name} (Stun 2 turnos)`;
      addMoveToHistory(moveNotation);
    } else {
      // Standard attack capture
      boardData[action.r][action.c] = piece;
      boardData[fromR][fromC] = null;
      playChime("stun");
      moveNotation = `${piece.name} x ${target.name} [${coordsToNotation(action.r, action.c)}]`;
      addMoveToHistory(moveNotation);
    }
  }

  const evalAfter = computeBoardCentipawns(boardData);
  classifyLastMove(evalBefore, evalAfter, moveNotation, piece.team);
  updateLiveEvalBar(evalAfter);
  renderGameReviewPanel();
}

function coordsToNotation(r, c) {
  const colLetter = String.fromCharCode(97 + c);
  const rowNumber = boardGrid - r;
  return `${colLetter}${rowNumber}`;
}

function addMoveToHistory(text) {
  moveHistory.push(text);
  const currentEval = computeBoardCentipawns(boardData);
  evalHistory.push(currentEval);
}

// Turn Cycle and AI Bot Invocation
function finishTurn() {
  selectedSquare = null;
  currentLegalActions = [];

  // Decrement stun timers for the NEXT team entering their turn
  const nextTeam = currentTurn === "white" ? "pretas" : "brancas";
  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const p = boardData[r][c];
      if (p && p.team === nextTeam && p.stun > 0) {
        p.stun -= 1;
      }
    }
  }

  currentTurn = currentTurn === "white" ? "black" : "white";
  updateClockDisplays();
  drawBoard();

  // Check Game Over
  let whiteCount = 0;
  let blackCount = 0;
  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const p = boardData[r][c];
      if (p) {
        if (p.team === "brancas") whiteCount++;
        else if (p.team === "pretas") blackCount++;
      }
    }
  }

  if (whiteCount === 0) {
    isGameOver = true;
    alert("Partida terminada: As Pretas Venceram!");
    showPostGameButtons();
    return;
  }
  if (blackCount === 0) {
    isGameOver = true;
    alert("Vitória! As Brancas derrotaram todas as forças oponentes!");
    playChime("victory");
    showPostGameButtons();
    return;
  }

  // If it's Black's turn and opponent is AI, invoke Ares AI Bot
  const oppVal = document.getElementById("opponentSelect").value;
  if (currentTurn === "black" && oppVal.startsWith("bot_") && !isGameOver && !isAcademyMode) {
    isAiThinking = true;
    setTimeout(() => {
      playAresBotMove();
      isAiThinking = false;
    }, 400);
  }
}

// Ares AI Bot (Stockfish-inspired tactical scoring)
function playAresBotMove() {
  if (isGameOver) return;

  const allBotActions = [];
  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const p = boardData[r][c];
      if (p && p.team === "pretas") {
        const acts = getLegalActionsForPiece(r, c, boardData);
        for (const act of acts) {
          allBotActions.push({ fromR: r, fromC: c, action: act });
        }
      }
    }
  }

  if (allBotActions.length === 0) {
    isGameOver = true;
    alert("Vitória! Ares Bot não tem jogadas legais disponíveis!");
    showPostGameButtons();
    return;
  }

  // Tactical evaluation for each action
  const oppVal = document.getElementById("opponentSelect").value;
  let randomness = 20;
  if (oppVal === "bot_apprentice") randomness = 50;
  else if (oppVal === "bot_advanced") randomness = 5;
  else if (oppVal === "bot_master") randomness = 0;

  for (const item of allBotActions) {
    let score = 0;
    const act = item.action;

    if (act.type === "attack") {
      const targetRule = HERO_RULES[act.target.name] || { cost: 10 };
      score += targetRule.cost * 10;

      // Two-Hit Stun Priority: Lethal elimination gets huge bonus!
      if (act.target.stun > 0) {
        score += 800;
      } else if (act.stunOnly) {
        score += 150;
      }
    } else if (act.type === "move") {
      // Reward advancing towards White side
      score += act.r * 5;
      // Slight center control preference
      const centerDist = Math.abs(act.c - boardGrid / 2) + Math.abs(act.r - boardGrid / 2);
      score += (8 - centerDist) * 2;
    }

    score += (Math.random() - 0.5) * randomness;
    item.score = score;
  }

  // Sort descending by score
  allBotActions.sort((a, b) => b.score - a.score);
  const chosen = allBotActions[0];

  applyAction(chosen.fromR, chosen.fromC, chosen.action);
  finishTurn();
}

function showPostGameButtons() {
  document.getElementById("btnResign").style.display = "none";
  document.getElementById("btnRematch").style.display = "inline-block";
  document.getElementById("btnGameReview").style.display = "inline-block";
}

// Board Rendering (Chessboard styling, asset silhouettes, move dots & attack rings)
function drawBoard() {
  const size = canvas.width;
  const squareSize = size / boardGrid;

  for (let r = 0; r < boardGrid; r++) {
    for (let c = 0; c < boardGrid; c++) {
      const isLight = (r + c) % 2 === 0;
      ctx.fillStyle = isLight ? "#eeeed2" : "#769656"; // Chess.com style green & cream
      ctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);

      // Selected square highlight
      if (selectedSquare && selectedSquare.r === r && selectedSquare.c === c) {
        ctx.fillStyle = "rgba(255, 255, 0, 0.4)";
        ctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
      }

      // Legal move/attack indicators
      for (const act of currentLegalActions) {
        if (act.r === r && act.c === c) {
          const cx = c * squareSize + squareSize / 2;
          const cy = r * squareSize + squareSize / 2;
          if (act.type === "move") {
            // Small translucent circle for empty move
            ctx.beginPath();
            ctx.arc(cx, cy, squareSize * 0.14, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(0, 0, 0, 0.22)";
            ctx.fill();
          } else if (act.type === "attack") {
            // Red ring for target attack
            ctx.beginPath();
            ctx.arc(cx, cy, squareSize * 0.42, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(239, 68, 68, 0.85)";
            ctx.lineWidth = 4;
            ctx.stroke();
          }
        }
      }

      // Render Piece
      const piece = boardData[r][c];
      if (piece) {
        const cx = c * squareSize + squareSize / 2;
        const cy = r * squareSize + squareSize / 2;
        const radius = squareSize * 0.38;

        // Base circular token
        ctx.save();
        ctx.shadowColor = "rgba(0, 0, 0, 0.35)";
        ctx.shadowBlur = 6;
        ctx.shadowOffsetY = 3;

        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        if (piece.team === "brancas") {
          ctx.fillStyle = "#ffffff";
        } else {
          ctx.fillStyle = "#1e293b";
        }
        ctx.fill();
        ctx.restore();

        // Border ring
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.strokeStyle = piece.team === "brancas" ? "#cbd5e1" : "#475569";
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Stun effect: Electric cyan ring + badge
        if (piece.stun > 0) {
          ctx.beginPath();
          ctx.arc(cx, cy, radius + 3, 0, Math.PI * 2);
          ctx.strokeStyle = "#00e5ff";
          ctx.lineWidth = 3.5;
          ctx.stroke();

          // Small stun indicator text
          ctx.fillStyle = "#00e5ff";
          ctx.font = "bold 11px sans-serif";
          ctx.fillText(`❄${piece.stun}`, cx + radius - 6, cy - radius + 8);
        }

        // Draw Hero Visual Asset or fallback acronym
        const assetName = piece.name.toLowerCase();
        const img = PIECE_IMAGES[assetName];
        if (img && img.complete && img.naturalWidth > 0) {
          const iconSize = squareSize * 0.58;
          ctx.save();
          // For dark pieces, invert/tint white silhouettes
          if (piece.team === "brancas") {
            ctx.filter = "invert(1) drop-shadow(0 1px 1px rgba(0,0,0,0.4))";
          } else {
            ctx.filter = "drop-shadow(0 1px 1px rgba(255,255,255,0.2))";
          }
          ctx.drawImage(img, cx - iconSize / 2, cy - iconSize / 2, iconSize, iconSize);
          ctx.restore();
        } else {
          // Fallback text symbol
          const rule = HERO_RULES[piece.name] || { acronym: piece.name.substring(0, 2) };
          ctx.fillStyle = piece.team === "brancas" ? "#0f172a" : "#f8fafc";
          ctx.font = `bold ${Math.floor(squareSize * 0.30)}px sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(rule.acronym, cx, cy);
        }
      }
    }
  }
}

// User Interaction Handler (STRICT INVARIANT: Player cannot move Black/AI pieces, No Self-Capture)
canvas.addEventListener("click", (e) => {
  if (isGameOver || isAiThinking) return;

  const rect = canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  const squareSize = canvas.width / boardGrid;
  const c = Math.floor(x / squareSize);
  const r = Math.floor(y / squareSize);

  if (r < 0 || r >= boardGrid || c < 0 || c >= boardGrid) return;

  const clickedPiece = boardData[r][c];

  // If no piece is currently selected:
  if (!selectedSquare) {
    if (clickedPiece) {
      // In normal game vs Bot, player is White! Strictly forbid selecting opponent pieces!
      const activeColor = currentTurn === "white" ? "brancas" : "pretas";
      if (clickedPiece.team === activeColor) {
        selectedSquare = { r, c };
        currentLegalActions = getLegalActionsForPiece(r, c, boardData);
        drawBoard();
      }
    }
    return;
  }

  // A piece was already selected at selectedSquare
  const fromR = selectedSquare.r;
  const fromC = selectedSquare.c;
  const selectedPiece = boardData[fromR][fromC];

  // If clicked the exact same square, deselect
  if (fromR === r && fromC === c) {
    selectedSquare = null;
    currentLegalActions = [];
    drawBoard();
    return;
  }

  // If clicked another allied piece, switch selection to that ally (NO self-capture!)
  if (clickedPiece && clickedPiece.team === selectedPiece.team) {
    selectedSquare = { r, c };
    currentLegalActions = getLegalActionsForPiece(r, c, boardData);
    drawBoard();
    return;
  }

  // Check if destination (r, c) is among the valid legal actions
  const chosenAction = currentLegalActions.find(act => act.r === r && act.c === c);

  if (chosenAction) {
    // If in Academy Mode, verify with lesson objective
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

    // If in Tactical Puzzle Mode, verify with puzzle solution
    if (isPuzzleMode && currentPuzzle) {
      const sol = currentPuzzle.solution;
      const banner = document.getElementById("puzzleStatusBanner");
      const nextBtn = document.getElementById("btnNextPuzzle");

      const isCorrect = (fromR === sol.fromR && fromC === sol.fromC && r === sol.toR && c === sol.toC);
      if (isCorrect) {
        puzzleStreak++;
        puzzleUserElo += 15;
        savePuzzleStats();
        updatePuzzleStatsUI();
        if (banner) {
          banner.style.display = "block";
          banner.style.background = "rgba(34, 197, 94, 0.2)";
          banner.style.border = "1px solid #22c55e";
          banner.style.color = "#22c55e";
          banner.innerHTML = `<strong>✨ Resolvido com Sucesso! (+15 ELO)</strong> ${currentPuzzle.explanation}`;
        }
        if (nextBtn) nextBtn.style.display = "inline-block";
        playChime("brilliant");
      } else {
        puzzleStreak = 0;
        puzzleUserElo = Math.max(800, puzzleUserElo - 10);
        savePuzzleStats();
        updatePuzzleStatsUI();
        if (banner) {
          banner.style.display = "block";
          banner.style.background = "rgba(239, 68, 68, 0.2)";
          banner.style.border = "1px solid #ef4444";
          banner.style.color = "#f87171";
          banner.innerHTML = "<strong>Lance Incorreto (-10 ELO).</strong> Tenta novamente ou consulta a Dica.";
        }
        playChime("blunder");
      }
    }

    applyAction(fromR, fromC, chosenAction);
    finishTurn();
  } else {
    // Clicked an illegal destination: simply deselect
    selectedSquare = null;
    currentLegalActions = [];
    drawBoard();
  }
});

// Clocks and Timers
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

// Board Initialization
function initDefaultBoard() {
  boardData = Array(boardGrid).fill(null).map(() => Array(boardGrid).fill(null));
  isGameOver = false;
  moveHistory = [];
  evalHistory = [0];
  selectedSquare = null;
  currentLegalActions = [];
  currentTurn = "white";

  document.getElementById("btnRematch").style.display = "none";
  document.getElementById("btnGameReview").style.display = "none";
  document.getElementById("btnResign").style.display = "inline-block";

  // White pieces (Row 7 and 6)
  boardData[boardGrid - 1][0] = { name: "Dragoon", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][1] = { name: "FrostMage", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][2] = { name: "BoneLord", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][3] = { name: "Paladin", team: "brancas", stun: 0 };
  boardData[boardGrid - 1][4] = { name: "Stormcaller", team: "brancas", stun: 0 };
  for (let c = 0; c < Math.min(boardGrid, 5); c++) {
    boardData[boardGrid - 2][c] = { name: "Bone", team: "brancas", stun: 0 };
  }

  // Black pieces (Row 0 and 1)
  boardData[0][0] = { name: "Dragoon", team: "pretas", stun: 0 };
  boardData[0][1] = { name: "FrostMage", team: "pretas", stun: 0 };
  boardData[0][2] = { name: "BoneLord", team: "pretas", stun: 0 };
  boardData[0][3] = { name: "Shadowblade", team: "pretas", stun: 0 };
  boardData[0][4] = { name: "Hookmaster", team: "pretas", stun: 0 };
  for (let c = 0; c < Math.min(boardGrid, 5); c++) {
    boardData[1][c] = { name: "Bone", team: "pretas", stun: 0 };
  }
}

// Hero Academy Curriculum
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
  currentLegalActions = [];
  currentTurn = "white";

  lesson.pieces.forEach(p => {
    boardData[p.r][p.c] = { name: p.name, team: p.team, stun: p.stun };
  });

  drawBoard();
}

// Football-style Radar Chart & Square Heatmap
function renderRadarChart(metrics) {
  const chartCanvas = document.getElementById("radarChartCanvas");
  if (!chartCanvas) return;
  const cctx = chartCanvas.getContext("2d");
  const w = chartCanvas.width;
  const h = chartCanvas.height;
  cctx.clearRect(0, 0, w, h);

  const cx = w / 2;
  const cy = h / 2;
  const radius = Math.min(cx, cy) - 24;

  const labels = ["Controlo", "Letalidade", "Stun/CC", "Mobilidade", "Sobrevivência", "Final"];
  const values = [metrics.zone, metrics.lethality, metrics.cc, metrics.mobility, metrics.surv, metrics.endg];
  const numAxes = labels.length;
  const angleStep = (Math.PI * 2) / numAxes;

  // Concentric web rings
  cctx.strokeStyle = "#30363d";
  cctx.lineWidth = 1;
  for (let level = 1; level <= 4; level++) {
    cctx.beginPath();
    const r = (radius / 4) * level;
    for (let i = 0; i < numAxes; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      if (i === 0) cctx.moveTo(x, y);
      else cctx.lineTo(x, y);
    }
    cctx.closePath();
    cctx.stroke();
  }

  // Radial axes & labels
  cctx.fillStyle = "#8b949e";
  cctx.font = "10px sans-serif";
  cctx.textAlign = "center";
  cctx.textBaseline = "middle";

  for (let i = 0; i < numAxes; i++) {
    const angle = i * angleStep - Math.PI / 2;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    cctx.beginPath();
    cctx.moveTo(cx, cy);
    cctx.lineTo(x, y);
    cctx.stroke();

    const labelX = cx + Math.cos(angle) * (radius + 14);
    const labelY = cy + Math.sin(angle) * (radius + 14);
    cctx.fillText(labels[i], labelX, labelY);
  }

  // Polygon fill
  cctx.beginPath();
  for (let i = 0; i < numAxes; i++) {
    const angle = i * angleStep - Math.PI / 2;
    const valRatio = values[i] / 100.0;
    const r = radius * valRatio;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    if (i === 0) cctx.moveTo(x, y);
    else cctx.lineTo(x, y);
  }
  cctx.closePath();
  cctx.fillStyle = "rgba(56, 189, 248, 0.25)";
  cctx.fill();
  cctx.strokeStyle = "#38bdf8";
  cctx.lineWidth = 2;
  cctx.stroke();
}

let currentHeatmapMode = "density"; // "density" or "delta_wr"

function renderHeatmap(heroName) {
  const data = HERO_ANALYTICS_DATA[heroName] || HERO_ANALYTICS_DATA["Paladin"];
  const chartCanvas = document.getElementById("heatmapCanvas");
  if (!chartCanvas) return;
  const cctx = chartCanvas.getContext("2d");
  const size = chartCanvas.width;
  const squareSize = size / 8;

  cctx.clearRect(0, 0, size, size);

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const isLight = (r + c) % 2 === 0;
      cctx.fillStyle = isLight ? "#21262d" : "#161b22";
      cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
    }
  }

  if (currentHeatmapMode === "density") {
    // Draw hotspot glows (density of presence/activity)
    const hotspots = data.heatmapHotspots || [[3, 3], [3, 4], [4, 3], [4, 4]];
    hotspots.forEach(([r, c]) => {
      cctx.fillStyle = "rgba(239, 68, 68, 0.65)";
      cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
      cctx.strokeStyle = "#f87171";
      cctx.lineWidth = 1.5;
      cctx.strokeRect(c * squareSize, r * squareSize, squareSize, squareSize);
    });
  } else {
    // Draw Delta Win Rate (Opta / LoL spatial efficiency: green = +delta WR, red = -delta WR)
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const isHotspot = (data.heatmapHotspots || []).some(([hr, hc]) => hr === r && hc === c);
        const centerDist = Math.abs(r - 3.5) + Math.abs(c - 3.5);
        let delta = 0;
        if (isHotspot) {
          delta = 0.05 + (4 - centerDist) * 0.01;
        } else if (centerDist > 4.5) {
          delta = -0.04 - (centerDist - 4.5) * 0.01;
        } else {
          delta = (3.5 - centerDist) * 0.008;
        }

        if (delta > 0.02) {
          const alpha = Math.min(0.75, Math.max(0.2, delta * 8));
          cctx.fillStyle = `rgba(34, 197, 94, ${alpha.toFixed(2)})`;
          cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
          cctx.strokeStyle = "#4ade80";
          cctx.lineWidth = 1;
          cctx.strokeRect(c * squareSize, r * squareSize, squareSize, squareSize);
        } else if (delta < -0.02) {
          const alpha = Math.min(0.75, Math.max(0.2, Math.abs(delta) * 8));
          cctx.fillStyle = `rgba(239, 68, 68, ${alpha.toFixed(2)})`;
          cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
          cctx.strokeStyle = "#f87171";
          cctx.lineWidth = 1;
          cctx.strokeRect(c * squareSize, r * squareSize, squareSize, squareSize);
        }
      }
    }
  }
}

function renderSquareHeatmap(hotspots) {
  const selHero = document.getElementById("analyticsHeroSelect") ? document.getElementById("analyticsHeroSelect").value : "Paladin";
  renderHeatmap(selHero);
}

function updateHeroAnalyticsDisplay(heroName) {
  const data = HERO_ANALYTICS_DATA[heroName] || HERO_ANALYTICS_DATA["Paladin"];
  const derivedEl = document.getElementById("analyticsDerivedClasses");
  if (derivedEl) derivedEl.textContent = data.classes.join(" • ");

  const effEl = document.getElementById("analyticsCostEfficiency");
  if (effEl) effEl.textContent = data.efficiency;

  const riotBadge = document.getElementById("analyticsRiotBadge");
  if (riotBadge) {
    if (data.riotStatus === "STRONG_FOR_COST") {
      riotBadge.textContent = `Forte para o Custo (CIR: ${data.cir || 1.12}x)`;
      riotBadge.style.background = "#065f46";
      riotBadge.style.color = "#34d399";
    } else if (data.riotStatus === "OVERPRICED") {
      riotBadge.textContent = `Sobre-precificado (CIR: ${data.cir || 0.75}x)`;
      riotBadge.style.background = "#78350f";
      riotBadge.style.color = "#fbbf24";
    } else {
      riotBadge.textContent = `Equilibrado (CIR: ${data.cir || 1.02}x)`;
      riotBadge.style.background = "#1e3a8a";
      riotBadge.style.color = "#60a5fa";
    }
  }

  const wrEl = document.getElementById("analyticsWinRate");
  if (wrEl) wrEl.textContent = data.winRate || "50.0%";

  const prEl = document.getElementById("analyticsPresenceRate");
  if (prEl) prEl.textContent = data.presenceRate || "16.0%";

  const powerEl = document.getElementById("analyticsPowerTiles");
  if (powerEl && data.powerTiles) powerEl.innerHTML = data.powerTiles.join("<br>");

  const vulnEl = document.getElementById("analyticsVulnerableTiles");
  if (vulnEl && data.vulnerableTiles) vulnEl.innerHTML = data.vulnerableTiles.join("<br>");

  const synEl = document.getElementById("analyticsSynergies");
  if (synEl && data.topSynergies) {
    synEl.innerHTML = data.topSynergies.map(s => `${s.hero} (${s.delta})`).join("<br>");
  }

  const counterEl = document.getElementById("analyticsCounters");
  if (counterEl && data.topCounters) {
    counterEl.innerHTML = data.topCounters.map(c => `${c.hero} (${c.delta})`).join("<br>");
  }

  const openEl = document.getElementById("openingRating");
  if (openEl) openEl.textContent = data.phases.opening;
  const midEl = document.getElementById("midgameRating");
  if (midEl) midEl.textContent = data.phases.midgame;
  const endEl = document.getElementById("endgameRating");
  if (endEl) endEl.textContent = data.phases.endgame;

  renderRadarChart(data.radar);
  renderHeatmap(heroName);
}

function renderCentipawnChart(evals) {
  const chartCanvas = document.getElementById("evalChartCanvas");
  if (!chartCanvas) return;
  const cctx = chartCanvas.getContext("2d");
  const w = chartCanvas.width;
  const h = chartCanvas.height;
  cctx.clearRect(0, 0, w, h);

  cctx.fillStyle = "#161b22";
  cctx.fillRect(0, 0, w, h);

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

// --- Navigation Tabs & Panels ---
function hideAllPanels() {
  document.getElementById("playPanel").style.display = "none";
  document.getElementById("academyPanel").style.display = "none";
  document.getElementById("puzzlesPanel").style.display = "none";
  document.getElementById("leaderboardPanel").style.display = "none";
  document.getElementById("reviewPanel").style.display = "none";
  document.getElementById("analyticsPanel").style.display = "none";

  document.querySelectorAll(".nav-btn").forEach(btn => btn.classList.remove("active"));
}

document.getElementById("tabPlay").addEventListener("click", () => {
  hideAllPanels();
  document.getElementById("playPanel").style.display = "block";
  document.getElementById("tabPlay").classList.add("active");
  isAcademyMode = false;
  drawBoard();
});

document.getElementById("tabAcademy").addEventListener("click", () => {
  hideAllPanels();
  document.getElementById("academyPanel").style.display = "block";
  document.getElementById("tabAcademy").classList.add("active");
  loadAcademyLesson(document.getElementById("heroSelect").value || "paladin");
});

document.getElementById("tabAnalytics").addEventListener("click", () => {
  hideAllPanels();
  document.getElementById("analyticsPanel").style.display = "block";
  document.getElementById("tabAnalytics").classList.add("active");
  isAcademyMode = false;
  const selHero = document.getElementById("analyticsHeroSelect").value || "Paladin";
  updateHeroAnalyticsDisplay(selHero);
});

document.getElementById("tabPuzzles").addEventListener("click", async () => {
  hideAllPanels();
  document.getElementById("puzzlesPanel").style.display = "block";
  document.getElementById("tabPuzzles").classList.add("active");
  isAcademyMode = false;
  loadPuzzles();
});

document.getElementById("tabLeaderboard").addEventListener("click", async () => {
  hideAllPanels();
  document.getElementById("leaderboardPanel").style.display = "block";
  document.getElementById("tabLeaderboard").classList.add("active");
  isAcademyMode = false;
  loadLeaderboard();
});

document.getElementById("tabReview").addEventListener("click", () => {
  hideAllPanels();
  document.getElementById("reviewPanel").style.display = "block";
  document.getElementById("tabReview").classList.add("active");
  isAcademyMode = false;
  renderCentipawnChart(evalHistory);
});

document.getElementById("btnGameReview").addEventListener("click", () => {
  hideAllPanels();
  document.getElementById("reviewPanel").style.display = "block";
  document.getElementById("tabReview").classList.add("active");
  isAcademyMode = false;
  renderCentipawnChart(evalHistory);
});

document.getElementById("heroSelect").addEventListener("change", (e) => {
  loadAcademyLesson(e.target.value);
});

document.getElementById("btnStartLesson").addEventListener("click", () => {
  const heroKey = document.getElementById("heroSelect").value;
  loadAcademyLesson(heroKey);
});

document.getElementById("analyticsHeroSelect").addEventListener("change", (e) => {
  updateHeroAnalyticsDisplay(e.target.value);
});

const btnDensity = document.getElementById("btnHeatmapDensity");
const btnDeltaWR = document.getElementById("btnHeatmapDeltaWR");
if (btnDensity) {
  btnDensity.addEventListener("click", () => {
    currentHeatmapMode = "density";
    btnDensity.style.background = "#0284c7";
    btnDensity.style.color = "white";
    if (btnDeltaWR) {
      btnDeltaWR.style.background = "#334155";
      btnDeltaWR.style.color = "#cbd5e1";
    }
    const selHero = document.getElementById("analyticsHeroSelect") ? document.getElementById("analyticsHeroSelect").value : "Paladin";
    renderHeatmap(selHero);
  });
}
if (btnDeltaWR) {
  btnDeltaWR.addEventListener("click", () => {
    currentHeatmapMode = "delta_wr";
    btnDeltaWR.style.background = "#0284c7";
    btnDeltaWR.style.color = "white";
    if (btnDensity) {
      btnDensity.style.background = "#334155";
      btnDensity.style.color = "#cbd5e1";
    }
    const selHero = document.getElementById("analyticsHeroSelect") ? document.getElementById("analyticsHeroSelect").value : "Paladin";
    renderHeatmap(selHero);
  });
}

// Emote buttons
document.querySelectorAll(".btn-emote").forEach((btn) => {
  btn.addEventListener("click", () => {
    const emote = btn.dataset.emote;
    showEmoteNotification(`Tu: ${btn.textContent}`);
  });
});

function showEmoteNotification(text) {
  const el = document.getElementById("emoteNotification");
  el.textContent = text;
  setTimeout(() => { if (el.textContent === text) el.textContent = ""; }, 3000);
}

// Game Actions
document.getElementById("btnResign").addEventListener("click", () => {
  isGameOver = true;
  showPostGameButtons();
  playChime("stun");
  alert("Partida terminada por desistência.");
});

document.getElementById("btnRematch").addEventListener("click", () => {
  initDefaultBoard();
  drawBoard();
  whiteSeconds = 600;
  blackSeconds = 600;
  updateClockDisplays();
  startClock();
  alert("Desforra iniciada! Boa sorte no tabuleiro!");
});

// Board Theme Switcher
const boardThemeSelect = document.getElementById("boardThemeSelect");
if (boardThemeSelect) {
  boardThemeSelect.addEventListener("change", (e) => {
    currentTheme = e.target.value;
    drawBoard();
  });
}

// Tactical Puzzles UI Handlers
const btnLoadPuzzle = document.getElementById("btnLoadPuzzle");
if (btnLoadPuzzle) {
  btnLoadPuzzle.addEventListener("click", () => {
    const pzSelect = document.getElementById("puzzleSelect");
    if (pzSelect) setupPuzzle(pzSelect.value);
  });
}

const puzzleSelectEl = document.getElementById("puzzleSelect");
if (puzzleSelectEl) {
  puzzleSelectEl.addEventListener("change", (e) => {
    setupPuzzle(e.target.value);
  });
}

const btnPuzzleHint = document.getElementById("btnPuzzleHint");
if (btnPuzzleHint) {
  btnPuzzleHint.addEventListener("click", () => {
    if (!currentPuzzle) return;
    const banner = document.getElementById("puzzleStatusBanner");
    if (banner) {
      banner.style.display = "block";
      banner.style.background = "rgba(245, 158, 11, 0.2)";
      banner.style.border = "1px solid #f59e0b";
      banner.style.color = "#fbbf24";
      banner.innerHTML = `<strong>💡 Dica:</strong> ${currentPuzzle.hint}`;
    }
  });
}

const btnNextPuzzle = document.getElementById("btnNextPuzzle");
if (btnNextPuzzle) {
  btnNextPuzzle.addEventListener("click", () => {
    if (!currentPuzzle) return;
    const curIdx = PUZZLES.findIndex(p => p.puzzle_id === currentPuzzle.puzzle_id);
    const nextIdx = (curIdx + 1) % PUZZLES.length;
    const nextPz = PUZZLES[nextIdx];
    const pzSelect = document.getElementById("puzzleSelect");
    if (pzSelect) pzSelect.value = nextPz.puzzle_id;
    setupPuzzle(nextPz.puzzle_id);
  });
}

document.getElementById("btnStartGame").addEventListener("click", () => {
  const mode = document.getElementById("modeSelect").value;
  boardGrid = mode === "grand_10x10" ? 10 : 8;
  initDefaultBoard();
  drawBoard();
  const tcSelect = document.getElementById("timeControlSelect");
  const tcVal = tcSelect ? tcSelect.value : "rapid_10_0";
  let initialSeconds = 600;
  if (tcVal === "bullet_1_0") initialSeconds = 60;
  else if (tcVal === "blitz_3_2") initialSeconds = 180;
  else if (tcVal === "blitz_5_0") initialSeconds = 300;
  else if (tcVal === "rapid_10_0") initialSeconds = 600;
  else if (tcVal === "rapid_15_10") initialSeconds = 900;
  whiteSeconds = initialSeconds;
  blackSeconds = initialSeconds;
  updateClockDisplays();
  startClock();
});

// Leaderboard and Puzzles Data
async function loadLeaderboard() {
  const tbody = document.getElementById("leaderboardBody");
  tbody.innerHTML = "<tr><td colspan='4' style='text-align:center;'>A carregar classificações...</td></tr>";
  try {
    const res = await fetch("/api/leaderboard");
    if (res.ok) {
      const data = await res.json();
      const entries = data.leaderboard || [];
      tbody.innerHTML = "";
      if (entries.length === 0) {
        tbody.innerHTML = "<tr><td colspan='4' style='text-align:center; color:#94a3b8;'>Nenhum registo no ranking ainda.</td></tr>";
        return;
      }
      entries.forEach((entry, idx) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${idx + 1}</td>
          <td><strong>${entry.player_name || entry.player_id}</strong></td>
          <td>${entry.rating}</td>
          <td>${entry.wins || 0}/${entry.losses || 0}</td>
        `;
        tbody.appendChild(tr);
      });
      return;
    }
  } catch (err) {
    console.warn("Could not fetch remote leaderboard, displaying local fallback:", err);
  }

  // Fallback if offline or running static standalone
  tbody.innerHTML = "";
  const defaultEntries = [
    { rank: 1, username: "Ares Stockfish Master", rating: 2650, wins: 412, losses: 18 },
    { rank: 2, username: "Grandmaster_Vanguard", rating: 2340, wins: 280, losses: 65 },
    { rank: 3, username: "ShadowStriker", rating: 2180, wins: 210, losses: 80 },
    { rank: 4, username: "NecroKing", rating: 1950, wins: 175, losses: 92 },
    { rank: 5, username: "TacticalRanger", rating: 1820, wins: 140, losses: 110 }
  ];
  defaultEntries.forEach((entry) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${entry.rank}</td>
      <td><strong>${entry.username}</strong></td>
      <td>${entry.rating}</td>
      <td>${entry.wins}/${entry.losses}</td>
    `;
    tbody.appendChild(tr);
  });
}

const PUZZLES = [
  {
    puzzle_id: "pz1",
    title: "O Salto Duplo do Dragoon",
    rating: 1350,
    description: "O Dragoon branco na casa d4 pode saltar sobre o bloqueio e aplicar o golpe letal final no Paladino preto atordoado em f6.",
    hint: "Usa o padrão em 'L' do Dragoon para saltar por cima das peças e atingir o alvo enfraquecido.",
    board: [
      { r: 4, c: 3, name: "Dragoon", team: "brancas", stun: 0 },
      { r: 4, c: 4, name: "Bone", team: "brancas", stun: 0 },
      { r: 2, c: 5, name: "Paladin", team: "pretas", stun: 1 },
      { r: 1, c: 4, name: "FrostMage", team: "pretas", stun: 0 }
    ],
    solution: { fromR: 4, fromC: 3, toR: 2, toC: 5 },
    explanation: "Excelente! O Dragoon saltou sobre a barreira e eliminou instantaneamente o Paladino atordoado."
  },
  {
    puzzle_id: "pz2",
    title: "A Lâmina Fantasma na Cripta",
    rating: 1520,
    description: "A Shadowblade pode atravessar tropas em diagonal com a sua mobilidade espectral para eliminar o FrostMage atordoado em b7.",
    hint: "A Shadowblade ignora peças intermediárias em trajetórias diagonais.",
    board: [
      { r: 4, c: 4, name: "Shadowblade", team: "brancas", stun: 0 },
      { r: 3, c: 3, name: "Bone", team: "brancas", stun: 0 },
      { r: 2, c: 2, name: "Bone", team: "pretas", stun: 0 },
      { r: 1, c: 1, name: "FrostMage", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 4, fromC: 4, toR: 1, toC: 1 },
    explanation: "Perfeito! A Shadowblade atravessou duas unidades na diagonal para desferir o golpe letal."
  },
  {
    puzzle_id: "pz3",
    title: "As Asas Celestes da Valkyrie",
    rating: 1650,
    description: "A recém-chegada Valkyrie voa até 3 casas ignorando obstáculos terrestres. Encontra o ângulo para abater o Lich atordoado.",
    hint: "A Valkyrie salta sobre unidades terrestres até 3 casas em qualquer direção.",
    board: [
      { r: 5, c: 2, name: "Valkyrie", team: "brancas", stun: 0 },
      { r: 4, c: 2, name: "StoneWall", team: "pretas", stun: 0 },
      { r: 3, c: 2, name: "Bone", team: "pretas", stun: 0 },
      { r: 2, c: 2, name: "Lich", team: "pretas", stun: 2 }
    ],
    solution: { fromR: 5, fromC: 2, toR: 2, toC: 2 },
    explanation: "Brilhante! O voo espectral da Valkyrie sobrevoou a parede e o lacaio, liquidando o Lich."
  },
  {
    puzzle_id: "pz4",
    title: "Rajada Rúnica do Arcanist",
    rating: 1720,
    description: "O Arcanist canaliza a sua Rajada Arcana ortogonal até 3 casas. Elimina a unidade inimiga vulnerável em linha reta.",
    hint: "O Arcanist ataca em linha reta ortogonal até 3 casas com magia perfurante.",
    board: [
      { r: 5, c: 3, name: "Arcanist", team: "brancas", stun: 0 },
      { r: 2, c: 3, name: "Stormcaller", team: "pretas", stun: 1 },
      { r: 3, c: 5, name: "BoneLord", team: "pretas", stun: 0 }
    ],
    solution: { fromR: 5, fromC: 3, toR: 2, toC: 3 },
    explanation: "Cirúrgico! A Rajada Arcana do Arcanist atingiu o Stormcaller à distância sem expor o mago."
  },
  {
    puzzle_id: "pz5",
    title: "A Estocada Precisa do Duelist",
    rating: 1780,
    description: "O Duelist especializa-se em trespassar diagonais até 2 casas. Elimina o berserker atordoado na retaguarda.",
    hint: "Move e ataca em diagonal até 2 casas com precisão cirúrgica.",
    board: [
      { r: 4, c: 2, name: "Duelist", team: "brancas", stun: 0 },
      { r: 2, c: 4, name: "Berserker", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 4, fromC: 2, toR: 2, toC: 4 },
    explanation: "Sensacional! A estocada diagonal do Duelist finalizou o adversário com eficiência perfeita."
  },
  {
    puzzle_id: "pz6",
    title: "O Bastião Inabalável do Warden",
    rating: 1850,
    description: "O Warden controla a linha de frente. Avança para neutralizar e derrubar a ameaça que invadiu o campo aliado.",
    hint: "O Warden move-se 1 casa em qualquer direção e ataca ortogonalmente com golpe de escudo.",
    board: [
      { r: 3, c: 3, name: "Warden", team: "brancas", stun: 0 },
      { r: 2, c: 3, name: "Nightshade", team: "pretas", stun: 1 }
    ],
    solution: { fromR: 3, fromC: 3, toR: 2, toC: 3 },
    explanation: "Inabalável! O golpe de escudo do Warden encerrou o avanço inimigo na linha de frente."
  }
];

let isPuzzleMode = false;
let currentPuzzle = null;
let puzzleUserElo = 1200;
let puzzleStreak = 0;
const PUZZLE_STORAGE_KEY = "redwar_puzzle_stats_v1";

function loadPuzzleStats() {
  try {
    if (typeof localStorage !== "undefined" && localStorage.getItem) {
      const raw = localStorage.getItem(PUZZLE_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (typeof parsed.elo === "number") puzzleUserElo = parsed.elo;
        if (typeof parsed.streak === "number") puzzleStreak = parsed.streak;
      }
    }
  } catch (e) {
    console.warn("Failed to load puzzle stats:", e);
  }
}

function savePuzzleStats() {
  try {
    if (typeof localStorage !== "undefined" && localStorage.setItem) {
      localStorage.setItem(PUZZLE_STORAGE_KEY, JSON.stringify({
        elo: puzzleUserElo,
        streak: puzzleStreak,
        lastUpdated: new Date().toISOString()
      }));
    }
  } catch (e) {
    console.warn("Failed to save puzzle stats:", e);
  }
}

function updatePuzzleStatsUI() {
  const eloEl = document.getElementById("puzzleElo");
  const streakEl = document.getElementById("puzzleStreak");
  if (eloEl) eloEl.textContent = puzzleUserElo;
  if (streakEl) streakEl.textContent = `🔥 ${puzzleStreak}`;
}

function loadPuzzles() {
  loadPuzzleStats();
  const select = document.getElementById("puzzleSelect");
  if (!select) return;
  select.innerHTML = "";
  PUZZLES.forEach((pz, idx) => {
    const opt = document.createElement("option");
    opt.value = pz.puzzle_id;
    opt.textContent = `${pz.title} (${pz.rating} ELO)`;
    select.appendChild(opt);
  });
  updatePuzzleStatsUI();
  setupPuzzle(PUZZLES[0].puzzle_id);
}

function setupPuzzle(puzzleId) {
  loadPuzzleStats();
  const pz = PUZZLES.find(p => p.puzzle_id === puzzleId) || PUZZLES[0];
  currentPuzzle = pz;
  isPuzzleMode = true;
  isAcademyMode = false;
  boardGrid = 8;
  boardData = Array(8).fill(null).map(() => Array(8).fill(null));
  selectedSquare = null;
  currentLegalActions = [];
  currentTurn = "white";

  pz.board.forEach(p => {
    boardData[p.r][p.c] = { name: p.name, team: p.team, stun: p.stun || 0 };
  });

  const desc = document.getElementById("puzzleDesc");
  if (desc) desc.textContent = pz.description;
  const banner = document.getElementById("puzzleStatusBanner");
  if (banner) banner.style.display = "none";
  const nextBtn = document.getElementById("btnNextPuzzle");
  if (nextBtn) nextBtn.style.display = "none";

  drawBoard();
  const cp = computeBoardCentipawns(boardData);
  updateLiveEvalBar(cp);
  updatePuzzleStatsUI();
}

// --- Security & Identity Authentication Management ---
const AUTH_STORAGE_KEY = "redwar_auth_session_v2";

function loadUserAuthSession() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.warn("Failed to load auth session:", e);
  }
  const guestId = "guest_" + Math.random().toString(36).substring(2, 8);
  return {
    mode: "guest",
    playerId: guestId,
    username: "Convidado_" + guestId.substring(6, 10).toUpperCase(),
    elo: 1200,
    isAnonymous: true
  };
}

let currentAuthSession = loadUserAuthSession();

function updateUserAuthUI() {
  const badge = document.getElementById("userAuthBadge");
  const whiteName = document.getElementById("whitePlayerName");
  const whiteElo = document.getElementById("whitePlayerElo");

  let modeIcon = "👤";
  if (currentAuthSession.mode === "google_oidc") modeIcon = "🟢";
  else if (currentAuthSession.mode === "studio_dedicated") modeIcon = "🔐";

  if (badge) badge.textContent = `${modeIcon} ${currentAuthSession.username} (${currentAuthSession.elo})`;
  if (whiteName) whiteName.textContent = currentAuthSession.username;
  if (whiteElo) whiteElo.textContent = `(${currentAuthSession.elo})`;

  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(currentAuthSession));
  } catch (e) {}
}

const authModal = document.getElementById("authModal");
const btnOpenAuth = document.getElementById("btnOpenAuthModal");
const btnCloseAuth = document.getElementById("btnCloseAuthModal");

if (btnOpenAuth && authModal) {
  btnOpenAuth.addEventListener("click", () => { authModal.style.display = "flex"; });
}
if (btnCloseAuth && authModal) {
  btnCloseAuth.addEventListener("click", () => { authModal.style.display = "none"; });
}

const btnAuthGuest = document.getElementById("btnAuthGuest");
if (btnAuthGuest) {
  btnAuthGuest.addEventListener("click", () => {
    const guestId = "guest_" + Math.random().toString(36).substring(2, 8);
    currentAuthSession = {
      mode: "guest",
      playerId: guestId,
      username: "Convidado_" + guestId.substring(6, 10).toUpperCase(),
      elo: 1200,
      isAnonymous: true
    };
    updateUserAuthUI();
    authModal.style.display = "none";
  });
}

const btnAuthGoogle = document.getElementById("btnAuthGoogle");
if (btnAuthGoogle) {
  btnAuthGoogle.addEventListener("click", () => {
    alert("A autenticação federada Google OIDC requer conexão a um servidor RedWar ativo com o módulo StudioAuth configurado.\n\nNo cliente estático local, o jogo mantém o seu progresso no perfil Convidado Local.");
    authModal.style.display = "none";
  });
}

const btnAuthDedicated = document.getElementById("btnAuthDedicated");
if (btnAuthDedicated) {
  btnAuthDedicated.addEventListener("click", () => {
    const userInput = document.getElementById("authDedicatedUser");
    const username = userInput && userInput.value.trim() ? userInput.value.trim() : "JogadorLocal";

    currentAuthSession = {
      mode: "guest",
      playerId: "local_" + Math.random().toString(36).substring(2, 10),
      username: username,
      elo: currentAuthSession.elo >= 1200 ? currentAuthSession.elo : 1200,
      isAnonymous: true,
      connectedAt: new Date().toISOString()
    };
    updateUserAuthUI();
    authModal.style.display = "none";
    alert(`Perfil local atualizado como "${username}".\n\nProgresso salvo localmente no seu navegador.`);
  });
}

// Initial Boot
initDefaultBoard();
drawBoard();
updateClockDisplays();
updateUserAuthUI();
loadPuzzleStats();

// --- RedWar Notation (RWN) Export & Import Engine ---
function exportRwn() {
  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, ".");
  let rwn = `[Event "RedWar 2.0 Match"]\n[Site "RedWar Platform"]\n[Date "${dateStr}"]\n`;
  rwn += `[White "Jogador"]\n[Black "Ares AI"]\n`;
  rwn += `[Roster "Paladin,Shadowblade,Stormcaller,Valkyrie,Arcanist,Duelist,Warden,Illusionist,Marksman"]\n\n`;

  if (!classifiedMoves || classifiedMoves.length === 0) {
    rwn += "1. { Partida sem movimentos registrados }";
  } else {
    for (let i = 0; i < classifiedMoves.length; i += 2) {
      const moveNum = Math.floor(i / 2) + 1;
      const whiteMove = classifiedMoves[i] ? classifiedMoves[i].moveText : "";
      const blackMove = classifiedMoves[i + 1] ? classifiedMoves[i + 1].moveText : "";
      rwn += `${moveNum}. ${whiteMove} ${blackMove} `.trim() + "\n";
    }
  }

  const ta = document.getElementById("rwnTextArea");
  if (ta) {
    ta.value = rwn;
    ta.style.display = "block";
    if (navigator.clipboard) {
      navigator.clipboard.writeText(rwn).catch(() => {});
    }
  }
  const notif = document.getElementById("rwnNotification");
  if (notif) {
    notif.textContent = "✅ Notação RWN exportada e copiada para a área de transferência!";
    notif.style.display = "block";
    setTimeout(() => { if (notif) notif.style.display = "none"; }, 4000);
  }
  return rwn;
}

function renderGameReviewPanel() {
  if (typeof document === "undefined" || !document.getElementById || !document.createElement) return;
  const list = document.getElementById("reviewMovesList");
  if (list && list.appendChild) {
    list.innerHTML = "";
    classifiedMoves.forEach((m, idx) => {
      const item = document.createElement("div");
      item.style.display = "flex";
      item.style.justifyContent = "space-between";
      item.style.padding = "4px 8px";
      item.style.cursor = "pointer";
      item.style.borderRadius = "4px";
      item.title = "Clique para ouvir o som da classificação tática";
      item.innerHTML = `<span>${idx + 1}. ${m.moveText}</span> <span class="${m.badgeClass}">${m.label}</span>`;
      if (item.addEventListener) {
        item.addEventListener("click", () => {
          if (m.classification === "brilliant") playChime("brilliant");
          else if (m.classification === "best" || m.classification === "great") playChime("best");
          else if (m.classification === "blunder") playChime("blunder");
          else if (m.classification === "mistake" || m.classification === "inaccuracy") playChime("mistake");
        });
      }
      list.appendChild(item);
    });
  }
  const counts = { brilliant: 0, great: 0, best: 0, inaccuracy: 0, mistake: 0, blunder: 0 };
  classifiedMoves.forEach(m => {
    if (counts[m.classification] !== undefined) counts[m.classification]++;
  });
  const elB = document.getElementById("countBrilliant"); if (elB) elB.textContent = counts.brilliant;
  const elG = document.getElementById("countGreat"); if (elG) elG.textContent = counts.great;
  const elBe = document.getElementById("countBest"); if (elBe) elBe.textContent = counts.best;
  const elI = document.getElementById("countInacc"); if (elI) elI.textContent = counts.inaccuracy;
  const elM = document.getElementById("countMistake"); if (elM) elM.textContent = counts.mistake;
  const elBl = document.getElementById("countBlunder"); if (elBl) elBl.textContent = counts.blunder;
}

function importRwn(rwnText) {
  if (!rwnText || typeof rwnText !== "string") return false;
  const lines = rwnText.split("\n");
  const moveRegex = /^\d+\.\s+(.*)/;
  const importedList = [];

  for (const line of lines) {
    const trimmed = line.trim();
    const match = trimmed.match(moveRegex);
    if (match) {
      const parts = match[1].split(/\s+/);
      if (parts[0]) importedList.push({ moveText: parts[0], team: "brancas", classification: "best", badgeClass: "badge-best", label: "Melhor" });
      if (parts[1]) importedList.push({ moveText: parts[1], team: "pretas", classification: "best", badgeClass: "badge-best", label: "Melhor" });
    }
  }

  if (importedList.length > 0) {
    classifiedMoves = importedList;
    renderGameReviewPanel();
    const notif = document.getElementById("rwnNotification");
    if (notif) {
      notif.textContent = `✅ ${importedList.length} lances carregados com sucesso no Game Review!`;
      notif.style.display = "block";
      setTimeout(() => { if (notif) notif.style.display = "none"; }, 4000);
    }
    return true;
  }
  return false;
}

// Audio Toggle Logic
let soundEnabled = true;
function toggleAudio() {
  soundEnabled = !soundEnabled;
  const btn = document.getElementById("btnToggleAudio");
  if (btn) {
    btn.textContent = soundEnabled ? "🔊 Som: Ligado" : "🔇 Som: Desligado";
    btn.style.color = soundEnabled ? "#cbd5e1" : "#94a3b8";
  }
}

if (typeof document !== "undefined" && document.getElementById) {
  const btnExp = document.getElementById("btnExportRwn");
  if (btnExp) btnExp.addEventListener("click", exportRwn);

  const btnImp = document.getElementById("btnImportRwn");
  if (btnImp) {
    btnImp.addEventListener("click", () => {
      const ta = document.getElementById("rwnTextArea");
      if (ta) {
        if (ta.style.display === "none") {
          ta.style.display = "block";
          ta.focus();
        } else {
          importRwn(ta.value);
        }
      }
    });
  }

  const btnSnd = document.getElementById("btnToggleAudio");
  if (btnSnd) btnSnd.addEventListener("click", toggleAudio);
}
