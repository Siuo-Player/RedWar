from __future__ import annotations

import json
from pathlib import Path
import re


def test_web_hero_rules_parity_with_engine_config():
    """Verify that deploy/web/app.js HERO_RULES matches engine/heroes_config.json for all 30 heroes."""
    json_path = Path("engine/heroes_config.json")
    heroes_cfg = json.loads(json_path.read_text(encoding="utf-8"))

    app_js_path = Path("deploy/web/app.js")
    app_js = app_js_path.read_text(encoding="utf-8")

    start = app_js.find("const HERO_RULES = {")
    end = app_js.find("};\n// Directions", start)
    if end == -1:
        end = app_js.find("};\r\n// Directions", start)
    if end == -1:
        end = app_js.find("};\n\n// Directions", start)
    if end == -1:
        end = app_js.find("};\r\n\r\n// Directions", start)

    assert start != -1 and end != -1, "HERO_RULES block not found in deploy/web/app.js"
    rules_block = app_js[start:end+2]

    assert len(heroes_cfg) == 30, f"Expected 30 heroes in config, found {len(heroes_cfg)}"

    for hero_name, info in heroes_cfg.items():
        expected_cost = info["cost"]
        expected_acronym = info["acronym"]

        # Check hero presence and casing
        idx = rules_block.find(f"  {hero_name}: {{")
        assert idx != -1, f"Hero '{hero_name}' missing or casing mismatched in deploy/web/app.js HERO_RULES"

        # Check cost
        cost_match = re.search(r"cost:\s*(\d+)", rules_block[idx:idx+300])
        assert cost_match is not None, f"Cost field missing for '{hero_name}' in HERO_RULES"
        actual_cost = int(cost_match.group(1))
        assert actual_cost == expected_cost, (
            f"Cost mismatch for '{hero_name}': expected {expected_cost} (engine), found {actual_cost} (web)"
        )

        # Check acronym
        acr_match = re.search(r"acronym:\s*\"([^\"]+)\"", rules_block[idx:idx+300])
        assert acr_match is not None, f"Acronym field missing for '{hero_name}' in HERO_RULES"
        actual_acronym = acr_match.group(1)
        assert actual_acronym == expected_acronym, (
            f"Acronym mismatch for '{hero_name}': expected '{expected_acronym}', found '{actual_acronym}'"
        )
