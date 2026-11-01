# 🌐 RedWar — Guia Oficial de Publicação e Hosting Gratuito na Internet

> Este guia explica detalhadamente como publicar e jogar o **RedWar** gratuitamente na internet (100% Free / Zero Custos) sem gastar dinheiro em infraestrutura.

---

## 🚀 Arquitetura de Publicação Gratuita

O RedWar utiliza uma arquitetura moderna desacoplada:
1. **Frontend Web**: Hospedado no **GitHub Pages** (gratuito, com CDN global e HTTPS automático).
2. **Backend WebSocket & REST API**: Hospedado num serviço de contentores gratuito (**Render.com**, **Fly.io** ou **HuggingFace Spaces**) com WSS automático.

```
                  ┌───────────────────────────────┐
                  │    GitHub Pages (Frontend)    │
                  │  https://<user>.github.io/... │
                  └──────────────┬────────────────┘
                                 │
                     HTTPS / WSS │ (Internet)
                                 ▼
                  ┌───────────────────────────────┐
                  │   Free Cloud Container (WSS)  │
                  │  (Render.com / Fly.io / HF)   │
                  │   WebSocket Multi-Room Server │
                  └───────────────────────────────┘
```

---

## 1. Publicação do Frontend no GitHub Pages (1 Clique)

O repositório já inclui o workflow oficial de CI/CD em [`.github/workflows/deploy_web.yml`](../.github/workflows/deploy_web.yml).

### Passos:
1. No repositório GitHub, aceda a **Settings** → **Pages**.
2. Em **Build and deployment** → **Source**, selecione **GitHub Actions**.
3. Em qualquer push para a branch `main` que altere ficheiros em `deploy/web/`, o GitHub Actions publica automaticamente o jogo.
4. O seu jogo fica imediatamente disponível no link:
   ```text
   https://<seu-utilizador>.github.io/RedWar/
   ```

---

## 2. Publicação do Backend WebSocket (Gratuito via Docker)

O projeto inclui um [`Dockerfile`](../Dockerfile) e [`docker-compose.yml`](../docker-compose.yml) prontos para produção.

### Opção A: Render.com (Recomendado — Plano Gratuito)
1. Crie uma conta gratuita em [render.com](https://render.com/).
2. Clique em **New** → **Web Service**.
3. Conecte o repositório GitHub do RedWar (`Siuo-Player/RedWar`).
4. Configurações:
   - **Environment**: Docker
   - **Plan**: Free (0$/mês)
   - **Port**: 8000 (ou 8765)
5. Clique em **Deploy Web Service**. O Render gera um domínio seguro com HTTPS e WSS, por exemplo: `https://redwar-server.onrender.com`.

### Opção B: HuggingFace Spaces (100% Gratuito Permanente)
1. Crie um novo Space no [huggingface.co/spaces](https://huggingface.co/spaces).
2. Selecione o SDK **Docker**.
3. Conecte o repositório RedWar.
4. O HuggingFace disponibiliza imediatamente o container com HTTPS e WebSockets seguros integrados.

### Opção C: Fly.io (Alocação Gratuita de Containers)
1. Instale o CLI `flyctl`:
   ```bash
   fly launch
   fly deploy
   ```
2. O servidor fica ativo em `https://<seu-app>.fly.dev`.

---

## 3. Execução Local com Docker

Caso queira executar localmente o ambiente idêntico ao de produção:

```bash
docker compose up --build
```

O jogo estará disponível em:
- **Web UI & REST API**: `http://localhost:8000/`
- **Servidor WebSocket**: `ws://localhost:8765/`

---

## 4. Segurança e Boas Práticas

Conforme estipulado na [Política de Segurança](../SECURITY.md):
- **Rate Limiting Ativo**: Cada conexão WebSocket está limitada a 30 mensagens/segundo via Token Bucket para evitar spam ou inundações DoS.
- **Tamanho Máximo de Mensagem**: 64 KB por frame para prevenir estouro de memória.
- **Zero PII**: Nenhuma palavra-passe ou dados pessoais são exigidos ou persistidos.
