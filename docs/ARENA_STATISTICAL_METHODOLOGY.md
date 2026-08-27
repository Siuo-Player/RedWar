# Arena Statistical Methodology

## Objetivo

A Arena é o principal instrumento para medir a força relativa da Ares. Os benchmarks dirigidos e o hold-out têm funções complementares de regressão e generalização; não substituem a comparação de força através de partidas.

## 1. A unidade experimental deve ser um par quando as cores são invertidas

Quando a Arena joga a mesma abertura duas vezes, trocando as cores do challenger e do baseline, as duas partidas não devem ser tratadas como observações independentes.

O desenho recomendado é:

```text
opening O
  ├─ game 1: Ares = White, baseline = Black
  └─ game 2: baseline = White, Ares = Black
                 ↓
          one paired observation
```

Isto permite cancelar parte do efeito da cor e modelar explicitamente a relação entre os dois resultados. O Fishtest usa este princípio através do modelo **pentanomial**, em vez de reduzir imediatamente tudo a W/D/L independentes. A documentação do Fishtest explica que a estrutura dos pares pode reduzir a variância e poupar partidas. citeturn190723search2turn162297search2

## 2. Pentanomial para jogos pareados

Para um par de partidas, contando pontos do challenger como 0, 0.5 ou 1 por partida, existem cinco resultados agregados:

| Resultado do par | Pontos challenger |
|---|---:|
| LL | 0 |
| LD / DL | 0.5 |
| DD / WL / LW | 1 |
| WD / DW | 1.5 |
| WW | 2 |

A implementação futura da Arena deve conservar os dois resultados individuais e derivar estes bins, em vez de armazenar apenas a percentagem final de vitórias.

## 3. Elo continua útil, mas como efeito descritivo

O RedWar pode continuar a apresentar um `Elo-equivalent delta` para tornar resultados compreensíveis. Porém, esse número não é por si só a decisão estatística de promoção.

A cadeia recomendada é:

```text
games
 ↓
paired results
 ↓
pentanomial statistics
 ↓
strength effect / Elo-equivalent
 ↓
uncertainty
 ↓
sequential test
```

O Fishtest separa precisamente medição de Elo e decisão através de SPRT/GSPRT. citeturn190723search0turn190723search2

## 4. SPRT/GSPRT

O teste futuro deve comparar explicitamente uma hipótese de ausência de ganho com uma hipótese de ganho mínimo relevante. O Fishtest usa GSPRT para esse processo e deixa que o número de partidas seja determinado pela evidência, em vez de fixar previamente um número arbitrário. citeturn190723search1turn190723search2

A literatura estatística dá fundamentação independente ao uso de testes sequenciais generalizados, incluindo Li, Liu e Ying (2014), *Generalized Sequential Probability Ratio Test for Separate Families of Hypotheses*. citeturn162297search12

## 5. Viés do opening book / conjunto experimental

Uma Arena pode ser enviesada pelo conjunto inicial de posições. O próprio Fishtest documenta selection bias associado ao opening book e recomenda analisar esse efeito explicitamente. citeturn190723search1

No RedWar isso implica:

- openings/seeds devem ser determinísticos e versionados;
- a distribuição de cores deve ser auditável;
- pares devem usar a mesma abertura quando a comparação se destina a cancelar o efeito da cor;
- o resultado deve guardar a identidade do par;
- hold-out continua separado do desenvolvimento.

## 6. Não assumir independência quando o desenho não a suporta

A experiência do próprio Fishtest mostra correlação negativa observável entre as duas partidas de um par com cores invertidas. Isto não é um detalhe académico: tratar os jogos como independentes altera a variância estimada e pode tornar o teste menos eficiente. citeturn162297search2

## 7. Normalized Elo / precisão experimental

Para comparar contextos diferentes, a investigação e documentação de Fishtest também introduzem normalized Elo/normalized t-value, relacionando o efeito observado com a quantidade de jogos necessária para demonstrá-lo. Isto é uma referência futura para comparar condições de teste com diferentes draw rates ou books, sem confundir efeito de força com sensibilidade do contexto. citeturn162297search36turn162297search37

## 8. Regra para a implementação do RedWar

Não ligar o SPRT ao gate antes de existirem:

1. armazenamento explícito de pares;
2. contagem pentanomial testada;
3. auditoria de cores/openings/seeds;
4. validação com partidas reais da Ares;
5. testes sintéticos da estatística;
6. política documentada para draws e pares incompletos.

A implementação atual de Elo batch permanece deliberadamente descritiva até estes componentes existirem.

## 9. Interpretação do dataset real de 100 jogos

A primeira experiência real persistida contém **100 partidas organizadas em 50 pares completos**. A unidade pareada é válida para a comparação controlada, mas não deve ser descrita como 50 condições experimentais independentes: o dataset reutiliza parte das combinações de opening/seed.

A distinção necessária é:

```text
50 paired game units
        ≠
50 independent experimental conditions
```

Repetições de opening/seed podem ser úteis como replicação das mesmas condições. Ao mesmo tempo, reduzem a diversidade efetiva da população experimental e limitam generalização para outras posições, books ou seeds.

Portanto, resultados deste dataset devem ser reportados como evidência **condicionada à população experimental definida pelo manifest**, não como uma estimativa automaticamente representativa da força global em toda a distribuição de jogo.

O próximo desenho experimental deve preferir uma mistura explícita de:

```text
replicação controlada
+
variação/estratificação da população
```

em vez de apenas aumentar N mantendo exatamente as mesmas condições.

## 10. Paired bootstrap: semântica do intervalo

O bootstrap emparelhado pode produzir quantis 2,5% e 97,5% para descrever a distribuição empírica do efeito reamostrado. **Esses percentis não devem ser apresentados automaticamente como um IC95% calibrado**.

Até existir uma justificação estatística específica para esse uso no estimador escolhido, a nomenclatura recomendada é:

```text
paired bootstrap interval
ou
bootstrap percentile interval (descriptive)
```

Quando a metodologia de inferência mudar, a semântica do intervalo deve ser atualizada explicitamente em conjunto com testes e documentação.

## 11. Intransitividade: deteção não é prova de estabilidade estratégica

Um padrão observado como:

```text
A > B
B > C
C > A
```

é evidência de um ciclo observado na amostra, não prova suficiente de uma relação de intransitividade estratégica estável no jogo.

Antes de tratar um ciclo como propriedade do metagame, o projeto deve verificar:

- repetição do padrão em novas partidas;
- sensibilidade a opening/seed/cor;
- incerteza dos efeitos por matchup;
- estabilidade da população/estratégias comparadas.

A análise de ciclos deve portanto continuar como ferramenta diagnóstica e não como decisão automática de balanceamento.

## 12. SPRT e dados reais

A existência de um SPRT isolado e de um dataset real não autoriza ainda ligar o teste ao gate de promoção.

No estado atual, permanecem gaps importantes:

- ausência de draws no primeiro dataset real;
- necessidade de testar comportamento com draws legítimos;
- validação de jogos inválidos/incompletos;
- calibração da escala de efeito;
- validação da independência/estrutura de dependência assumida pelo modelo;
- definição de população experimental e estratificação;
- preservação do raw Arena record para investigações posteriores.

O pipeline correto permanece:

```text
raw Arena JSONL
→ durable derived dataset
→ paired/pentanomial audit
→ population/context audit
→ uncertainty calibration
→ realistic SPRT validation
→ promotion decision
```

## 13. Preservação da proveniência

O dataset derivado deve guardar referência ao raw Arena artifact e à execução que o produziu. O compact dataset é uma vista analítica conveniente; não deve substituir o raw game record para:

- replay-level investigation;
- debugging de invalidez;
- verificação de termination reason;
- reconstrução de uma discrepância estatística.

O contrato de proveniência deve distinguir claramente:

```text
raw source
→ derived dataset
→ derived statistics/audit
```

## 14. Referências principais

- Stockfish/Fishtest — Statistical Methods and Algorithms in Fishtest: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html
- Stockfish/Fishtest — Creating a test: https://official-stockfish.github.io/docs/fishtest-wiki/Creating-my-first-test.html
- Stockfish/Fishtest — FAQ: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-FAQ.html
- van den Bergh — *Normalized Elo*: https://cantate.be/Fishtest/normalized_elo.pdf
- van den Bergh — *Comments on Normalized Elo*: https://www.cantate.be/Fishtest/normalized_elo_practical.pdf
- Li, Liu & Ying — *Generalized Sequential Probability Ratio Test for Separate Families of Hypotheses*: https://pmc.ncbi.nlm.nih.gov/articles/PMC4941833/
