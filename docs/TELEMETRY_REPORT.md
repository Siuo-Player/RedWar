# RedWar — Telemetry Evidence Report

`tools/telemetry/report.py` transforma eventos válidos em métricas descritivas.

Mede contagem de eventos, escolhas expostas, seleções, cancelamentos explícitos, decisões concluídas e latência observada entre exposição e seleção.

Ausência de `action_selected` não é interpretada como rejeição ou preferência. O relatório também não é evidência de força, balanceamento ou causalidade; essas conclusões continuam dependentes dos protocolos independentes de avaliação.
