# RedWar — Documentation Structure

A documentação é organizada por **autoridade e função**, não por acumulação de snapshots.

## Estrutura

```text
docs/
├── 00_INDEX.md
├── PROJECT_REASONING.md      ← eixo transversal de raciocínio
├── CURRENT_STATE.md          ← fotografia verificável
├── ROADMAP.md                ← única fila operacional
├── canonical domain docs     ← contratos atuais
├── DECISIONS/                ← histórico de decisões
├── audits/research           ← evidência/propostas
└── legacy/transitional       ← compatibilidade
```

## Source of truth

```text
implementação + testes
→ contrato canónico
→ decisão histórica
→ research/audit
→ proposta/backlog
→ snapshot
```

`ROADMAP.md` não é um segundo contrato técnico; é a ordem de trabalho. `PROJECT_REASONING.md` não é um segundo roadmap; é a explicação da dependência entre contratos e evidências.

## Regra anti-duplicação

Antes de criar um ficheiro novo, procurar primeiro no `00_INDEX.md`, no `PROJECT_REASONING.md` e no documento canónico do domínio. Só criar novo ficheiro para histórico, research independente ou contrato realmente separado.

Não criar outro current-state/roadmap/backlog para resolver drift documental.

## Histórico

`DECISIONS/` e snapshots datados devem conservar a sua data e contexto. Não os reescrever para parecerem atuais. A sincronização acontece nos documentos canónicos e em `ROADMAP.md`.

## Regra de sincronização

Quando o código muda um contrato:

```text
código/testes
+
documento canónico afetado
+
ROADMAP
```

Se a política muda, acrescentar também uma decisão histórica. `CURRENT_STATE` é atualizado para refletir o novo baseline, mas não substitui os contratos.
