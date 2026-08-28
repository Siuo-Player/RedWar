# RedWar — Licenças e Conteúdo de Terceiros

> Este documento descreve a política de licenciamento do repositório. Não substitui aconselhamento jurídico.

## 1. Código geral do projeto

O código próprio do produto e tooling geral do RedWar, fora do subsistema Ares em `ai/`, é distribuído sob a licença **MIT**. O texto da licença está em [`../LICENSE`](../LICENSE).

## 2. Ares

O código próprio do subsistema Ares em `ai/` é distribuído sob **GPL-3.0-or-later**. O aviso de licença está em [`../ai/LICENSE`](../ai/LICENSE).

A licença GPL é uma licença de software livre e não é uma licença "não comercial". A política do projeto não cobra uma licença pelo uso do código.

Esta licença aplica-se apenas ao código próprio do projeto. Componentes de terceiros dentro de `ai/` mantêm as suas licenças originais.

## 3. Componentes de terceiros

Os componentes de terceiros não são relicenciados pelo RedWar. Cada componente deve conservar os seus avisos, copyright e licença aplicáveis.

A auditoria atual identifica pelo menos:

| Componente | Localização / origem | Licença verificada | Observação |
| --- | --- | --- | --- |
| nlohmann/json 3.12.0 | `ai/cpp_engine/nlohmann/json.hpp` | MIT | O próprio ficheiro contém `SPDX-License-Identifier: MIT`. |
| pygame 2.5.2 | `requirements.txt` / PyPI | LGPL-2.1 | Dependência Python; os termos de pygame continuam aplicáveis. |
| pytest 9.0.3 | `requirements.txt` / PyPI | MIT | Dependência de testes. |
| websockets 12.0 | `requirements.txt` / PyPI | BSD-3-Clause | Dependência de rede/websocket. |
| Cython | `requirements.txt` / PyPI | Apache-2.0 | Ferramenta/dependência de build; requisito não totalmente pinado. |

Fontes oficiais consultadas:

- pygame 2.5.2: https://pypi.org/project/pygame/2.5.2/
- pytest: https://pypi.org/project/pytest/
- websockets 12.0: https://pypi.org/project/websockets/12.0/
- Cython: https://pypi.org/project/Cython/

O `nlohmann/json.hpp` vendorizado contém diretamente os avisos SPDX de copyright e MIT.

## 4. Game Icons

Os PNGs em `ui/assets/` foram copiados manualmente de game-icons.net, segundo a proveniência fornecida pelo autor do repositório.

A coleção oficial `game-icons/icons` declara os seus SVGs como **CC BY 3.0**, com ficheiro de licença que identifica os autores e pede a inclusão de uma menção do tipo `Icons made by {author}` em trabalhos derivados.

Fontes oficiais:

- coleção: https://github.com/game-icons/icons
- licença: https://github.com/game-icons/icons/blob/master/license.txt
- site: https://game-icons.net/

A correspondência de cada PNG local com o SVG original é mantida em [`assets/game-icons-attribution.json`](assets/game-icons-attribution.json). Não são inferidos autores a partir do nome do ficheiro: um resultado só pode ser promovido a `CONFIRMED` ou `HIGH CONFIDENCE` quando o matcher tem evidência suficiente.

A ferramenta permanente de auditoria está em [`../tools/licensing/match_game_icons.py`](../tools/licensing/match_game_icons.py), com instruções em [`../tools/licensing/README.md`](../tools/licensing/README.md).

### Convenção local de renderização

Os PNGs foram produzidos com Game Icons Studio segundo a convenção declarada pelo autor:

- 256 × 256;
- background: black;
- shape: square;
- type: gradient;
- gradient: plain;
- icon colour: black;
- frame: reset / back to zero / reset background.

A auditoria distingue o SVG original do PNG transformado localmente. Redimensionamento, recoloração ou composição não removem a obrigação de manter a atribuição aplicável.

## 5. Política para novos terceiros

Antes de adicionar código, imagens, fontes, dados ou outros materiais externos:

1. identificar a origem;
2. identificar a licença aplicável no próprio material ou na fonte oficial;
3. verificar compatibilidade com a distribuição pretendida;
4. preservar copyright/SPDX/attribution notices;
5. registar a proveniência quando ela for relevante para uma futura auditoria.

Nunca incorporar material apenas porque "está na internet".

## 6. Secrets e histórico

O repositório é público. Não devem ser adicionados tokens, passwords, API keys, private keys ou quaisquer credenciais.

Uma auditoria de padrões de secrets no conteúdo atual não encontrou correspondências para `ghp_` nem para `BEGIN PRIVATE KEY`. Isso não substitui uma análise histórica especializada nem constitui garantia absoluta de ausência de secrets no histórico.
