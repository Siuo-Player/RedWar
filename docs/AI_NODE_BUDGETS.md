# Ares node budgets

The trainer deliberately uses small node budgets so 200 sequential games finish quickly:

- Iniciante: 1,000 nodes
- Intermédio: 5,000 nodes
- Avançado: 10,000 nodes

Gameplay bots use higher budgets so the real game gets stronger search:

- Iniciante: 5,000 nodes
- Intermédio: 25,000 nodes
- Avançado: 50,000 nodes

The 5x ratio is intentional. It can be increased to 10x later if measured turn time remains within the target of roughly 0.5-1.0 s/turn.
