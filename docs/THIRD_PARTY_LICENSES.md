# RedWar — Third-Party Licenses and Attribution

This document is the concise human-readable companion to the machine-maintained provenance records.

## Game Icons

RedWar uses PNG assets copied from the Game Icons collection at https://game-icons.net/.

The official Game Icons repository is:
https://github.com/game-icons/icons

The collection is provided under Creative Commons Attribution 3.0 (CC BY 3.0), with contributor-specific authorship recorded by the upstream project:
https://github.com/game-icons/icons/blob/master/license.txt

Attribution must be retained when a Game Icons asset is copied, resized, recolored, or otherwise transformed.

### Current local assets

The current repository contains 19 PNGs under `ui/assets/`. Their original icon/author mappings are intentionally not guessed from filenames. The machine-readable status is in:

- `tools/licensing/game_icons_manifest.json`
- `docs/assets/game-icons-attribution.json` (created/updated by the audit)

Until an image comparison has enough evidence, an entry remains `UNRESOLVED` and must not be presented as an attribution.

## Python dependencies

The direct dependencies currently declared in `requirements.txt` are:

| Package | Declared version | License |
| --- | --- | --- |
| pygame | 2.5.2 | LGPL-2.1 |
| pytest | 9.0.3 | MIT |
| websockets | 12.0 | BSD-3-Clause |
| Cython | >=3.0.0 | Apache-2.0 |

The versions/licenses were checked against the corresponding package metadata on PyPI during the public-release audit.

## Vendored C++ dependency

`ai/cpp_engine/nlohmann/json.hpp` is vendored source from nlohmann/json. The file itself carries:

```text
SPDX-CopyrightText: 2013 - 2025 Niels Lohmann <https://nlohmann.me>
SPDX-License-Identifier: MIT
```

Its MIT notice must remain intact.

## General rule

Third-party material is not relicensed by RedWar merely because it is stored in this repository. Copyright notices, SPDX identifiers and attribution requirements must remain attached to the original material.
