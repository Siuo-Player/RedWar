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

### License resolution

The upstream corpus is **not uniformly CC BY 3.0**. The official `license.txt` declares CC BY 3.0 as the default and explicitly marks some contributors, including **Viscious Speed** and **Zeromancer**, as **CC0**.

The matcher reads the pinned corpus `license.txt` and resolves the license from the contributor folder rather than attaching a repository-wide hardcoded license to every match. If contributor-folder mapping cannot be established, the match is left without a resolved license and is forced to `UNRESOLVED`.

### Performance

The corpus is rasterized once per SVG for a given audit run and the normalized variants are reused for all local assets. This avoids rasterizing the same upstream SVG once for every local PNG.

The renderer/normalizer preserves the local export convention (256×256 source convention, black background, square SVG rendering, gradient/plain mode, black icon, reset frame) through normalized foreground geometry and multiple background variants. A high numerical similarity score is not by itself sufficient to claim authorship.

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

The generated manifest records the pinned corpus revision, visual evidence, author, and license resolution metadata per candidate. Do not change unresolved or ambiguous entries to positive attribution statuses without image evidence.

The tool is an audit utility, not a permission grant and not legal advice.
