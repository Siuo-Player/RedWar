import os
import shutil
from pathlib import Path

MAPA_FICHEIROS = {
    # Scripts / Ferramentas auxiliares
    "reorganize.py": "scripts",
    "gerar_estrutura.py": "scripts",
    "fetch_icons.py": "scripts",
    "build_pipeline.py": "scripts",
    "tmp_game_sim.py": "scripts",
    "tmp_ui_test.py": "scripts",

    # Multiplayer
    "multiplayer_main.py": "multiplayer",

    # Packaging e Builds
    "RedWar_Online.spec": "packaging",
    "main.spec": "packaging",

    # Logs (Se existirem atualmente na raiz)
    "jogos_encravados_log.txt": "logs",
    "relatorio_build.txt": "logs",
    "relatorio_telemetria.txt": "logs",
    "telemetria_profunda.json": "logs",

    # Dados
    "estatisticas_treino.json": "data"
}

def organizar_projeto():
    base_dir = Path.cwd()
    movidos = 0
    print("🧹 A organizar o projeto RedWar...")

    # Criar pastas se não existirem
    for pasta in set(MAPA_FICHEIROS.values()):
        (base_dir / pasta).mkdir(exist_ok=True)

    # Mover ficheiros da raiz
    for ficheiro in base_dir.iterdir():
        if ficheiro.is_file() and ficheiro.name in MAPA_FICHEIROS:
            pasta_destino = base_dir / MAPA_FICHEIROS[ficheiro.name]
            caminho_destino = pasta_destino / ficheiro.name

            if caminho_destino.exists():
                caminho_destino.unlink() # Apaga o antigo no destino se existir
                
            shutil.move(str(ficheiro), str(caminho_destino))
            print(f"✅ Movido: {ficheiro.name} -> {pasta_destino.name}/")
            movidos += 1

    # Limpar o lixo das pastas antigas (se o estatisticas_treino ficou esquecido no ai/)
    ai_stats = base_dir / "ai" / "estatisticas_treino.json"
    if ai_stats.exists():
        (base_dir / "data").mkdir(exist_ok=True)
        caminho_dados = base_dir / "data" / "estatisticas_treino.json"
        if caminho_dados.exists():
            caminho_dados.unlink()
        shutil.move(str(ai_stats), str(caminho_dados))
        print("✅ Movido: ai/estatisticas_treino.json -> data/")

    if movidos == 0:
        print("✨ Tudo perfeitamente organizado!")

if __name__ == "__main__":
    organizar_projeto()