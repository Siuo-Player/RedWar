# RedWar — Decision & Knowledge Protocol

## 1. Regra fundamental

> **Qualquer pessoa ou IA deve conseguir continuar o desenvolvimento a partir do repositório, sem depender da conversa que originou a decisão.**

O repositório é a fonte operacional de verdade. Conversas, memória de um agente ou contexto local não podem ser requisitos ocultos para compreender por que uma alteração existe.

Uma decisão, descoberta, hipótese relevante ou resultado experimental deve ser documentado **logo que for conhecido e antes de alterar a implementação com base nele**.

## 2. Ordem obrigatória

Para mudanças que envolvam uma escolha técnica, científica, arquitetural, metodológica ou de produto:

```text
OBSERVAÇÃO / PROBLEMA
        ↓
DOCUMENTAR O FACTO
        ↓
DOCUMENTAR HIPÓTESE / ALTERNATIVAS
        ↓
ESCOLHER E JUSTIFICAR
        ↓
IMPLEMENTAR
        ↓
TESTAR / EXPERIMENTAR
        ↓
DOCUMENTAR RESULTADO
        ↓
ATUALIZAR ROADMAP / ESTADO
```

A documentação inicial deve preceder a implementação que depende da decisão. A documentação posterior regista o que realmente aconteceu e pode corrigir a hipótese inicial sem apagar o histórico.

## 3. O que é obrigatório documentar

Documentar imediatamente qualquer:

- descoberta de bug ou divergência semântica;
- escolha entre alternativas tecnicamente plausíveis;
- alteração de arquitetura ou fronteira entre módulos;
- mudança de algoritmo, heurística, métrica ou protocolo experimental;
- resultado de benchmark/Arena que altere uma decisão;
- limitação descoberta numa abordagem;
- hipótese que passe a orientar desenvolvimento;
- dependência externa relevante;
- decisão de não implementar algo que parecia previsto no roadmap;
- conflito entre documentação e implementação;
- resultado negativo que faça abandonar uma direção;
- decisão motivada por paper, standard, projeto externo ou experiência de outro engine.

Não é necessário criar um registo para alterações mecânicas sem decisão própria, como correção de typo, renome puramente local ou formatação sem efeito semântico.

## 4. Discovery Log vs Decision Record

Usar o nível mínimo que preserve o conhecimento.

### Discovery

Para uma descoberta factual:

```text
## Discovery: <título>
Data: YYYY-MM-DD
Estado: aberto | confirmado | refutado
Origem: teste / paper / código / CI / Arena / revisão

### Facto observado
...

### Evidência
...

### Impacto
...

### Próxima ação
...
```

### Decision Record

Para uma escolha:

```text
## Decision: <título>
Data: YYYY-MM-DD
Estado: proposta | aceite | substituída | rejeitada

### Contexto
...

### Problema
...

### Opções consideradas
1. ...
2. ...
3. ...

### Decisão
...

### Razão
...

### Evidência
- paper / documentação / teste / benchmark / Arena

### Consequências
#### Positivas
...
#### Negativas / custos
...

### Como validar
...

### Quando rever
...
```

## 5. Decisão antes de código

Não fazer:

```text
alteração de código
    ↓
procurar depois uma justificação
```

Preferir:

```text
problema
 ↓
facto + evidência
 ↓
opções
 ↓
decisão documentada
 ↓
código
```

Isto não exige conhecer antecipadamente a solução final. Uma hipótese pode ser documentada como hipótese. O objetivo é tornar explícito **o que se sabia, o que se acreditava e por que se escolheu testar determinada direção**.

## 6. Evidência e incerteza

Toda conclusão relevante deve distinguir:

```text
FACTO
→ observado diretamente

INFERÊNCIA
→ conclusão suportada pelos factos

HIPÓTESE
→ explicação ainda não demonstrada

DECISÃO
→ escolha de engenharia baseada na evidência disponível
```

Nunca transformar uma hipótese em facto apenas porque foi implementada.

Usar os níveis existentes em `ENGINEERING_METHODOLOGY_AND_RESEARCH.md` e no repositório de estudos. Uma fonte externa pode justificar um mecanismo sem provar que a mesma intervenção funciona em RedWar.

## 7. Papers e fontes externas

Quando uma decisão é inspirada por investigação externa:

```text
projeto
 ↓
fonte primária
 ↓
resumo / estudo no Project Studies
 ↓
interpretação para RedWar
 ↓
decisão
 ↓
validação local
```

O paper não deve ser citado apenas pelo título. Registar:

- referência completa;
- DOI ou identificador persistente;
- URL canónico;
- parte do trabalho relevante;
- afirmação científica suportada;
- limite dessa evidência;
- implicação específica para RedWar;
- teste local necessário.

O repositório `Siuo-Player/Siuo-Player-PROJECT-STUDIES` é a base de conhecimento complementar. O seu `REPOSITORY_PROTOCOL.md` define explicitamente que outra pessoa ou IA deve conseguir continuar sem a conversa de origem e estabelece o fluxo inventário → aquisição → leitura → síntese → aplicação → auditoria. RedWar segue esse princípio para decisões de engenharia. 

## 8. Quando não houver informação suficiente

Não preencher lacunas com memória ou suposição silenciosa.

Usar esta sequência:

```text
informação em falta
        ↓
procurar no RedWar
        ↓
procurar no Project Studies
        ↓
procurar paper / documentação primária
        ↓
se continuar em falta:
    registar a lacuna
        ↓
    formular pergunta / prompt de investigação
```

### Prompt padrão de investigação

```text
Contexto:
Estamos a desenvolver RedWar/Ares e a decisão <DESCREVER DECISÃO> precisa de fundamento.

Pergunta:
Qual é a melhor prática cientificamente/tecnicamente suportada para <PROBLEMA>?

Tarefas:
1. Procurar primeiro no repositório Siuo-Player/Siuo-Player-PROJECT-STUDIES.
2. Reutilizar paper cards e estudos existentes; não duplicar fontes.
3. Se a evidência for insuficiente, procurar papers académicos primários e surveys relevantes.
4. Priorizar fontes peer-reviewed, trabalhos seminais e documentação técnica primária.
5. Para cada fonte: resumir problema, método, resultados, limitações e relevância para RedWar.
6. Separar claramente a afirmação do paper da inferência para RedWar.
7. Propor uma decisão ou alternativas apenas depois da revisão da evidência.
8. Indicar como testar/falsificar a decisão localmente.
9. Registar DOI/URL e localização suficiente para futura auditoria.

Saída:
- evidência encontrada;
- fontes novas;
- conclusões;
- recomendação para RedWar;
- teste necessário;
- lacunas/incertezas.
```

## 9. Documentar descobertas antes de corrigir

Quando um teste encontra uma divergência:

```text
falha
 ↓
registar divergência
 ↓
identificar implementação de referência
 ↓
formular causa provável
 ↓
correção
 ↓
regressão
 ↓
atualizar discovery com resultado
```

Exemplo: a divergência Python/C++ de `ignite` deve ser preservada como conhecimento sobre a semântica, não apenas como um teste que ficou verde depois da correção.

## 10. Resultados negativos são conhecimento

Uma tentativa que falha deve permanecer documentada quando é tecnicamente relevante.

Registar:

- hipótese;
- alteração tentada;
- ambiente/orçamento;
- resultado;
- motivo conhecido ou hipótese explicativa;
- decisão de abandonar, modificar ou repetir;
- implicação para trabalhos futuros.

Isto impede que futuras pessoas/IA repitam experimentos já refutados sem saber porquê.

## 11. PR como unidade de conhecimento

Cada PR de desenvolvimento relevante deve permitir reconstruir:

```text
qual era o problema?
qual hipótese foi usada?
que decisão foi tomada?
o que foi alterado?
como foi testado?
o que foi descoberto durante o trabalho?
qual foi o resultado?
qual é o próximo passo?
```

Uma PR pode conter vários commits. O importante é que exista uma linha causal compreensível entre **evidência → decisão → implementação → validação**.

## 12. Ordem da documentação dentro da branch

A primeira alteração funcional de um bloco deve ser precedida, quando aplicável, por um commit de documentação que registe a decisão/hipótese que orienta o bloco.

Depois:

```text
commit docs: decision/discovery
        ↓
commit implementation
        ↓
commit tests
        ↓
commit docs: result/update
```

Não é obrigatório criar exatamente quatro commits; é obrigatório preservar essa informação no histórico da branch.

## 13. Roadmap e documentação viva

O `ROADMAP.md` responde a **o que vem a seguir**.

Este protocolo responde a **como sabemos por que estamos a fazer isso**.

`ENGINEERING_METHODOLOGY_AND_RESEARCH.md` responde a **quais princípios gerais orientam as decisões**.

Os documentos específicos respondem a **como o subsistema funciona agora**.

Se uma decisão alterar qualquer uma destas camadas, atualizar a camada correspondente imediatamente.

## 14. Anti-drift documental

Uma alteração não está concluída quando apenas o código funciona.

Antes do merge perguntar:

- A documentação descreve o comportamento atual?
- A razão da escolha está preservada?
- As alternativas importantes foram registadas?
- Descobertas durante a implementação foram adicionadas?
- O resultado experimental está associado ao commit/versão correta?
- O roadmap ainda representa o próximo passo real?
- Uma IA sem acesso à conversa entenderia a decisão?

Se a resposta à última pergunta for “não”, o bloco ainda tem dívida de conhecimento.

## 15. Relação com literatura

A política é inspirada por investigação sobre documentação de decisões de arquitetura. Estudos encontraram benefícios em qualidade/produtividade da documentação de decisões, maior sistematização de avaliação de alternativas por designers juniores e benefícios/limitações reais na adoção de ADRs. 

Referências principais:

- van Heesch, Avgeriou & Hilliard — *A documentation framework for architecture decisions*, com viewpoints para detalhe, relações, cronologia e stakeholders: https://research.rug.nl/en/publications/a-documentation-framework-for-architecture-decisions/
- van Heesch, Avgeriou & Tang — *Does decision documentation help junior designers rationalize their decisions?*: DOI https://doi.org/10.1016/j.jss.2013.01.057
- Tang et al. — *Decision architect – A decision documentation tool for industry*: DOI https://doi.org/10.1016/j.jss.2015.10.034
- van Heesch et al. — *An expert survey on kinds, influence factors and documentation of design decisions in practice*: DOI https://doi.org/10.1016/j.future.2014.12.002
- Ahmeti, Linder, Groner & Wohlrab — *Architecture Decision Records in Practice: An Action Research Study* (2024): https://zenodo.org/records/11635100
- Ahmeti et al. — *Exploring the Adoption and Effectiveness of Architecture Decision Records in Agile Software Development*: https://research.chalmers.se/en/publication/538920
- Nogueira, Silva & Conte — *One Size Fits All? An Empirical Comparison of ADR Templates regarding Comprehension, Usability, and Ease of Adoption*: https://arxiv.org/abs/2604.27333

A literatura também mostra que documentação demasiado rígida pode criar custos e que manutenção/atualização são problemas reais. Portanto o protocolo privilegia **documentação mínima suficiente, no momento certo, ligada a evidência e mantida viva**, em vez de burocracia.

## 16. Critério final

Uma pessoa nova no projeto deve conseguir pegar num bloco do roadmap, ler os documentos relevantes e reconstruir:

```text
estado atual
   ↓
problema
   ↓
evidência disponível
   ↓
decisão
   ↓
experimento/implementação
   ↓
resultado
   ↓
próximo passo
```

Sem essa cadeia, o conhecimento ainda está parcialmente fora do projeto.
