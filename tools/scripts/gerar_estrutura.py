import os
from pathlib import Path

# Pastas a ignorar para não poluir o ficheiro de texto com ruído do sistema ou compilação
IGNORAR_PASTAS = {'.git', '.vscode', 'venv', '__pycache__', 'build', 'dist', '.idea'}

def gerar_arvore(diretorio: Path, prefixo: str = "") -> list:
    linhas = []
    try:
        # Ordenar: pastas primeiro, seguidas dos ficheiros alfabeticamente
        caminhos = sorted(diretorio.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return linhas

    # Filtrar diretórios indesejados
    caminhos = [p for p in caminhos if p.name not in IGNORAR_PASTAS]

    for i, caminho in enumerate(caminhos):
        is_last = (i == len(caminhos) - 1)
        conector = "└── " if is_last else "├── "
        
        linhas.append(f"{prefixo}{conector}{caminho.name}")
        
        if caminho.is_dir():
            extensao_prefixo = "    " if is_last else "│   "
            linhas.extend(gerar_arvore(caminho, prefixo + extensao_prefixo))
            
    return linhas

def exportar_estrutura():
    base_dir = Path.cwd()
    logs_dir = base_dir / "logs"
    
    # Garantir que a pasta 'logs' existe na raiz do projeto
    logs_dir.mkdir(exist_ok=True)
    
    # Gerar o ficheiro no caminho especificado
    ficheiro_saida = logs_dir / "estrutura_atual.txt"
    
    linhas_arvore = [f"REDWAR - ARQUITETURA DE DIRETÓRIOS\n==================================\n."]
    linhas_arvore.extend(gerar_arvore(base_dir))
    
    texto_final = "\n".join(linhas_arvore)
    
    with open(ficheiro_saida, "w", encoding="utf-8") as f:
        f.write(texto_final)
        
    print(f"✅ Estrutura do projeto mapeada com sucesso em: {ficheiro_saida.relative_to(base_dir)}")

if __name__ == "__main__":
    exportar_estrutura()