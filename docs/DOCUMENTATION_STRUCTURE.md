# RedWar — Documentation Structure

A documentação é organizada por **autoridade e função**, não por acumulação de snapshots.

## Estrutura

```text
docs/
├── 00_INDEX.md
├── CURRENT_STATE.md          ← baseline verificável atual
├── ROADMAP.md                ← única fila operacional
├── PROJECT_REASONING.md      ← cadeia causal transversal
├── canonical domain docs     ← contratos atuais
├── DECISIONS/                ← histórico de decisões
├── audits/research           ← evidência/propostas
└── legacy/transitional       ← compatibilidade histórica
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

`ROADMAP.md` não é um segundo contrato técnico. `PROJECT_REASONING.md` não é um segundo roadmap.

## Regra de ownership

> **Before creating documentation for an existing subject, locate its canonical owner and update that owner unless the new artifact is genuinely historical, experimental or contractually distinct.**

Antes de adicionar um ficheiro, verificar `00_INDEX.md`, `CURRENT_STATE.md`, `ROADMAP.md` e o proprietário do domínio. Um novo documento não deve existir apenas porque um estado anterior ficou desatualizado.

## Estados documentais vs estados do sistema

A documentação deve distinguir explicitamente:

```text
DOCUMENTED
IMPLEMENTED
TESTED
VALIDATED
PROVEN
```

Uma palavra não implica automaticamente a seguinte.

## Traceability obrigatória do roadmap

Para cada dependência consequente em [`ROADMAP.md`](ROADMAP.md), o bloco deve apontar para:

```text
objetivo
→ contrato canónico
→ evidência base
→ acceptance gate
```

e deve citar a passagem crítica do documento canónico quando a interpretação futura puder ser ambígua. O roadmap não deve duplicar a metodologia inteira, mas também não pode pedir que uma IA adivinhe por que um gate existe.

## Histórico

`DECISIONS/` e snapshots datados conservam data e contexto. Não os reescrever para parecerem atuais. Se o conhecimento atual mudou, sincronizar o contrato canónico, `CURRENT_STATE.md` e `ROADMAP.md`.

## Regra de sincronização

Quando o código muda um contrato:

```text
código/testes
+
documento canónico afetado
+
ROADMAP
```

Se a política muda, acrescentar também a decisão histórica. `CURRENT_STATE` atualiza o baseline e não substitui os contratos.

## Redundância controlada

Snapshots e audits podem existir para preservar a história. Não são fontes operacionais alternativas. Branches de documentação nunca vencem o `main`.
