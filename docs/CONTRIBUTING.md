# Contribuir para RedWar

## Modelo do projeto

O repositório é público, mas existem **dois níveis diferentes de contribuição**.

### Ares / `ai/`

A ideia é abrir a Ares à comunidade de forma semelhante ao espírito do Stockfish.

Uma alteração de IA não é aceite apenas porque compila.

Tem de demonstrar que melhora a engine segundo condições controladas.

Exemplos:

- maior força;
- melhor desempenho sem perda de força;
- correção de bug com melhoria mensurável;
- avaliação mais forte;
- redução de memória sem perda significativa.

### Restante projeto

Alterações em:

- `engine/`;
- `ui/`;
- `online/`;
- `tools/`;
- `deploy/`;
- documentação de produto;
- regras;

podem ser propostas publicamente, mas a aceitação/merge é manual e pertence ao autor.

## Branches

Alterações devem ser trabalhadas em branches próprias:

```bash
git switch -c nome-da-alteracao
```

Não trabalhar diretamente em `main`.

## Antes de abrir PR

Executar pelo menos:

```bash
pytest tests/
```

Se houver alterações C++:

```bash
cd ai/cpp_engine
g++ -std=c++17 -O3 board.cpp evaluate.cpp main.cpp movegen.cpp search.cpp -o engine
```

No ambiente Windows do projeto, o `pre-push` também executa uma pipeline local de build/testes.

## Alterações na IA

Para uma alteração de Ares, o PR deve explicar:

1. o problema;
2. o que foi alterado;
3. como foi medido;
4. contra que versão foi comparado;
5. condições da pesquisa;
6. número de jogos/posições;
7. resultado.

Não basta dizer “parece melhor”.

## Alterações de regras

As regras do jogo são propriedade do design do projeto.

Um PR pode sugerir:

- uma nova mecânica;
- um novo herói;
- alteração de uma regra;
- novo modo.

Mas deve deixar explícito que é uma proposta de design e não assumir que a implementação proposta é automaticamente a regra correta.

## Heróis

Antes de criar código especial:

1. verificar `engine/heroes_config.json`;
2. verificar `engine/HEROES_SCHEMA.md`;
3. verificar se o comportamento pode ser expresso pela configuração existente;
4. só adicionar lógica específica quando a habilidade for realmente nova.

## Testes

Mudanças de regras devem vir com regressões quando possível.

Testes prioritários:

- ações legais;
- ações ilegais;
- stun;
- segundo stun/morte;
- timers;
- efeitos;
- vitória;
- ausência de movimentos;
- hash;
- reversibilidade make/unmake.

## Commits

Preferir commits pequenos e semanticamente focados:

```text
fix: correct stun timer expiration
refactor: isolate move ordering
perf: reduce allocations in move generation
test: add fire effect regression
docs: update multiplayer architecture
```

## Documentação

Sempre que uma alteração mudar uma regra ou arquitetura, atualizar o documento correspondente.

Não escrever documentos como se uma funcionalidade futura já existisse.

## IA assistida

O projeto foi desenvolvido com assistência de ferramentas de IA. Isso não altera a responsabilidade humana pela revisão do código, pela escolha da licença e pelo uso de conteúdo de terceiros.

Qualquer contribuição assistida por IA deve ser tratada como código normal: deve ser compreendida, testada e revista antes de ser aceite.
