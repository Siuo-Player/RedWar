# RedWar — Licenças e Conteúdo de Terceiros

> Este documento é uma política de preparação, não uma declaração jurídica definitiva.

## 1. Código do jogo

A intenção é que o código do produto possa permanecer sob controlo do autor mesmo com o repositório público.

Antes do lançamento público deve ser escolhida uma licença explícita para cada componente que será distribuído.

## 2. Ares

A intenção é que a Ares venha a ser a parte do projeto aberta a contribuições da comunidade.

A licença final da Ares deve ser escolhida antes da abertura formal do fluxo de contribuições automatizadas.

A escolha deve considerar:

- liberdade para forks;
- redistribuição;
- uso comercial ou não comercial;
- compatibilidade com bibliotecas usadas no C++;
- compatibilidade com qualquer eventual separação futura do repositório.

## 3. Código assistido por IA

O projeto foi desenvolvido com ajuda de ferramentas como modelos de IA.

Uma ferramenta de IA não é, por si só, uma garantia de que determinado trecho de código seja livre de problemas de licença.

Antes do lançamento/contribuição pública deve ser feita uma revisão de:

- código gerado;
- snippets copiados de fontes externas;
- dependências;
- licenças transitivas;
- documentação e textos derivados.

## 4. Assets

O projeto utiliza referências/arte de fontes externas, incluindo `game-icons.net`.

Cada asset usado na distribuição final deve ser associado à sua licença e, quando necessário, à atribuição exigida.

Não assumir que “está na internet” significa “pode ser distribuído”.

## 5. Dependências

Antes do lançamento deve existir uma lista de dependências com:

- nome;
- versão;
- licença;
- origem;
- uso no projeto.

Isto deve incluir dependências Python, C++ e web.

## 6. Assets gerados

Arte gerada por ferramentas de IA ou modificada a partir de assets externos deve ter a sua origem documentada quando necessário.

## 7. Política para Pull Requests

Um PR que introduza código ou assets incompatíveis com a política de licenças pode ser recusado independentemente da qualidade técnica.

## 8. Ação antes do lançamento

Checklist mínimo:

- [ ] escolher licença do produto;
- [ ] escolher licença do Ares;
- [ ] auditar `requirements.txt`;
- [ ] auditar dependências C++;
- [ ] auditar assets;
- [ ] documentar atribuições obrigatórias;
- [ ] rever conteúdo gerado por IA quando necessário;
- [ ] garantir que o README não promete direitos que a licença não concede.
