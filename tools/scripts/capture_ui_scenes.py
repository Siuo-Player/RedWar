from __future__ import annotations

import argparse
from pathlib import Path

from tools.ui_scene_validation import SCENES, capture_all, capture


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture deterministic RedWar battle UI scenes")
    parser.add_argument("--output", default="artifacts/ui-scenes", help="PNG output directory")
    parser.add_argument("--scene", choices=SCENES, help="Capture one scene instead of all scenes")
    args = parser.parse_args()

    if args.scene:
        paths = [capture(args.scene, Path(args.output))]
    else:
        paths = capture_all(Path(args.output))

    for path in paths:
        print(f"captured: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
