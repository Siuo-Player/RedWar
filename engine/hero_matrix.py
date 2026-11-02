# engine/hero_matrix.py
"""
Hero Tactical Matrix, Archetypes, and Emergent Mechanics Synergies for RedWar.
Implements non-arithmetic game design synergies (Displacement + Hazards, Silence + Stun,
Lightning Conduits) and comprehensive team composition balance analysis.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any
from engine.game_state import GameState


class HeroArchetype(str, Enum):
    VANGUARD = "vanguard"       # Frontline tank, lane controller, displacement (Paladin, Golem)
    STRIKER = "striker"         # High mobility, execution, phantom phasing (Shadowblade, Dragoon)
    ARTILLERY = "artillery"     # Long-range line attacks, chain lightning (Stormcaller, Archer, Pyromancer)
    DISRUPTOR = "disruptor"     # Crowd control, freeze, area silence (FrostMage, Banshee)
    SUMMONER = "summoner"       # Minion summoning, board saturation (BoneLord)


class MechanicSynergy(str, Enum):
    LOCKDOWN_EXECUTION = "lockdown_execution"       # Disruptor freeze + Striker flank lethal hit
    DISPLACEMENT_HAZARD = "displacement_hazard"     # Vanguard shield push into lethal lava or barrier
    LIGHTNING_CONDUIT = "lightning_conduit"         # Chain lightning bridging across allied/enemy units
    HOOK_AND_EXECUTE = "hook_and_execute"           # Pulling high-value target into lethal melee range
    PROTECTION_CLEANSE = "protection_cleanse"       # Cleansing stunned ally within vulnerable window


@dataclass
class DetectedSynergy:
    synergy_type: MechanicSynergy
    description: str
    initiator_pos: Tuple[int, int]
    partner_pos: Optional[Tuple[int, int]] = None
    target_pos: Optional[Tuple[int, int]] = None
    value: float = 10.0


@dataclass
class TeamCompositionAnalysis:
    archetype_counts: Dict[HeroArchetype, int]
    is_well_rounded: bool
    missing_archetypes: List[HeroArchetype]
    tactical_vulnerabilities: List[str]
    synergy_potential_score: float  # 0.0 to 100.0


class HeroMatrix:
    """Canonical registry mapping heroes to archetypes, synergies, and balance profiles."""

    HERO_ARCHETYPES: Dict[str, HeroArchetype] = {
        # Vanguards
        "Paladin": HeroArchetype.VANGUARD,
        "Golem": HeroArchetype.VANGUARD,
        "Guardian": HeroArchetype.VANGUARD,
        "Berserker": HeroArchetype.VANGUARD,
        
        # Strikers
        "Shadowblade": HeroArchetype.STRIKER,
        "Dragoon": HeroArchetype.STRIKER,
        "Rogue": HeroArchetype.STRIKER,
        "Assassin": HeroArchetype.STRIKER,
        
        # Artillery
        "Stormcaller": HeroArchetype.ARTILLERY,
        "Archer": HeroArchetype.ARTILLERY,
        "Pyromancer": HeroArchetype.ARTILLERY,
        "Bombard": HeroArchetype.ARTILLERY,
        
        # Disruptors
        "FrostMage": HeroArchetype.DISRUPTOR,
        "Banshee": HeroArchetype.DISRUPTOR,
        "Inquisitor": HeroArchetype.DISRUPTOR,
        "Illusionist": HeroArchetype.DISRUPTOR,
        
        # Summoners / Minions
        "BoneLord": HeroArchetype.SUMMONER,
        "Necromancer": HeroArchetype.SUMMONER,
        "Bone": HeroArchetype.VANGUARD,  # Basic summoned meat-shield
    }

    def get_archetype(self, hero_name: str) -> HeroArchetype:
        """Return the archetype of a given hero name, defaulting to VANGUARD if unknown."""
        return self.HERO_ARCHETYPES.get(hero_name, HeroArchetype.VANGUARD)

    def detect_spatial_synergies(self, state: GameState, team: str) -> List[DetectedSynergy]:
        """
        Detect emergent mechanic synergies between allied units on the board.
        """
        synergies: List[DetectedSynergy] = []
        enemy_team = "pretas" if team == "brancas" else "brancas"

        # Collect pieces
        allies = []
        enemies = []
        for r in range(len(state.board)):
            for c in range(len(state.board[0])):
                p = state.board[r][c]
                if p:
                    if p.team == team:
                        allies.append((r, c, p))
                    else:
                        enemies.append((r, c, p))

        # Check for LOCKDOWN_EXECUTION:
        # A friendly Disruptor and a friendly Striker are within range of an enemy (especially if already stunned)
        strikers = [a for a in allies if self.get_archetype(a[2].__class__.__name__) == HeroArchetype.STRIKER]
        disruptors = [a for a in allies if self.get_archetype(a[2].__class__.__name__) == HeroArchetype.DISRUPTOR]

        for s_r, s_c, striker in strikers:
            for e_r, e_c, enemy in enemies:
                dist_striker = max(abs(s_r - e_r), abs(s_c - e_c))
                if dist_striker <= 3:  # Within striker leap/dash range
                    # Check if enemy is stunned or a disruptor is nearby to stun
                    if getattr(enemy, "stun_timer", 0) > 0:
                        synergies.append(DetectedSynergy(
                            synergy_type=MechanicSynergy.LOCKDOWN_EXECUTION,
                            description=f"Striker {striker.__class__.__name__} alinhado para executar alvo atordoado {enemy.__class__.__name__}.",
                            initiator_pos=(s_r, s_c),
                            target_pos=(e_r, e_c),
                            value=50.0
                        ))
                    else:
                        for d_r, d_c, disruptor in disruptors:
                            dist_disruptor = max(abs(d_r - e_r), abs(d_c - e_c))
                            if dist_disruptor <= 3:
                                synergies.append(DetectedSynergy(
                                    synergy_type=MechanicSynergy.LOCKDOWN_EXECUTION,
                                    description=f"Coordenação de Lockdown: {disruptor.__class__.__name__} e {striker.__class__.__name__} encurralam {enemy.__class__.__name__}.",
                                    initiator_pos=(d_r, d_c),
                                    partner_pos=(s_r, s_c),
                                    target_pos=(e_r, e_c),
                                    value=35.0
                                ))

        return synergies

    def evaluate_push_hazard_threat(self, state: GameState, hazards: Dict[str, List[Tuple[int, int]]], team: str) -> float:
        """
        Evaluate lethal knockback/displacement opportunities into hazards (Lava).
        """
        threat_score = 0.0
        lava_tiles = set(hazards.get("lava", []))
        if not lava_tiles:
            return 0.0

        enemy_team = "pretas" if team == "brancas" else "brancas"

        # Check all allied Vanguards and Strikers adjacent to enemies
        for r in range(len(state.board)):
            for c in range(len(state.board[0])):
                piece = state.board[r][c]
                if piece and piece.team == team and self.get_archetype(piece.__class__.__name__) in (HeroArchetype.VANGUARD, HeroArchetype.STRIKER):
                    # Check 4 orthogonal directions for enemy
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        adj_r, adj_c = r + dr, c + dc
                        if 0 <= adj_r < len(state.board) and 0 <= adj_c < len(state.board[0]):
                            target = state.board[adj_r][adj_c]
                            if target and target.team == enemy_team:
                                # Direction of push is (adj_r + dr, adj_c + dc)
                                push_r, push_c = adj_r + dr, adj_c + dc
                                if (push_r, push_c) in lava_tiles:
                                    # Lethal knockback directly into lava!
                                    threat_score += float(getattr(target, "cost", 50)) * 1.5

        return threat_score

    def analyze_composition(self, hero_names: List[str]) -> TeamCompositionAnalysis:
        """
        Analyze a draft or team composition across the 5 archetypes,
        diagnosing balance, synergies, and tactical vulnerabilities.
        """
        counts: Dict[HeroArchetype, int] = {arch: 0 for arch in HeroArchetype}
        for name in hero_names:
            arch = self.get_archetype(name)
            counts[arch] += 1

        missing = [arch for arch, cnt in counts.items() if cnt == 0]
        vulnerabilities: List[str] = []

        if counts[HeroArchetype.VANGUARD] == 0:
            vulnerabilities.append("Falta presença de linha de frente: Exército vulnerável a investidas diretas.")
        if counts[HeroArchetype.DISRUPTOR] == 0:
            vulnerabilities.append("Sem controlo de grupo: Incapaz de impedir saltos ou feitiços adversários.")
        if counts[HeroArchetype.ARTILLERY] == 0:
            vulnerabilities.append("Sem alcance direto: Dificuldade em pressionar adversários defensivos.")
        if counts[HeroArchetype.STRIKER] == 0:
            vulnerabilities.append("Falta de mobilidade de finalização: Dificuldade em converter stuns em mortes.")

        # Calculate well-roundedness
        covered_archetypes = sum(1 for cnt in counts.values() if cnt > 0)
        is_well_rounded = covered_archetypes >= 4 or (counts[HeroArchetype.VANGUARD] >= 1 and counts[HeroArchetype.STRIKER] >= 1 and counts[HeroArchetype.DISRUPTOR] >= 1 and counts[HeroArchetype.ARTILLERY] >= 1)

        # Calculate synergy potential score
        synergy_score = min(100.0, float(covered_archetypes * 20.0 + (10.0 if not vulnerabilities else 0.0)))

        return TeamCompositionAnalysis(
            archetype_counts=counts,
            is_well_rounded=is_well_rounded,
            missing_archetypes=missing,
            tactical_vulnerabilities=vulnerabilities,
            synergy_potential_score=synergy_score,
        )
