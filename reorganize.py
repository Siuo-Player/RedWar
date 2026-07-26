import os
from pathlib import Path

def create_structure():
    structure = {
        "engine": {
            "__init__.py": "",
            "game_state.py": "# Gere o estado do tabuleiro, regras, relogio, stun timer e 50-move rule",
            "move_generator.py": "# Gerador otimizado de movimentos",
            "pieces.py": "# Definicao das classes, custos, get_valid_moves, attacks e stuns",
        },
        "ui": {
            "__init__.py": "",
            "window.py": "# Gestao da janela Pygame, resolucao e grid",
            "renderer.py": "# Desenho visual, overlays AoE (Alpha), loja de draft e relogios",
            "assets": {}
        },
        "ai": {
            "__init__.py": "",
            "evaluator.py": "# Perfis de IA (Gulosa, Estrategica, Agressiva, Defensiva)",
            "search.py": "# Algoritmo Minimax com Poda Alfa-Beta e Move Ordering",
            "trainer.py": "# Simulador rapido (1000 partidas aleatorias)",
            "exhaustive_trainer.py": "# Simulador exaustivo de estruturas (Minimax + Monte Carlo)",
            "opening_tester.py": "# Arena modular para testar perfis de IA em aberturas",
            "auto_balancer.py": "# Script de analise de Win-Rate para ajuste automatico de custos"
        },
        "tests": {
            "__init__.py": "",
            "test_moves.py": "# Testes unitarios de movimentos base",
            "test_rules.py": "# Testes de game over, stun hit-kill e passivas",
        }
    }

    base_dir = Path.cwd()
    print(f"A verificar/atualizar estrutura em: {base_dir}\n")

    for folder, contents in structure.items():
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)

        if isinstance(contents, dict):
            for file_name, file_content in contents.items():
                if file_name == "assets":
                    (folder_path / file_name).mkdir(exist_ok=True)
                else:
                    file_path = folder_path / file_name
                    if not file_path.exists():
                        file_path.write_text(file_content, encoding='utf-8')

    print("Estrutura de pastas e ficheiros atualizada com sucesso!")

if __name__ == '__main__':
    create_structure()