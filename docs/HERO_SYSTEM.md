# RedWar — Hero System

## Autoridade

Os dados estruturais dos heróis pertencem a `engine/heroes_config.json` e ao schema associado. A implementação pode conter código especializado enquanto o schema não representar uma mecânica de forma suficiente.

A regra transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md). Mudanças de mecânicas seguem [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## Ações

A camada canónica de ações distingue `MOVE`, `ATTACK`, `STUN`, `SPAWN` e `SPELL`. Uma ofensiva implementada como spell não deve ser artificialmente duplicada como `ATTACK`.

PR #291 consolidou a análise Python sobre o espaço de ação canónico; #306 tornou a fronteira explícita e #308 normaliza `execute_action()` através dela. PR #321 acrescentou `resolve_legal_action()` como seam de resolução canónica/legacy. **Isto não prova ainda que qualquer ação estruturalmente válida seja rejeitada por membership antes da mutação:** esse bloco continua aberto porque #317 documenta a diferença entre action-space e transition validation; #309/#315 não foram merged.

## Casos especiais já validados

- **Inquisitor:** a condição de silêncio e a exceção de Inquisitor atordoado têm regressão explícita em #292.
- **FrostMage:** `NEVADA` é `SPELL`; o código morto que sugeria um segundo mecanismo de STUN foi removido em #300 depois de cobertura para o comportamento ativo.
- **Special spells:** a paridade de legalidade é coberta em #303 para as ações especiais declaradas no contrato desse PR.

## Estado data-driven

O sistema continua **híbrido**. A configuração é fonte dos dados e vocabulary, mas ainda existem comportamentos especializados em código. A redução desse hardcoding é trabalho futuro, não evidência de que o sistema já seja totalmente declarativo.

## Níveis de evidência

Para evitar sobreinterpretação:

```text
DOCUMENTED
≠
IMPLEMENTED
≠
TESTED
≠
VALIDATED
≠
PROVEN para qualquer estado possível
```

As regressões de ações especiais provam os casos e condições que exercitam; não constituem por si só prova de semantic closure universal.

## Regra para nova mecânica

Uma nova mecânica só entra no contrato como concluída quando passa a cadeia relevante da matriz: configuração/schema quando aplicável → Python → C++ → ações → transição → RWEN → make/unmake → hash → differential → regressão → benchmark quando altera capacidade de search.

## Arquétipos do Catálogo Expandido

O catálogo de heróis de RedWar divide-se em 4 arquétipos estratégicos balanceados:
1. **Defesa e Controlo de Terreno:**
   - `Paladin` (custo 55): Linha de frente ágil com avanço ortogonal até 2 casas e ataque direto.
   - `Templar` (custo 15): Bloqueador robusto com contra-ataque.
   - `Obelisk` (custo 16) & `StoneWall` (custo 8): Estruturas defensivas de controle de espaço.
2. **Furtividade e Flanqueamento:**
   - `Shadowblade` (custo 65): Flanqueador diagonal com mobilidade fantasma (atravessa peças) até 3 casas.
   - `Nightshade` (custo 193): Mobilidade extrema ortogonal atravessando peças.
   - `Phantom` (custo 5): Salto em L e golpe espectral.
   - `Berserker` (custo 31): Dano em área em redor do alvo sem friendly fire.
3. **Magia, Área e Suporte:**
   - `FrostMage` (custo 5): Controle de área com Nevada e criação de gelo.
   - `Stormcaller` (custo 72): Atacante em raio elétrico com capacidade de stun à distância.
   - `Pyromancer` (custo 17): Terreno de fogo persistente.
   - `Inquisitor` (custo 128): Aura passiva de silêncio a raio 2.
   - `Cleric` (custo 58), `Trickster` (custo 26), `Geomancer` (custo 21), `Lich` (custo 11).
4. **Artilharia e Dano de Longo Alcance:**
   - `Ranger` (custo 40): Tiro de precisão com distância mínima de 2 casas.
   - `Sentry` (custo 96): Raio ortogonal direto de alta ameaça.
   - `BoneLord` (custo 86): Golpe em V e invocação de Bones em baixas inimigas.
   - `Dragoon` (custo 193): Mobilidade ortogonal e feitiço de salto.

