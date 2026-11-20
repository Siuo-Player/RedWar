# engine/hero_academy.py
"""
Hero Academy (Academia de Heróis) for RedWar.
Provides interactive tutorial lessons, deep hero lore, ability breakdowns,
and tactical puzzle scenarios designed to teach new and advanced mechanics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass
class AcademyLesson:
    hero_id: str
    hero_name: str
    title: str
    lore: str
    ability_description: str
    puzzle_objective: str
    initial_board: Dict[str, List[Dict[str, Any]]]
    solution_moves: List[Dict[str, Any]]
    post_solve_explanation: str


class HeroAcademy:
    """Manages the curriculum of hero tutorials, lore, and interactive puzzles."""

    def __init__(self):
        self._lessons: Dict[str, AcademyLesson] = {}
        self._build_curriculum()

    def _build_curriculum(self):
        # 1. Paladin
        self._lessons["paladin"] = AcademyLesson(
            hero_id="paladin",
            hero_name="Paladin",
            title="O Bastião da Linha de Frente",
            lore="Treinado nos mosteiros de ferro das montanhas do norte, o Paladino é um guerreiro sagrado inabalável. Serve como âncora defensiva da equipa, quebrando avanços inimigos com o seu escudo de corpo inteiro.",
            ability_description="Avanço Ortogonal: Move-se até 2 casas em linha reta (horizontal ou vertical). Aplica um stun poderoso a qualquer inimigo que colida no seu caminho.",
            puzzle_objective="Avança 2 casas para cima para aplicar o segundo stun no Dragoon inimigo enfraquecido e eliminá-lo.",
            initial_board={
                "white": [{"name": "Paladin", "pos": (4, 3), "stun": 0}],
                "black": [{"name": "Dragoon", "pos": (2, 3), "stun": 1}],
            },
            solution_moves=[{"from": (4, 3), "to": (2, 3)}],
            post_solve_explanation="Correto! O avanço de 2 casas ortogonais do Paladino permitiu colidir com a unidade atordoada e garantir uma eliminação imediata."
        )

        # 2. Shadowblade
        self._lessons["shadowblade"] = AcademyLesson(
            hero_id="shadowblade",
            hero_name="Shadowblade",
            title="A Lâmina Fantasma",
            lore="Criada nas sombras das criptas ancestrais, a Shadowblade maneja adagas de éter e transita entre dimensões. Nenhuma muralha defensiva ou formação compacta consegue bloquear a sua passagem.",
            ability_description="Mobilidade Fantasma: Move-se até 3 casas em diagonal atravessando peças aliadas e inimigas sem ser bloqueada. Golpeia e atordoa o alvo na casa final.",
            puzzle_objective="Usa a mobilidade fantasma da Shadowblade para atravessar o soldado aliado e abater o FrostMage inimigo na casa (1, 1).",
            initial_board={
                "white": [
                    {"name": "Shadowblade", "pos": (3, 3), "stun": 0},
                    {"name": "Bone", "pos": (2, 2), "stun": 0},  # Ally in between
                ],
                "black": [{"name": "FrostMage", "pos": (1, 1), "stun": 1}],
            },
            solution_moves=[{"from": (3, 3), "to": (1, 1)}],
            post_solve_explanation="Excelente! A Shadowblade atravessou o soldado sem colidir, demonstrando a capacidade única de ignorar bloqueios e alcançar alvos protegidos."
        )

        # 3. Stormcaller
        self._lessons["stormcaller"] = AcademyLesson(
            hero_id="stormcaller",
            hero_name="Stormcaller",
            title="O Mestre dos Relâmpagos",
            lore="Capaz de canalizar as correntes elétricas da estratosfera, o Stormcaller domina o combate à distância sem precisar de se aproximar dos perigos do combate corpo a corpo.",
            ability_description="Chain Lightning: Feitiço de raio direto que dispara ao longo de uma coluna ou linha direta até 4 casas de alcance, atordoando à distância.",
            puzzle_objective="Dispara o teu raio elétrico ao longo da coluna para atordoar o herói inimigo desprotegido.",
            initial_board={
                "white": [{"name": "Stormcaller", "pos": (5, 2), "stun": 0}],
                "black": [{"name": "BoneLord", "pos": (2, 2), "stun": 0}],
            },
            solution_moves=[{"from": (5, 2), "to": (2, 2)}],
            post_solve_explanation="Vitória! O raio do Stormcaller atingiu o alvo com precisão cirúrgica sem expor a sua posição defensiva."
        )

        # 4. Dragoon
        self._lessons["dragoon"] = AcademyLesson(
            hero_id="dragoon",
            hero_name="Dragoon",
            title="O Salto do Dragão",
            lore="Armado com uma lança pesada forjada em escamas de dragão, o Dragoon combina velocidade e poder aéreo fulminante.",
            ability_description="Salto Tático em L: Move-se de forma semelhante ao cavalo do xadrez, mas com alcance estendido para surpreender formações inimigas.",
            puzzle_objective="Salta sobre a barreira e neutraliza a retaguarda inimiga.",
            initial_board={
                "white": [{"name": "Dragoon", "pos": (4, 4), "stun": 0}],
                "black": [{"name": "Paladin", "pos": (2, 5), "stun": 1}],
            },
            solution_moves=[{"from": (4, 4), "to": (2, 5)}],
            post_solve_explanation="Excelente! O salto do Dragoon contornou as linhas defensivas com maestria."
        )

        # 5. FrostMage
        self._lessons["frostmage"] = AcademyLesson(
            hero_id="frostmage",
            hero_name="FrostMage",
            title="O Domínio do Gelo",
            lore="Especialista em magia glacial arcaica, o FrostMage controla o tempo e o ritmo da partida reduzindo a temperatura ao redor dos oponentes.",
            ability_description="Congelamento Remoto: Aplica stun à distância em alvos dentro de 3 casas ortogonais, paralisando unidades chave durante 2 turnos.",
            puzzle_objective="Congela o atacante inimigo antes que ele consiga romper as tuas defesas.",
            initial_board={
                "white": [{"name": "FrostMage", "pos": (4, 1), "stun": 0}],
                "black": [{"name": "Dragoon", "pos": (4, 3), "stun": 0}],
            },
            solution_moves=[{"from": (4, 1), "to": (4, 3)}],
            post_solve_explanation="Perfeito! O atordoamento de gelo paralisou a ameaça antes do seu próximo turno."
        )

        # 6. BoneLord
        self._lessons["bonelord"] = AcademyLesson(
            hero_id="bonelord",
            hero_name="BoneLord",
            title="O Soberano das Criptas",
            lore="Necromante lendário que ergue soldados esqueléticos das profundezas para criar superioridade numérica no tabuleiro.",
            ability_description="Invocação de Minions: Invoca soldados 'Bone' em casas adjacentes livres, criando obstáculos e peões de sacrifício.",
            puzzle_objective="Move o BoneLord para a casa (3, 3) para consolidar o controle da área central.",
            initial_board={
                "white": [{"name": "BoneLord", "pos": (4, 3), "stun": 0}],
                "black": [{"name": "FrostMage", "pos": (1, 3), "stun": 0}],
            },
            solution_moves=[{"from": (4, 3), "to": (3, 3)}],
            post_solve_explanation="Muito bem! O avanço do BoneLord estabelece a presença central necessária para invocar tropas nos turnos seguintes."
        )

    def list_lessons(self) -> List[AcademyLesson]:
        """Return all available lessons."""
        return list(self._lessons.values())

    def get_lesson(self, hero_id: str) -> Optional[AcademyLesson]:
        """Fetch a specific lesson by hero identifier."""
        return self._lessons.get(hero_id)

    def verify_solution(self, hero_id: str, move: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Verify if the player's attempted move matches the lesson solution.
        Returns: (is_correct, feedback_message)
        """
        lesson = self.get_lesson(hero_id)
        if not lesson:
            return False, "Lição não encontrada."

        from_pos = tuple(move.get("from", ()))
        to_pos = tuple(move.get("to", ()))

        for sol in lesson.solution_moves:
            sol_from = tuple(sol.get("from", ()))
            sol_to = tuple(sol.get("to", ()))
            if from_pos == sol_from and to_pos == sol_to:
                return True, lesson.post_solve_explanation

        return False, "Lance incorreto. Tenta novamente observando as capacidades únicas do herói."
