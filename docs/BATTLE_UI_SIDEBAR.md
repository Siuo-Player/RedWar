# RedWar — Battle Sidebar

## Estado atual

A primeira arquitetura funcional foi integrada no #184 e a camada Encyclopedia/contexto foi posteriormente consolidada (#278–#281). A geometria responsiva e o tema semântico também foram integrados (#274–#277).

**Estado de conhecimento:** a arquitetura e os componentes descritos abaixo estão `IMPLEMENTED`; a validação visual/UX ainda é `OPEN`/`UNVERIFIED` nas dimensões listadas nesta página. Não reabrir o desenho estrutural apenas por existirem snapshots antigos.

## Contrato

```text
Selected Hero
    = estado persistente

Hovered Cell / Context
    = estado transitório

Actions
    = superfície contextual de decisão
```

Uma ação legal executa diretamente. Quando existem várias ações legais para o mesmo contexto, o painel expõe a escolha completa. `1..9` e `ESC` mantêm a interação navegável. O tabuleiro continua visível e o renderer não é autoridade de legalidade.

A legalidade pertence ao domínio de jogo e à fronteira canónica de ações documentada em [`HERO_SYSTEM.md`](HERO_SYSTEM.md) e [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Encyclopedia

A informação do herói permanece consultável durante a batalha através do contexto canónico usado pelo painel. Isso inclui regras relevantes, passivas e spells; não deve existir uma segunda fonte de regras apenas para a UI.

## Validação restante

Estas atividades são `VALIDATION`, não implementação da arquitetura:

- desktop largo/médio/estreito;
- resize sem destruir a semântica dos estados;
- keyboard/focus;
- sinalização não dependente apenas de cor;
- recuperação de destinos ilegais;
- silêncio/stun/lifespan/cooldown e efeitos;
- cenário visual de stress FrostMage/NEVADA;
- captura determinística de cenas.

Uma conclusão de UX só deve ser promovida a `VALIDATED` quando houver evidência de interação/inspeção visual adequada.

Fonte operacional da sequência: [`ROADMAP.md`](ROADMAP.md).

## Explicit feedback for blocked spells

When the selected hero is silenced by an active opposing Inquisitor, the selected-hero status must state that spells are unavailable and give the recovery action (move outside the Inquisitor's configured aura). This status is informational only: it must call the engine's read-only silence query rather than reimplementing radius/turn-state rules in the UI. An active Inquisitor's aura suppresses spells, not movement; the UI must not imply that the entire hero is unable to act. This feedback does not resolve or change the strategic outcome of the separate 16-FrostMage-vs-Inquisitor endgame report (#444), whose exact replay is still required for a complete reproduction.
