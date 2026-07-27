# reorganize.py
import os
import shutil
from pathlib import Path

# Mapa de Arrumação Automática
MAPA_FICHEIROS = {
    "game_state.py": "engine",
    "pieces.py": "engine",
    "mobs_config.json": "engine",
    "renderer.py": "ui",
    "evaluator.py": "ai",
    "search.py": "ai",
    "trainer.py": "ai",
    "arena_tournament.py": "ai",
    "color_balancer.py": "ai",
    "game_analyzer.py": "ai",
    "opening_tester.py": "ai",
    "client.py": "network",
    "app.py": "server",
    "test_moves.py": "tests",
    "test_rules.py": "tests"
}

def organizar_projeto():
    base_dir = Path.cwd()
    movidos = 0
    
    print("🧹 A verificar ficheiros soltos na raiz do projeto...")
    
    for ficheiro in base_dir.iterdir():
        if ficheiro.is_file() and ficheiro.name in MAPA_FICHEIROS:
            pasta_destino = base_dir / MAPA_FICHEIROS[ficheiro.name]
            pasta_destino.mkdir(exist_ok=True)
            
            caminho_destino = pasta_destino / ficheiro.name
            
            if caminho_destino.exists():
                print(f"⚠️ {ficheiro.name} já existe em {pasta_destino.name}/. A substituir pela versão da raiz...")
                caminho_destino.unlink()
                
            shutil.move(str(ficheiro), str(caminho_destino))
            print(f"✅ Movido: {ficheiro.name} -> {pasta_destino.name}/")
            movidos += 1
            
    if movidos == 0:
        print("✨ Tudo perfeitamente organizado!")

if __name__ == "__main__":
    organizar_projeto()