# RedWar — Telemetry Evidence Report

`tools/telemetry/report.py` transforma eventos válidos em métricas descritivas.

## Métricas

- contagem total e por tipo de evento;
- decisões com opções expostas;
- decisões efetivamente selecionadas;
- cancelamentos explícitos;
- decisões expostas que chegaram a `action_selected`;
- latência entre exposição e seleção quando ambos existem e os timestamps são válidos.

O relatório não interpreta ausência de `action_selected` como rejeição ou preferência. Também não produz força, balanceamento ou causalidade.

## Uso

Pode ser usado para analisar a frequência de escolhas ambíguas, cancelamentos e tempos de decisão por sessão/build/UI schema. Conclusões de força ou balanceamento continuam dependentes dos protocolos independentes já existentes.
