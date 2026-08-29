# RedWar — Telemetry Evidence Report

`tools/telemetry/report.py` transforma uma sequência válida de `TelemetryEvent` em métricas descritivas.

## Métricas atuais

- contagem total e por tipo de evento;
- número de decisões com opções expostas;
- número de decisões efetivamente selecionadas;
- número de cancelamentos explícitos;
- número de decisões expostas que chegaram a `action_selected`;
- latência entre `action_choices_exposed` e `action_selected`, quando ambos existem e os timestamps são válidos.

O relatório não trata ausência de `action_selected` como rejeição. Também não calcula preferência por ação, qualidade da decisão, força ou causalidade a partir desta telemetria.

## Uso analítico

Esta camada é adequada para perguntas como:

- quantas escolhas ambíguas foram realmente apresentadas;
- quantas foram canceladas explicitamente;
- quanto tempo passou entre exposição e seleção;
- comparar UX entre builds ou versões da sidebar, usando a provenance da sessão.

Qualquer conclusão sobre balanceamento, força da Ares ou causalidade deve continuar a utilizar os protocolos independentes de Strength Evaluation e os conjuntos de validação/hold-out já existentes.
