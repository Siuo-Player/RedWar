import os
import shutil
from pathlib import Path

def create_structure():
    # Definir a estrutura de pastas e ficheiros iniciais
    structure = {
        "engine": {
            "__init__.py": "",
            "game_state.py": "# Gere o estado do tabuleiro, regras e mecânicas temporárias (ex: timers de gelo/imobilização)",
            "move_generator.py": "# Dada uma posição, devolve todos os movimentos válidos para as peças",
            "pieces.py": "# Definição das classes das peças, custos de exército e as suas regras de movimento únicas",
        },
        "ui": {
            "__init__.py": "",
            "window.py": "# Gestão da janela Pygame, eventos de input do rato e renderização base",
            "renderer.py": "# Lógica de desenho: traduz o game_state.py em imagens (tabuleiro, peças, seleções)",
            "assets": {
                # Pasta vazia para futuras imagens/sprites
            }
        },
        "ai": {
            "__init__.py": "",
            "evaluator.py": "# Avaliação estática de uma posição (material, controlo de casas, timers ativos)",
            "search.py": "# O algoritmo principal (Minimax / Alpha-Beta Pruning) para percorrer a árvore de jogadas",
        },
        "tests": {
            "__init__.py": "",
            "test_moves.py": "# Validação das regras: o Move Generator dá os movimentos corretos numa posição X?",
            "test_rules.py": "# Validação de mecânicas de tabuleiro: os turnos e temporizadores estão a funcionar?",
        }
    }

    base_dir = Path.cwd()
    print(f"A organizar o projeto em: {base_dir}\n")

    for folder, contents in structure.items():
        folder_path = base_dir / folder
        folder_path.mkdir(exist_ok=True)
        print(f"Criado/Verificado diretório: {folder_path}")

        if isinstance(contents, dict):
            for file_name, file_content in contents.items():
                if file_name == "assets":
                    (folder_path / file_name).mkdir(exist_ok=True)
                    print(f"  Criado sub-diretório: {folder_path / file_name}")
                else:
                    file_path = folder_path / file_name
                    if not file_path.exists():
                        file_path.write_text(file_content, encoding='utf-8')
                        print(f"  Criado ficheiro: {file_path}")

    # Mover o código solto do main para a UI, se ele ainda não foi movido
    # (assumindo que o utilizador criou o main.py na raiz no passo anterior)
    if (base_dir / "main.py").exists():
        print("\nAviso: O ficheiro main.py na raiz será o ponto de entrada. Ele deve chamar a lógica em /ui e /engine.")

    print("\nReorganização concluída com sucesso!")

if __name__ == '__main__':
    create_structure()
