import os

# Pastas que não queremos ver no mapeamento
PASTAS_IGNORADAS = {'.git', '__pycache__', 'venv', 'env', '.pytest_cache', '.vscode', 'dist', 'build'}

def gerar_arvore(startpath):
    tree = []
    base_name = os.path.basename(os.path.abspath(startpath))
    tree.append(f"📁 {base_name}/")
    
    for root, dirs, files in os.walk(startpath):
        # Filtrar pastas ignoradas modificando a lista 'dirs' in-place
        dirs[:] = [d for d in dirs if d not in PASTAS_IGNORADAS]
        dirs.sort()
        files.sort()
        
        level = root.replace(startpath, '').count(os.sep)
        
        if level > 0:
            indent = '│   ' * (level - 1) + '├── '
            folder_name = os.path.basename(root)
            tree.append(f"{indent}📁 {folder_name}/")
        
        subindent = '│   ' * level + '├── '
        for i, f in enumerate(files):
            is_last = (i == len(files) - 1) and not dirs
            prefix = '│   ' * level + '└── ' if is_last else subindent
            tree.append(f"{prefix}📄 {f}")
            
    return '\n'.join(tree)

if __name__ == "__main__":
    caminho_base = os.getcwd()
    arvore = gerar_arvore(caminho_base)
    
    nome_ficheiro = "estrutura_atual.txt"
    with open(nome_ficheiro, "w", encoding="utf-8") as f:
        f.write("ESTRUTURA REAL DO PROJETO REDWAR\n")
        f.write("=================================\n\n")
        f.write(arvore)
        
    print(f"✅ Auditoria concluída! Abre o ficheiro '{nome_ficheiro}' para veres a estrutura.")