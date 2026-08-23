import os
import shutil
from pathlib import Path

MAPA_FICHEIROS = {
    # 1. AI (Cérebros e Ferramentas ativas de jogo)
    "bot.py": "ai",
    "search.py": "ai",
    "book_generator.py": "ai",

    # 2. TOOLS (Ferramentas de Desenvolvimento e Teste)
    "reorganize.py": "tools/scripts",
    "gerar_estrutura.py": "tools/scripts",
    "fetch_icons.py": "tools/scripts",
    "build_pipeline.py": "tools/scripts",
    "build_cpp_engine.py": "tools/scripts",

    "trainer.py": "tools/analytics",
    "game_analyzer.py": "tools/analytics",
    "arena_tournament.py": "tools/analytics",
    "opening_tester.py": "tools/analytics",
    "calibrate_elo_chain.py": "tools/analytics",
    "elo_config.json": "tools/analytics",

    "auto_pricer.py": "tools/balance",
    "color_balancer.py": "tools/balance",

    # 3. ONLINE (Multijogador e Servidor)
    "multiplayer_main.py": "online/client",
    "client.py": "online/network",
    "app.py": "online/server",

    # 4. DEPLOY (Empacotamento)
    "RedWar_Online.spec": "deploy/packaging",
    "main.spec": "deploy/packaging",

    # 5. DOCS (Documentação)
    "Documento_Design_Jogo.md": "docs",
    "Estrutura_Projeto.md": "docs",
    "COPILOT_BACKLOG.md": "docs",

    # Ficam na sua pasta atual de raiz (se estiverem soltos, vão para o sítio certo)
    "jogos_encravados_log.txt": "logs",
    "relatorio_build.txt": "logs",
    "relatorio_telemetria.txt": "logs",
    "telemetria_profunda.json": "logs",
    "estatisticas_treino.json": "data",
    "opening_book.json": "data"
}


def organizar_projeto():
    base_dir = Path.cwd()
    movidos = 0
    print("🧹 A aplicar a Macro-Estrutura no projeto RedWar...")

    for pasta in set(MAPA_FICHEIROS.values()):
        (base_dir / pasta).mkdir(parents=True, exist_ok=True)

    pastas_a_verificar = [
        base_dir,
        base_dir / "ai",
        base_dir / "tools" / "scripts",
        base_dir / "tools" / "analytics",
        base_dir / "tools" / "balance",
        base_dir / "online" / "network",
        base_dir / "online" / "server",
        base_dir / "online" / "client",
        base_dir / "deploy" / "packaging",
        base_dir / "docs",
        base_dir / "logs",
        base_dir / "data",
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

    for root, dirs, files in os.walk(base_dir, topdown=False):
        for name in dirs:
            dir_path = Path(root) / name
            if name not in {".git", ".vscode", "venv", "ai", "tools", "engine", "ui", "data", "logs"}:
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        print(f"🗑️ Pasta vazia limpa: {dir_path.relative_to(base_dir)}")
                except Exception:
                    pass

    if movidos == 0:
        print("✨ A estrutura já está perfeita!")


if __name__ == "__main__":
    organizar_projeto()
