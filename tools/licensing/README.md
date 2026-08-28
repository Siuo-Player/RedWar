# RedWar licensing tools

## `match_game_icons.py`

Audits the PNG assets in `ui/assets/` against the official Game Icons corpus:

`https://github.com/game-icons/icons`

The tool intentionally does not treat filenames as attribution evidence. It rasterizes source SVGs with CairoSVG, normalizes the local PNG and source rendering, computes image similarity, and classifies the best candidate as:

- `CONFIRMED`
- `HIGH CONFIDENCE`
- `AMBIGUOUS`
- `UNRESOLVED`

The current implementation uses conservative thresholds and preserves the second-best score so ambiguous cases can be reviewed rather than silently accepted.

### Reproducible usage

Obtain a pinned checkout of the official corpus first. For example:

```bash
git clone https://github.com/game-icons/icons.git third_party/game-icons-icons
cd third_party/game-icons-icons
git checkout <PINNED_COMMIT>
cd ../..
```

Install the audit-only dependencies:

```bash
python -m pip install pillow cairosvg
```

Run:

```bash
python tools/licensing/match_game_icons.py \
  --assets ui/assets \
  --corpus third_party/game-icons-icons \
  --output tools/licensing/game_icons_manifest.json
```

The official corpus license is CC BY 3.0 (with the repository's stated attribution requirements). Do not change the local attribution manifest from `UNRESOLVED`/`AMBIGUOUS` to a positive status without image evidence.

The tool is an audit utility, not a permission grant and not legal advice.
