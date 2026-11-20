# tools/scripts/update_web_analytics_data.py
"""Update deploy/web/app.js with 30-hero analytics, Riot balance badge, and dual-mode heatmap."""
import json
import re
from pathlib import Path

APP_JS = Path("deploy/web/app.js")

HERO_EXTRAS = {
    "Paladin": {
        "classes": ["Vanguard (Tanque/Âncora)", "Disruptor Secundário"],
        "cost": 16,
        "efficiency": "1.04x (Equilibrado)",
        "cir": 1.04,
        "riotStatus": "BALANCED",
        "winRate": "51.2%",
        "presenceRate": "18.5%",
        "radar": {"zone": 88, "lethality": 62, "cc": 74, "mobility": 55, "surv": 92, "endg": 78},
        "phases": {"opening": 70, "midgame": 92, "endgame": 84},
        "heatmapHotspots": [[3, 3], [3, 4], [4, 3], [4, 4], [2, 3], [2, 4]],
        "powerTiles": ["d5 (+4.2%)", "e5 (+4.1%)", "d4 (+3.8%)"],
        "vulnerableTiles": ["a1 (-6.8%)", "h8 (-6.4%)", "a8 (-5.9%)"],
        "topSynergies": [{"hero": "Valkyrie", "delta": "+5.2%"}, {"hero": "Warden", "delta": "+4.1%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-6.4%"}, {"hero": "Duelist", "delta": "-4.8%"}],
    },
    "Shadowblade": {
        "classes": ["Striker (Flanqueador/Assassino)", "Finalizador Ágil"],
        "cost": 18,
        "efficiency": "1.08x (Equilibrado)",
        "cir": 1.08,
        "riotStatus": "BALANCED",
        "winRate": "52.4%",
        "presenceRate": "21.0%",
        "radar": {"zone": 45, "lethality": 94, "cc": 50, "mobility": 96, "surv": 65, "endg": 90},
        "phases": {"opening": 60, "midgame": 85, "endgame": 95},
        "heatmapHotspots": [[1, 2], [1, 5], [2, 1], [2, 6], [5, 2], [5, 5]],
        "powerTiles": ["c6 (+5.8%)", "f6 (+5.5%)", "c3 (+4.9%)"],
        "vulnerableTiles": ["d4 (-7.1%)", "e4 (-6.8%)", "d5 (-6.2%)"],
        "topSynergies": [{"hero": "FrostMage", "delta": "+6.1%"}, {"hero": "Timekeeper", "delta": "+4.8%"}],
        "topCounters": [{"hero": "Paladin", "delta": "-7.2%"}, {"hero": "Warden", "delta": "-5.9%"}],
    },
    "Stormcaller": {
        "classes": ["Artillery (Artilharia de Longo Alcance)", "Controlador Zonal"],
        "cost": 17,
        "efficiency": "0.98x (Equilibrado)",
        "cir": 0.98,
        "riotStatus": "BALANCED",
        "winRate": "49.6%",
        "presenceRate": "16.2%",
        "radar": {"zone": 92, "lethality": 85, "cc": 80, "mobility": 40, "surv": 58, "endg": 75},
        "phases": {"opening": 85, "midgame": 90, "endgame": 70},
        "heatmapHotspots": [[6, 1], [6, 2], [6, 5], [6, 6], [5, 3], [5, 4]],
        "powerTiles": ["b2 (+5.1%)", "g2 (+4.9%)", "d3 (+4.2%)"],
        "vulnerableTiles": ["d5 (-6.5%)", "e5 (-6.1%)", "c4 (-5.8%)"],
        "topSynergies": [{"hero": "Warden", "delta": "+5.4%"}, {"hero": "Paladin", "delta": "+4.5%"}],
        "topCounters": [{"hero": "Shadowblade", "delta": "-7.8%"}, {"hero": "Dragoon", "delta": "-6.2%"}],
    },
    "Dragoon": {
        "classes": ["Striker (Iniciador Móvel)", "Saltador Tático"],
        "cost": 18,
        "efficiency": "1.02x (Equilibrado)",
        "cir": 1.02,
        "riotStatus": "BALANCED",
        "winRate": "50.8%",
        "presenceRate": "17.4%",
        "radar": {"zone": 68, "lethality": 88, "cc": 60, "mobility": 90, "surv": 72, "endg": 82},
        "phases": {"opening": 75, "midgame": 88, "endgame": 80},
        "heatmapHotspots": [[3, 2], [3, 5], [4, 2], [4, 5], [2, 4]],
        "powerTiles": ["c5 (+4.8%)", "f5 (+4.6%)", "e6 (+4.1%)"],
        "vulnerableTiles": ["a1 (-6.2%)", "h1 (-5.8%)", "a8 (-5.4%)"],
        "topSynergies": [{"hero": "Valkyrie", "delta": "+5.8%"}, {"hero": "Stormcaller", "delta": "+4.3%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-6.1%"}, {"hero": "Paladin", "delta": "-5.5%"}],
    },
    "FrostMage": {
        "classes": ["Disruptor (Controlador de Gelo)", "Negação de Área"],
        "cost": 16,
        "efficiency": "1.06x (Equilibrado)",
        "cir": 1.06,
        "riotStatus": "BALANCED",
        "winRate": "51.8%",
        "presenceRate": "19.1%",
        "radar": {"zone": 84, "lethality": 40, "cc": 96, "mobility": 45, "surv": 64, "endg": 85},
        "phases": {"opening": 80, "midgame": 94, "endgame": 82},
        "heatmapHotspots": [[4, 2], [4, 5], [3, 1], [3, 6], [5, 3]],
        "powerTiles": ["c4 (+5.5%)", "f4 (+5.2%)", "d3 (+4.7%)"],
        "vulnerableTiles": ["b7 (-6.8%)", "g7 (-6.3%)", "c8 (-5.9%)"],
        "topSynergies": [{"hero": "Shadowblade", "delta": "+6.5%"}, {"hero": "Marksman", "delta": "+5.7%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-8.2%"}, {"hero": "BoneLord", "delta": "-6.0%"}],
    },
    "BoneLord": {
        "classes": ["Summoner (Invocador/Saturação)", "Âncora de Retaguarda"],
        "cost": 16,
        "efficiency": "1.01x (Equilibrado)",
        "cir": 1.01,
        "riotStatus": "BALANCED",
        "winRate": "50.2%",
        "presenceRate": "15.8%",
        "radar": {"zone": 95, "lethality": 50, "cc": 62, "mobility": 35, "surv": 85, "endg": 70},
        "phases": {"opening": 90, "midgame": 85, "endgame": 65},
        "heatmapHotspots": [[6, 3], [6, 4], [5, 2], [5, 5]],
        "powerTiles": ["d2 (+4.6%)", "e2 (+4.4%)", "c3 (+3.9%)"],
        "vulnerableTiles": ["d6 (-7.0%)", "e6 (-6.6%)", "f5 (-6.1%)"],
        "topSynergies": [{"hero": "Lich", "delta": "+5.9%"}, {"hero": "Bone", "delta": "+4.7%"}],
        "topCounters": [{"hero": "Pyromancer", "delta": "-7.5%"}, {"hero": "Stormcaller", "delta": "-6.8%"}],
    },
    "Hookmaster": {
        "classes": ["Disruptor (Puxador/Reposicionador)", "Vanguard Secundário"],
        "cost": 15,
        "efficiency": "1.05x (Equilibrado)",
        "cir": 1.05,
        "riotStatus": "BALANCED",
        "winRate": "51.5%",
        "presenceRate": "17.6%",
        "radar": {"zone": 80, "lethality": 70, "cc": 88, "mobility": 50, "surv": 80, "endg": 78},
        "phases": {"opening": 72, "midgame": 89, "endgame": 81},
        "heatmapHotspots": [[4, 3], [4, 4], [3, 3], [3, 4]],
        "powerTiles": ["d4 (+5.3%)", "e4 (+5.0%)", "d5 (+4.6%)"],
        "vulnerableTiles": ["a2 (-6.4%)", "h2 (-6.1%)", "a7 (-5.7%)"],
        "topSynergies": [{"hero": "Duelist", "delta": "+5.6%"}, {"hero": "Paladin", "delta": "+4.9%"}],
        "topCounters": [{"hero": "Illusionist", "delta": "-6.9%"}, {"hero": "Marksman", "delta": "-5.8%"}],
    },
    "Timekeeper": {
        "classes": ["Disruptor (Cronomante de Turnos)", "Manipulador Temporal"],
        "cost": 16,
        "efficiency": "1.03x (Equilibrado)",
        "cir": 1.03,
        "riotStatus": "BALANCED",
        "winRate": "51.0%",
        "presenceRate": "16.8%",
        "radar": {"zone": 75, "lethality": 45, "cc": 92, "mobility": 60, "surv": 78, "endg": 88},
        "phases": {"opening": 65, "midgame": 86, "endgame": 92},
        "heatmapHotspots": [[5, 3], [5, 4], [4, 2], [4, 5]],
        "powerTiles": ["d3 (+4.9%)", "e3 (+4.7%)", "c4 (+4.2%)"],
        "vulnerableTiles": ["d7 (-6.8%)", "e7 (-6.4%)", "a4 (-5.9%)"],
        "topSynergies": [{"hero": "Arcanist", "delta": "+5.5%"}, {"hero": "Valkyrie", "delta": "+4.7%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-7.1%"}, {"hero": "Shadowblade", "delta": "-6.4%"}],
    },
    "Ranger": {
        "classes": ["Artillery (Atirador Rápido)", "Supressor Linear"],
        "cost": 14,
        "efficiency": "0.97x (Equilibrado)",
        "cir": 0.97,
        "riotStatus": "BALANCED",
        "winRate": "49.2%",
        "presenceRate": "15.4%",
        "radar": {"zone": 78, "lethality": 75, "cc": 55, "mobility": 65, "surv": 52, "endg": 72},
        "phases": {"opening": 82, "midgame": 78, "endgame": 68},
        "heatmapHotspots": [[6, 2], [6, 5], [7, 3], [7, 4]],
        "powerTiles": ["c2 (+4.7%)", "f2 (+4.5%)", "d1 (+4.0%)"],
        "vulnerableTiles": ["d4 (-6.6%)", "e4 (-6.2%)", "c5 (-5.7%)"],
        "topSynergies": [{"hero": "Warden", "delta": "+5.1%"}, {"hero": "Paladin", "delta": "+4.2%"}],
        "topCounters": [{"hero": "Shadowblade", "delta": "-7.4%"}, {"hero": "Dragoon", "delta": "-6.5%"}],
    },
    "Valkyrie": {
        "classes": ["Striker (Iniciador Aéreo)", "Flanqueador Espectral"],
        "cost": 22,
        "efficiency": "1.09x (Equilibrado)",
        "cir": 1.09,
        "riotStatus": "BALANCED",
        "winRate": "53.2%",
        "presenceRate": "23.4%",
        "radar": {"zone": 72, "lethality": 86, "cc": 60, "mobility": 98, "surv": 70, "endg": 92},
        "phases": {"opening": 78, "midgame": 92, "endgame": 95},
        "heatmapHotspots": [[2, 2], [2, 5], [3, 3], [3, 4], [4, 2], [4, 5]],
        "powerTiles": ["c6 (+6.4%)", "f6 (+6.1%)", "d5 (+5.7%)"],
        "vulnerableTiles": ["a1 (-7.2%)", "h1 (-6.8%)", "a8 (-6.3%)"],
        "topSynergies": [{"hero": "Arcanist", "delta": "+6.8%"}, {"hero": "Paladin", "delta": "+5.4%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-6.7%"}, {"hero": "Marksman", "delta": "-5.8%"}],
    },
    "Arcanist": {
        "classes": ["Artillery (Artilharia Rúnica)", "Controlador Linear"],
        "cost": 23,
        "efficiency": "1.02x (Equilibrado)",
        "cir": 1.02,
        "riotStatus": "BALANCED",
        "winRate": "51.4%",
        "presenceRate": "20.2%",
        "radar": {"zone": 88, "lethality": 92, "cc": 65, "mobility": 50, "surv": 54, "endg": 80},
        "phases": {"opening": 84, "midgame": 90, "endgame": 76},
        "heatmapHotspots": [[6, 3], [6, 4], [5, 2], [5, 5], [4, 3]],
        "powerTiles": ["d2 (+5.6%)", "e2 (+5.3%)", "c3 (+4.8%)"],
        "vulnerableTiles": ["d6 (-7.3%)", "e6 (-6.9%)", "f5 (-6.4%)"],
        "topSynergies": [{"hero": "Valkyrie", "delta": "+6.8%"}, {"hero": "Warden", "delta": "+5.2%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-8.5%"}, {"hero": "Shadowblade", "delta": "-7.1%"}],
    },
    "Duelist": {
        "classes": ["Striker (Esgrimista Diagonal)", "Assassino Cirúrgico"],
        "cost": 24,
        "efficiency": "1.01x (Equilibrado)",
        "cir": 1.01,
        "riotStatus": "BALANCED",
        "winRate": "51.0%",
        "presenceRate": "19.5%",
        "radar": {"zone": 65, "lethality": 90, "cc": 50, "mobility": 82, "surv": 68, "endg": 88},
        "phases": {"opening": 68, "midgame": 88, "endgame": 90},
        "heatmapHotspots": [[3, 3], [3, 4], [4, 3], [4, 4], [2, 4], [5, 3]],
        "powerTiles": ["d5 (+5.2%)", "e4 (+4.9%)", "e6 (+4.5%)"],
        "vulnerableTiles": ["a3 (-6.5%)", "h6 (-6.1%)", "b1 (-5.8%)"],
        "topSynergies": [{"hero": "FrostMage", "delta": "+6.0%"}, {"hero": "Hookmaster", "delta": "+5.1%"}],
        "topCounters": [{"hero": "Paladin", "delta": "-6.8%"}, {"hero": "Warden", "delta": "-6.2%"}],
    },
    "Warden": {
        "classes": ["Vanguard (Âncora Pesada)", "Guardião de Ponto"],
        "cost": 25,
        "efficiency": "1.04x (Equilibrado)",
        "cir": 1.04,
        "riotStatus": "BALANCED",
        "winRate": "52.0%",
        "presenceRate": "22.0%",
        "radar": {"zone": 92, "lethality": 65, "cc": 85, "mobility": 40, "surv": 95, "endg": 82},
        "phases": {"opening": 75, "midgame": 94, "endgame": 86},
        "heatmapHotspots": [[3, 3], [3, 4], [4, 3], [4, 4], [3, 2], [4, 5]],
        "powerTiles": ["d4 (+5.5%)", "e5 (+5.2%)", "c4 (+4.8%)"],
        "vulnerableTiles": ["a1 (-6.9%)", "h8 (-6.5%)", "h1 (-6.1%)"],
        "topSynergies": [{"hero": "Marksman", "delta": "+6.2%"}, {"hero": "Arcanist", "delta": "+5.4%"}],
        "topCounters": [{"hero": "Illusionist", "delta": "-6.5%"}, {"hero": "Stormcaller", "delta": "-5.7%"}],
    },
    "Illusionist": {
        "classes": ["Disruptor (Controlo de Espaço)", "Transpositor Tático"],
        "cost": 27,
        "efficiency": "1.02x (Equilibrado)",
        "cir": 1.02,
        "riotStatus": "BALANCED",
        "winRate": "51.6%",
        "presenceRate": "18.8%",
        "radar": {"zone": 88, "lethality": 72, "cc": 80, "mobility": 85, "surv": 70, "endg": 84},
        "phases": {"opening": 78, "midgame": 89, "endgame": 88},
        "heatmapHotspots": [[3, 3], [3, 4], [4, 3], [4, 4], [2, 3], [5, 4]],
        "powerTiles": ["c6 (+5.4%)", "d5 (+5.1%)", "e4 (+4.7%)"],
        "vulnerableTiles": ["a8 (-6.7%)", "h1 (-6.2%)", "a1 (-5.9%)"],
        "topSynergies": [{"hero": "Duelist", "delta": "+5.8%"}, {"hero": "Marksman", "delta": "+5.0%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-7.6%"}, {"hero": "Shadowblade", "delta": "-6.3%"}],
    },
    "Marksman": {
        "classes": ["Artillery (Atirador Furtivo)", "Finalizador de Linha"],
        "cost": 28,
        "efficiency": "1.05x (Equilibrado)",
        "cir": 1.05,
        "riotStatus": "BALANCED",
        "winRate": "52.8%",
        "presenceRate": "24.5%",
        "radar": {"zone": 85, "lethality": 95, "cc": 60, "mobility": 50, "surv": 58, "endg": 86},
        "phases": {"opening": 80, "midgame": 92, "endgame": 85},
        "heatmapHotspots": [[6, 2], [6, 5], [5, 2], [5, 5], [4, 2], [4, 5]],
        "powerTiles": ["c2 (+6.0%)", "f2 (+5.7%)", "c3 (+5.2%)"],
        "vulnerableTiles": ["d5 (-7.4%)", "e5 (-7.0%)", "d4 (-6.5%)"],
        "topSynergies": [{"hero": "Warden", "delta": "+6.5%"}, {"hero": "FrostMage", "delta": "+5.8%"}],
        "topCounters": [{"hero": "Shadowblade", "delta": "-8.4%"}, {"hero": "Valkyrie", "delta": "-7.2%"}],
    },
    "Bone": {
        "classes": ["Minion (Esqueleto Conjurado)", "Peão de Contenção"],
        "cost": 8,
        "efficiency": "0.95x (Equilibrado)",
        "cir": 0.95,
        "riotStatus": "BALANCED",
        "winRate": "48.5%",
        "presenceRate": "12.0%",
        "radar": {"zone": 40, "lethality": 30, "cc": 20, "mobility": 45, "surv": 35, "endg": 25},
        "phases": {"opening": 60, "midgame": 50, "endgame": 30},
        "heatmapHotspots": [[3, 3], [4, 4]],
        "powerTiles": ["d5 (+3.2%)", "e4 (+3.0%)", "d4 (+2.8%)"],
        "vulnerableTiles": ["a1 (-5.2%)", "h8 (-5.0%)", "h1 (-4.8%)"],
        "topSynergies": [{"hero": "BoneLord", "delta": "+4.5%"}, {"hero": "Lich", "delta": "+3.8%"}],
        "topCounters": [{"hero": "Pyromancer", "delta": "-6.2%"}, {"hero": "Stormcaller", "delta": "-5.5%"}],
    },
    "Berserker": {
        "classes": ["Striker (Fúria Berserk)", "Duelista Agressivo"],
        "cost": 18,
        "efficiency": "1.06x (Equilibrado)",
        "cir": 1.06,
        "riotStatus": "BALANCED",
        "winRate": "51.5%",
        "presenceRate": "18.2%",
        "radar": {"zone": 60, "lethality": 92, "cc": 45, "mobility": 75, "surv": 70, "endg": 85},
        "phases": {"opening": 70, "midgame": 90, "endgame": 88},
        "heatmapHotspots": [[3, 3], [4, 4], [3, 4]],
        "powerTiles": ["d4 (+5.4%)", "e5 (+5.1%)", "e4 (+4.8%)"],
        "vulnerableTiles": ["a2 (-6.5%)", "h7 (-6.2%)", "b8 (-5.8%)"],
        "topSynergies": [{"hero": "Cleric", "delta": "+5.9%"}, {"hero": "FrostMage", "delta": "+5.2%"}],
        "topCounters": [{"hero": "Paladin", "delta": "-6.8%"}, {"hero": "Hookmaster", "delta": "-5.9%"}],
    },
    "Pyromancer": {
        "classes": ["Artillery (Mago Ígneo)", "Queimadura Zonal"],
        "cost": 16,
        "efficiency": "1.03x (Equilibrado)",
        "cir": 1.03,
        "riotStatus": "BALANCED",
        "winRate": "50.8%",
        "presenceRate": "16.5%",
        "radar": {"zone": 88, "lethality": 85, "cc": 60, "mobility": 45, "surv": 55, "endg": 78},
        "phases": {"opening": 80, "midgame": 88, "endgame": 75},
        "heatmapHotspots": [[5, 2], [5, 5], [6, 3]],
        "powerTiles": ["c3 (+5.1%)", "f3 (+4.8%)", "d2 (+4.4%)"],
        "vulnerableTiles": ["d6 (-7.0%)", "e6 (-6.6%)", "f5 (-6.1%)"],
        "topSynergies": [{"hero": "Warden", "delta": "+5.6%"}, {"hero": "Geomancer", "delta": "+4.9%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-7.8%"}, {"hero": "Shadowblade", "delta": "-6.9%"}],
    },
    "Phantom": {
        "classes": ["Infiltrator (Espectro Furtivo)", "Desestabilizador Barato"],
        "cost": 5,
        "efficiency": "1.12x (Forte para o Custo)",
        "cir": 1.12,
        "riotStatus": "STRONG_FOR_COST",
        "winRate": "51.0%",
        "presenceRate": "22.5%",
        "radar": {"zone": 35, "lethality": 65, "cc": 40, "mobility": 85, "surv": 30, "endg": 60},
        "phases": {"opening": 85, "midgame": 65, "endgame": 40},
        "heatmapHotspots": [[1, 3], [2, 4]],
        "powerTiles": ["d7 (+4.5%)", "e6 (+4.2%)", "c6 (+3.9%)"],
        "vulnerableTiles": ["d4 (-6.0%)", "e4 (-5.8%)", "d5 (-5.5%)"],
        "topSynergies": [{"hero": "Shadowblade", "delta": "+5.2%"}, {"hero": "Valkyrie", "delta": "+4.6%"}],
        "topCounters": [{"hero": "Sentry", "delta": "-6.5%"}, {"hero": "Stormcaller", "delta": "-5.8%"}],
    },
    "Cleric": {
        "classes": ["Support (Clérigo Protetor)", "Curandeiro e Âncora"],
        "cost": 14,
        "efficiency": "1.02x (Equilibrado)",
        "cir": 1.02,
        "riotStatus": "BALANCED",
        "winRate": "50.4%",
        "presenceRate": "15.0%",
        "radar": {"zone": 75, "lethality": 40, "cc": 70, "mobility": 50, "surv": 85, "endg": 82},
        "phases": {"opening": 72, "midgame": 85, "endgame": 88},
        "heatmapHotspots": [[4, 2], [4, 5], [5, 3]],
        "powerTiles": ["c4 (+4.8%)", "f4 (+4.5%)", "d3 (+4.1%)"],
        "vulnerableTiles": ["a1 (-6.3%)", "h8 (-6.0%)", "d7 (-5.6%)"],
        "topSynergies": [{"hero": "Berserker", "delta": "+6.1%"}, {"hero": "Templar", "delta": "+5.3%"}],
        "topCounters": [{"hero": "Nightshade", "delta": "-6.7%"}, {"hero": "Shadowblade", "delta": "-6.1%"}],
    },
    "Templar": {
        "classes": ["Vanguard (Cavaleiro Sagrado)", "Baluarte Ofensivo"],
        "cost": 15,
        "efficiency": "1.04x (Equilibrado)",
        "cir": 1.04,
        "riotStatus": "BALANCED",
        "winRate": "51.1%",
        "presenceRate": "16.8%",
        "radar": {"zone": 80, "lethality": 75, "cc": 65, "mobility": 60, "surv": 85, "endg": 80},
        "phases": {"opening": 75, "midgame": 88, "endgame": 82},
        "heatmapHotspots": [[3, 3], [4, 4], [3, 4]],
        "powerTiles": ["d5 (+5.0%)", "e4 (+4.7%)", "d4 (+4.5%)"],
        "vulnerableTiles": ["a2 (-6.4%)", "h7 (-6.0%)", "b8 (-5.6%)"],
        "topSynergies": [{"hero": "Cleric", "delta": "+5.4%"}, {"hero": "Arcanist", "delta": "+4.8%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-6.5%"}, {"hero": "Illusionist", "delta": "-5.8%"}],
    },
    "Inquisitor": {
        "classes": ["Disruptor (Silenciador Místico)", "Executor Anti-Magos"],
        "cost": 15,
        "efficiency": "1.07x (Equilibrado)",
        "cir": 1.07,
        "riotStatus": "BALANCED",
        "winRate": "52.1%",
        "presenceRate": "19.8%",
        "radar": {"zone": 82, "lethality": 80, "cc": 88, "mobility": 55, "surv": 78, "endg": 86},
        "phases": {"opening": 76, "midgame": 90, "endgame": 86},
        "heatmapHotspots": [[3, 2], [4, 5], [3, 4]],
        "powerTiles": ["c5 (+5.6%)", "f4 (+5.3%)", "e5 (+4.9%)"],
        "vulnerableTiles": ["a1 (-6.8%)", "h8 (-6.4%)", "b1 (-5.9%)"],
        "topSynergies": [{"hero": "Paladin", "delta": "+5.7%"}, {"hero": "Valkyrie", "delta": "+5.1%"}],
        "topCounters": [{"hero": "Marksman", "delta": "-6.4%"}, {"hero": "Warden", "delta": "-5.7%"}],
    },
    "Geomancer": {
        "classes": ["Controller (Manipulador Telúrico)", "Criador de Barreiras"],
        "cost": 14,
        "efficiency": "1.00x (Equilibrado)",
        "cir": 1.00,
        "riotStatus": "BALANCED",
        "winRate": "50.0%",
        "presenceRate": "14.2%",
        "radar": {"zone": 90, "lethality": 55, "cc": 85, "mobility": 40, "surv": 80, "endg": 78},
        "phases": {"opening": 82, "midgame": 86, "endgame": 74},
        "heatmapHotspots": [[4, 3], [4, 4], [5, 3]],
        "powerTiles": ["d4 (+4.9%)", "e4 (+4.6%)", "d3 (+4.2%)"],
        "vulnerableTiles": ["a7 (-6.5%)", "h2 (-6.1%)", "d8 (-5.7%)"],
        "topSynergies": [{"hero": "Marksman", "delta": "+5.8%"}, {"hero": "Ranger", "delta": "+5.0%"}],
        "topCounters": [{"hero": "Shadowblade", "delta": "-7.0%"}, {"hero": "Dragoon", "delta": "-6.3%"}],
    },
    "Lich": {
        "classes": ["Summoner (Necromante Supremo)", "Mestre da Morte"],
        "cost": 15,
        "efficiency": "1.05x (Equilibrado)",
        "cir": 1.05,
        "riotStatus": "BALANCED",
        "winRate": "51.4%",
        "presenceRate": "17.0%",
        "radar": {"zone": 92, "lethality": 70, "cc": 75, "mobility": 45, "surv": 75, "endg": 90},
        "phases": {"opening": 68, "midgame": 86, "endgame": 94},
        "heatmapHotspots": [[6, 3], [6, 4], [5, 2]],
        "powerTiles": ["d2 (+5.2%)", "e2 (+4.9%)", "c3 (+4.5%)"],
        "vulnerableTiles": ["d6 (-7.1%)", "e6 (-6.7%)", "f5 (-6.2%)"],
        "topSynergies": [{"hero": "BoneLord", "delta": "+6.3%"}, {"hero": "FrostMage", "delta": "+5.1%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-7.9%"}, {"hero": "Pyromancer", "delta": "-6.8%"}],
    },
    "Nightshade": {
        "classes": ["Striker (Veneno e Sombras)", "Emboscador Mortal"],
        "cost": 14,
        "efficiency": "1.03x (Equilibrado)",
        "cir": 1.03,
        "riotStatus": "BALANCED",
        "winRate": "50.9%",
        "presenceRate": "16.4%",
        "radar": {"zone": 50, "lethality": 90, "cc": 65, "mobility": 88, "surv": 55, "endg": 85},
        "phases": {"opening": 74, "midgame": 88, "endgame": 86},
        "heatmapHotspots": [[2, 2], [2, 5], [4, 3]],
        "powerTiles": ["c6 (+5.3%)", "f6 (+5.0%)", "d4 (+4.6%)"],
        "vulnerableTiles": ["d2 (-6.8%)", "e2 (-6.4%)", "a1 (-6.0%)"],
        "topSynergies": [{"hero": "Shadowblade", "delta": "+5.7%"}, {"hero": "Cleric", "delta": "+4.9%"}],
        "topCounters": [{"hero": "Paladin", "delta": "-7.1%"}, {"hero": "Warden", "delta": "-6.4%"}],
    },
    "Obelisk": {
        "classes": ["Bastion (Totem Estático)", "Sentinela de Bloqueio"],
        "cost": 12,
        "efficiency": "0.98x (Equilibrado)",
        "cir": 0.98,
        "riotStatus": "BALANCED",
        "winRate": "49.5%",
        "presenceRate": "13.5%",
        "radar": {"zone": 85, "lethality": 30, "cc": 70, "mobility": 10, "surv": 95, "endg": 60},
        "phases": {"opening": 85, "midgame": 75, "endgame": 50},
        "heatmapHotspots": [[4, 3], [4, 4], [3, 3]],
        "powerTiles": ["d4 (+4.5%)", "e4 (+4.2%)", "d5 (+3.9%)"],
        "vulnerableTiles": ["a8 (-5.8%)", "h1 (-5.5%)", "h8 (-5.2%)"],
        "topSynergies": [{"hero": "Marksman", "delta": "+5.5%"}, {"hero": "Stormcaller", "delta": "+4.8%"}],
        "topCounters": [{"hero": "Duelist", "delta": "-6.2%"}, {"hero": "Valkyrie", "delta": "-5.6%"}],
    },
    "Sentry": {
        "classes": ["Bastion (Torre de Vigia)", "Supressor Estático"],
        "cost": 10,
        "efficiency": "0.96x (Equilibrado)",
        "cir": 0.96,
        "riotStatus": "BALANCED",
        "winRate": "48.9%",
        "presenceRate": "12.8%",
        "radar": {"zone": 80, "lethality": 60, "cc": 50, "mobility": 10, "surv": 90, "endg": 55},
        "phases": {"opening": 82, "midgame": 72, "endgame": 48},
        "heatmapHotspots": [[5, 2], [5, 5], [4, 3]],
        "powerTiles": ["c3 (+4.4%)", "f3 (+4.1%)", "d4 (+3.8%)"],
        "vulnerableTiles": ["d7 (-6.0%)", "e7 (-5.7%)", "a1 (-5.3%)"],
        "topSynergies": [{"hero": "Warden", "delta": "+5.0%"}, {"hero": "Paladin", "delta": "+4.4%"}],
        "topCounters": [{"hero": "Shadowblade", "delta": "-6.5%"}, {"hero": "Phantom", "delta": "-5.8%"}],
    },
    "Stonewall": {
        "classes": ["Bastion (Muralha Viva)", "Barricada Tática"],
        "cost": 12,
        "efficiency": "0.97x (Equilibrado)",
        "cir": 0.97,
        "riotStatus": "BALANCED",
        "winRate": "49.2%",
        "presenceRate": "13.0%",
        "radar": {"zone": 90, "lethality": 20, "cc": 75, "mobility": 10, "surv": 98, "endg": 50},
        "phases": {"opening": 88, "midgame": 70, "endgame": 45},
        "heatmapHotspots": [[4, 3], [4, 4], [3, 4]],
        "powerTiles": ["d4 (+4.6%)", "e4 (+4.3%)", "e5 (+4.0%)"],
        "vulnerableTiles": ["a1 (-5.9%)", "h8 (-5.6%)", "h1 (-5.3%)"],
        "topSynergies": [{"hero": "Arcanist", "delta": "+5.4%"}, {"hero": "Stormcaller", "delta": "+4.7%"}],
        "topCounters": [{"hero": "Illusionist", "delta": "-6.4%"}, {"hero": "Duelist", "delta": "-5.7%"}],
    },
    "Trickster": {
        "classes": ["Disruptor (Trapaceiro Arcano)", "Ilusionista de Confusão"],
        "cost": 14,
        "efficiency": "1.01x (Equilibrado)",
        "cir": 1.01,
        "riotStatus": "BALANCED",
        "winRate": "50.6%",
        "presenceRate": "15.5%",
        "radar": {"zone": 75, "lethality": 65, "cc": 85, "mobility": 80, "surv": 60, "endg": 80},
        "phases": {"opening": 78, "midgame": 85, "endgame": 82},
        "heatmapHotspots": [[3, 2], [4, 5], [2, 4]],
        "powerTiles": ["c5 (+5.0%)", "f4 (+4.7%)", "e6 (+4.3%)"],
        "vulnerableTiles": ["d3 (-6.5%)", "e3 (-6.1%)", "a1 (-5.7%)"],
        "topSynergies": [{"hero": "Valkyrie", "delta": "+5.6%"}, {"hero": "FrostMage", "delta": "+4.9%"}],
        "topCounters": [{"hero": "Inquisitor", "delta": "-7.0%"}, {"hero": "Paladin", "delta": "-6.2%"}],
    },
    "Ghoul": {
        "classes": ["Minion (Carniçal Voraz)", "Enxame Rápido"],
        "cost": 10,
        "efficiency": "0.98x (Equilibrado)",
        "cir": 0.98,
        "riotStatus": "BALANCED",
        "winRate": "49.5%",
        "presenceRate": "14.0%",
        "radar": {"zone": 45, "lethality": 60, "cc": 30, "mobility": 70, "surv": 45, "endg": 40},
        "phases": {"opening": 75, "midgame": 60, "endgame": 35},
        "heatmapHotspots": [[3, 3], [4, 4], [2, 3]],
        "powerTiles": ["d5 (+3.8%)", "e4 (+3.5%)", "c6 (+3.2%)"],
        "vulnerableTiles": ["a1 (-5.5%)", "h8 (-5.2%)", "h1 (-5.0%)"],
        "topSynergies": [{"hero": "Lich", "delta": "+4.8%"}, {"hero": "BoneLord", "delta": "+4.2%"}],
        "topCounters": [{"hero": "Pyromancer", "delta": "-6.7%"}, {"hero": "Stormcaller", "delta": "-6.0%"}],
    },
}

with open(APP_JS, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Replace HERO_ANALYTICS_DATA
pattern = r"// Empirical Hero Analytics \(Football-style stats\)\nconst HERO_ANALYTICS_DATA = \{[\s\S]*?\n\};"
new_data_str = "// Empirical Hero Analytics (Football-style stats & Riot Game Balance Framework)\nconst HERO_ANALYTICS_DATA = " + json.dumps(HERO_EXTRAS, indent=2, ensure_ascii=False) + ";"
code = re.sub(pattern, new_data_str, code, count=1)

# 2. Add heatmap mode state and update renderSquareHeatmap / updateHeroAnalyticsDisplay
old_render_block = """function renderSquareHeatmap(hotspots) {
  const chartCanvas = document.getElementById("heatmapCanvas");
  if (!chartCanvas) return;
  const cctx = chartCanvas.getContext("2d");
  const size = chartCanvas.width;
  const squareSize = size / 8;

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const isLight = (r + c) % 2 === 0;
      cctx.fillStyle = isLight ? "#21262d" : "#161b22";
      cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
    }
  }

  // Draw hotspot glows
  hotspots.forEach(([r, c]) => {
    cctx.fillStyle = "rgba(239, 68, 68, 0.65)";
    cctx.fillRect(c * squareSize, r * squareSize, squareSize, squareSize);
    cctx.strokeStyle = "#f87171";
    cctx.lineWidth = 1.5;
    cctx.strokeRect(c * squareSize, r * squareSize, squareSize, squareSize);
  });
}

function updateHeroAnalyticsDisplay(heroName) {
  const data = HERO_ANALYTICS_DATA[heroName] || HERO_ANALYTICS_DATA["Paladin"];
  document.getElementById("analyticsDerivedClasses").textContent = data.classes.join(" • ");
  document.getElementById("analyticsCostEfficiency").textContent = data.efficiency;
  document.getElementById("openingRating").textContent = data.phases.opening;
  document.getElementById("midgameRating").textContent = data.phases.midgame;
  document.getElementById("endgameRating").textContent = data.phases.endgame;

  renderRadarChart(data.radar);
  renderSquareHeatmap(data.heatmapHotspots);
}"""

new_render_block = """let currentHeatmapMode = "density"; // "density" or "delta_wr"

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
}"""

assert old_render_block in code, "old_render_block not found in app.js!"
code = code.replace(old_render_block, new_render_block, 1)

# 3. Add listeners for btnHeatmapDensity and btnHeatmapDeltaWR
old_listener = """document.getElementById("analyticsHeroSelect").addEventListener("change", (e) => {
  updateHeroAnalyticsDisplay(e.target.value);
});"""

new_listener = """document.getElementById("analyticsHeroSelect").addEventListener("change", (e) => {
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
}"""

assert old_listener in code, "old_listener not found in app.js!"
code = code.replace(old_listener, new_listener, 1)

with open(APP_JS, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully updated deploy/web/app.js!")
