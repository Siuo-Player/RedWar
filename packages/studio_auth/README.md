# 🔐 Studio Auth Core (Zero Blast Radius Identity SDK)

Biblioteca universal, desacoplada e autónoma de autenticação e gestão de identidade para ecossistemas de múltiplos jogos e aplicações.

> [!IMPORTANT]
> **Zero Dependências Externas**: Construída exclusivamente sobre a biblioteca padrão do Python (`hashlib`, `hmac`, `secrets`, `base64`, `json`, `uuid`, `time`). Pode ser copiada diretamente para qualquer projeto Python (3.9+) sem conflitos de `requirements.txt`.

---

## 🎯 Por que usar este núcleo nos teus projetos?

1. **Raio de Explosão Zero (*Zero Blast Radius*)**:
   - Cada jogo define o seu próprio `project_slug` (ex.: `"redwar"`, `"space_battle"`, `"rpg_tactics"`).
   - O utilizador pode autenticar-se com a mesma Conta Google ou Conta Studio, mas o núcleo deriva um **Pairwise ID criptográfico único para cada jogo**:
     $$\text{PlayerID}_{\text{Jogo A}} \neq \text{PlayerID}_{\text{Jogo B}}$$
   - **Garantia**: Se a base de dados do Jogo A for violada, o atacante **NÃO consegue** descobrir a identidade do utilizador no Jogo B nem consegue usar os tokens de sessão noutros projetos.
2. **Três Níveis Prontos a Usar**:
   - **Convidado (Anónimo)**: Joga logo sem registo, sem e-mails e sem dados recolhidos.
   - **Google OIDC**: Login com 1 clique, nuvem segura, protegido pelo 2FA da Google.
   - **Conta Dedicada Studio**: Senha protegida por **PBKDF2-HMAC-SHA256 (600.000 iterações)** em conformidade com o OWASP 2023 e verificação em tempo constante (`hmac.compare_digest`).

---

## 🚀 Como Integrar noutro Projeto em 30 Segundos

### Opção 1: Copiar a pasta
Copia a pasta `packages/studio_auth/` para o diretório do teu novo projeto.

### Opção 2: Instalar localmente via pip
```bash
pip install -e /caminho/para/packages/studio_auth
```

---

## 💻 Exemplo de Uso no Backend (Python)

```python
from packages.studio_auth import StudioAuthCore, AuthMode

# 1. Inicializar para o teu novo jogo
auth = StudioAuthCore(
    project_slug="meu_outro_jogo",
    sector_salt="segredo-de-estudio-compartilhado-2026",
    secret_key="chave-secreta-de-assinatura-jwt",
    google_client_id="meu-app.apps.googleusercontent.com"
)

# 2. Criar uma sessão anónima de convidado
guest = auth.create_guest_session()
print(guest.player_id)  # ex.: "guest_8a7f9b1c"

# 3. Emitir token de sessão JWT à prova de adulteração (expira em 1 hora)
token = auth.issue_session_token(guest)

# 4. Validar token numa rota da API
session = auth.verify_session_token(token)
print(f"Utilizador autenticado: {session.username} ({session.player_id})")

# 5. Criar conta dedicada com hash seguro OWASP
salt, hash_key = auth.hash_password("SenhaUltraSegura!#2026")
valido = auth.verify_password("SenhaUltraSegura!#2026", salt, hash_key)
assert valido is True
```

---

## 🌐 Exemplo de Uso no Frontend (JavaScript / Web / Mobile WebView)

Inclui o ficheiro `client.js` no teu HTML:
```html
<script src="studio_auth_client.js"></script>
<script>
  // Inicializa com o slug do teu jogo
  const auth = new StudioAuthClient({ projectSlug: "meu_outro_jogo" });

  // Obtém o utilizador atual (convidado automático se não estiver logado)
  const user = auth.getSession();
  console.log("Player ID:", user.playerId);
  console.log("Modo:", user.authMode);

  // Login com Google
  // auth.loginWithGoogle({ name: "Nome do Google" });

  // Login com Conta Dedicada
  // auth.loginWithDedicated("Utilizador", "Senha");
</script>
```

---

## 📜 Conformidade com Padrões Internacionais
- **OpenID Connect Core 1.0 (Secção 8)**: Pairwise Pseudonymous Identifiers (PPID).
- **NIST SP 800-63B**: Digital Identity Guidelines & Lifecycle Management.
- **OWASP ASVS v4.0.3**: Application Security Verification Standard.
