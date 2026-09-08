# RedWar — Battle Sidebar

## Estado atual

A primeira arquitetura funcional foi integrada no #184 e a camada Encyclopedia/contexto foi posteriormente consolidada (#278–#281). A geometria responsiva e tema semântico também foram integrados (#274–#277). O trabalho restante é **validação visual/UX**, não redesenho arbitrário da arquitetura.

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

A legalidade pertence ao domínio de jogo e à fronteira canónica de ações documentada em [`HERO_SYSTEM.md`](HERO_SYSTEM.md) e [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## Encyclopedia

A informação do herói deve permanecer consultável durante a batalha através do contexto canónico usado pelo painel. Isso inclui regras relevantes, passivas e spells; não deve existir uma segunda fonte de regras apenas para a UI.

## Validação restante

- desktop largo/médio/estreito;
- resize sem destruir a semântica dos estados;
- keyboard/focus;
- sinalização não dependente apenas de cor;
- recuperação de destinos ilegais;
- silêncio/stun/lifespan/cooldown e efeitos;
- cenário visual de stress FrostMage/NEVADA;
- captura determinística de cenas.

Fonte operacional da sequência: [`ROADMAP.md`](ROADMAP.md).
