import os
import shutil
from pathlib import Path

MAPA_FICHEIROS = {
    # 1. TOOLS (Ferramentas de Desenvolvimento)
    "reorganize.py": "tools/scripts",
    "gerar_estrutura.py": "tools/scripts",
    "fetch_icons.py": "tools/scripts",
    "build_pipeline.py": "tools/scripts",
    "tmp_game_sim.py": "tools/scripts",
    "tmp_ui_test.py": "tools/scripts",

    "trainer.py": "tools/analytics",
    "game_analyzer.py": "tools/analytics",
    "arena_tournament.py": "tools/analytics",
    "opening_tester.py": "tools/analytics",
    "calibrate_elo.py": "tools/analytics",
    "calibrate_elo_chain.py": "tools/analytics",
    "elo_config.json": "tools/analytics",

    "auto_pricer.py": "tools/balance",
    "color_balancer.py": "tools/balance",

    # 2. ONLINE (Multijogador e Servidor)
    "multiplayer_main.py": "online/client",
    "client.py": "online/network",
    "app.py": "online/server",

    # 3. DEPLOY (Empacotamento)
    "RedWar_Online.spec": "deploy/packaging",
    "main.spec": "deploy/packaging",

    # 4. DOCS (Documentação)
    "Documento_Design_Jogo.md": "docs",
    "Estrutura_Projeto.md": "docs",

    # Ficam na sua pasta atual de raiz (se estiverem soltos, vão para o sítio certo)
    "jogos_encravados_log.txt": "logs",
    "relatorio_build.txt": "logs",
    "relatorio_telemetria.txt": "logs",
    "telemetria_profunda.json": "logs",
    "estatisticas_treino.json": "data"
}

def organizar_projeto():
    base_dir = Path.cwd()
    movidos = 0
    print("🧹 A aplicar a Macro-Estrutura no projeto RedWar...")

    # 1. Criar as pastas de destino (com subpastas)
    for pasta in set(MAPA_FICHEIROS.values()):
        (base_dir / pasta).mkdir(parents=True, exist_ok=True)

    # 2. Procurar ficheiros em todas as pastas conhecidas
    pastas_a_verificar = [
        base_dir, 
        base_dir / "ai", 
        base_dir / "scripts", 
        base_dir / "analytics", 
        base_dir / "balance",
        base_dir / "network",
        base_dir / "server",
        base_dir / "multiplayer",
        base_dir / "packaging"
    ]

    for pasta_origem in pastas_a_verificar:
        if not pasta_origem.exists():
            continue
            
        for ficheiro in pasta_origem.iterdir():
            if ficheiro.is_file() and ficheiro.name in MAPA_FICHEIROS:
                pasta_destino = base_dir / MAPA_FICHEIROS[ficheiro.name]
                caminho_destino = pasta_destino / ficheiro.name

                if ficheiro.absolute() == caminho_destino.absolute():
                    continue

                if caminho_destino.exists():
                    caminho_destino.unlink()
                    
                shutil.move(str(ficheiro), str(caminho_destino))
                print(f"✅ Organizado: {ficheiro.name} -> {pasta_destino}/")
                movidos += 1

    # 3. Limpar pastas antigas que ficaram vazias
    pastas_para_limpar = ["scripts", "analytics", "balance", "network", "server", "multiplayer", "packaging"]
    for pasta_vazia in pastas_para_limpar:
        p = base_dir / pasta_vazia
        if p.exists() and not any(p.iterdir()):
            p.rmdir()
            print(f"🗑️ Pasta limpa: {pasta_vazia}/")

    if movidos == 0:
        print("✨ A estrutura já está perfeita!")

if __name__ == "__main__":
    organizar_projeto()