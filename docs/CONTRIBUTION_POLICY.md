# RedWar — Política de Contribuições

## Princípio

O projeto é público, mas a política de contribuição depende da área.

### Ares / IA

A ideia é que `ai/` possa funcionar como uma zona de contribuição aberta e automatizada.

A futura regra é semelhante ao Stockfish:

> uma alteração entra porque melhora a engine, não apenas porque alguém a escreveu.

Uma pipeline de Arena deverá comparar a versão candidata com a versão anterior e aceitar apenas melhorias segundo critérios definidos pelo projeto.

### Jogo/produto

O restante projeto continua sob revisão manual do autor.

Isto inclui:

- regras;
- heróis;
- UI;
- aplicação;
- web;
- multiplayer;
- infraestrutura;
- documentação de produto;
- balanceamento e conteúdo.

Contribuições são bem-vindas como propostas, mas só o autor decide o merge.

## Futuro split de repositórios

O projeto pode vir a separar:

```text
RedWar        → jogo/produto
RedWar-Ares   → engine de IA
```

Não é necessário fazer essa separação imediatamente.

## Licença

Antes da abertura formal do projeto Ares e antes de uma distribuição pública do produto, deve ser escolhida uma licença explícita para cada componente.

O código foi desenvolvido com assistência de ferramentas de IA; isso não elimina a necessidade de revisão de direitos, dependências e assets.

Assets de terceiros, incluindo os provenientes ou derivados de `game-icons.net`, devem ser auditados individualmente de acordo com a licença aplicável.

## Política de IA assistida

Uso de IA para ajudar a escrever código é permitido no processo de desenvolvimento.

A responsabilidade pela alteração continua a ser humana.

Uma contribuição assistida por IA deve:

- compilar;
- ter testes adequados;
- ser compreensível para quem a revê;
- não esconder conteúdo de terceiros incompatível com a licença;
- não introduzir comportamento sem documentação.
