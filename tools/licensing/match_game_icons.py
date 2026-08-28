#!/usr/bin/env python3
"""Audit local PNG assets against the official Game Icons SVG corpus.

The tool is intentionally conservative. It only reports CONFIRMED or
HIGH_CONFIDENCE when image evidence supports the mapping; filename similarity
alone never creates an attribution.

The official corpus is game-icons/icons. For reproducible audits, prefer a
pinned corpus checkout/archive rather than a moving website result.

Requirements for the image-matching path:
    Pillow
    CairoSVG

Example:
    python tools/licensing/match_game_icons.py \
        --assets ui/assets \
        --corpus /path/to/game-icons-icons \
        --output tools/licensing/game_icons_manifest.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageChops, ImageStat
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("Pillow is required: python -m pip install pillow") from exc

try:
    import cairosvg
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("CairoSVG is required: python -m pip install cairosvg") from exc

CORPUS_REPOSITORY = "https://github.com/game-icons/icons"
CORPUS_LICENSE_URL = "https://github.com/game-icons/icons/blob/master/license.txt"
CORPUS_LICENSE = "CC BY 3.0"
DEFAULT_SIZE = 64
SUPPORTED_ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}

STATUS_ORDER = ("CONFIRMED", "HIGH CONFIDENCE", "AMBIGUOUS", "UNRESOLVED")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_name(path: str) -> str:
    value = Path(path).stem.lower().replace("_", "-").replace(" ", "-")
    return re.sub(r"[^a-z0-9-]+", "-", value).strip("-")


def git_revision(path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _rgba_on_black(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
    return Image.alpha_composite(background, rgba).convert("L")


def _rgba_on_white(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, rgba).convert("L")


def _foreground_mask(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    extrema = alpha.getextrema()
    if extrema != (255, 255):
        return alpha
    grey = rgba.convert("L")
    return grey.point(lambda value: 255 if value < 245 else 0)


def normalize_image(image: Image.Image, size: int = DEFAULT_SIZE) -> Image.Image:
    """Normalize canvas while preserving foreground geometry.

    We compare several color/background interpretations because the local PNGs
    are transformed exports from Game Icons Studio rather than source SVGs.
    """
    mask = _foreground_mask(image)
    bbox = mask.getbbox()
    if bbox is None:
        normalized = image.convert("L")
    else:
        cropped = image.crop(bbox)
        normalized = cropped.convert("L")
    normalized.thumbnail((size - 8, size - 8), Image.Resampling.LANCZOS)
    canvas = Image.new("L", (size, size), 0)
    offset = ((size - normalized.width) // 2, (size - normalized.height) // 2)
    canvas.paste(normalized, offset)
    return canvas


def normalized_variants(image: Image.Image, size: int = DEFAULT_SIZE) -> tuple[Image.Image, ...]:
    return (
        normalize_image(_rgba_on_black(image), size),
        normalize_image(_rgba_on_white(image), size),
        normalize_image(image, size),
    )


def rasterize_svg(svg_path: Path, size: int = DEFAULT_SIZE) -> Image.Image:
    png = cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
    from io import BytesIO

    return Image.open(BytesIO(png)).convert("RGBA")


def similarity(a: Image.Image, b: Image.Image) -> float:
    """Return a bounded visual similarity score in [0, 1]."""
    a_l = a.convert("L")
    b_l = b.convert("L")
    diff = ImageChops.difference(a_l, b_l)
    mean_abs = ImageStat.Stat(diff).mean[0]
    mse = sum((x - y) ** 2 for x, y in zip(a_l.getdata(), b_l.getdata())) / (a_l.width * a_l.height)
    # Combine geometry-sensitive absolute difference and MSE.
    abs_score = 1.0 - min(1.0, mean_abs / 255.0)
    mse_score = 1.0 - min(1.0, math.sqrt(mse) / 255.0)
    return 0.6 * abs_score + 0.4 * mse_score


def iter_svg_candidates(corpus: Path) -> Iterable[Path]:
    yield from sorted(corpus.rglob("*.svg"))


def classify(best: float, second: float | None) -> str:
    if best >= 0.995:
        return "CONFIRMED"
    if best >= 0.97 and (second is None or best - second >= 0.01):
        return "HIGH CONFIDENCE"
    if best >= 0.90 and (second is None or best - second >= 0.002):
        return "AMBIGUOUS"
    return "UNRESOLVED"


def audit_asset(asset: Path, corpus: Path, *, size: int) -> dict[str, object]:
    local = Image.open(asset).convert("RGBA")
    local_variants = normalized_variants(local, size)
    ranked: list[tuple[float, Path]] = []

    for source in iter_svg_candidates(corpus):
        try:
            source_image = rasterize_svg(source, size)
            source_variants = normalized_variants(source_image, size)
            score = max(
                similarity(local_variant, source_variant)
                for local_variant in local_variants
                for source_variant in source_variants
            )
        except Exception:
            continue
        ranked.append((score, source))

    ranked.sort(key=lambda item: (-item[0], str(item[1])))
    best = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    best_score = float(best[0]) if best else 0.0
    second_score = float(second[0]) if second else None
    status = classify(best_score, second_score)

    match: dict[str, object] | None = None
    if best is not None:
        rel = best[1].relative_to(corpus).as_posix()
        parts = rel.split("/")
        author = parts[0] if len(parts) >= 2 else None
        icon_name = Path(parts[-1]).stem
        match = {
            "status": status,
            "confidence": round(best_score, 6),
            "second_best_confidence": None if second_score is None else round(second_score, 6),
            "icon_path": rel,
            "icon_name": icon_name,
            "author": author,
            "license": CORPUS_LICENSE,
            "source_url": f"https://game-icons.net/1x1/{author}/{icon_name}.html" if author else None,
            "comparison": {
                "method": "rasterized-svg-vs-local-png-normalized-canvas",
                "raster_size": size,
                "variants": "black/white/composited normalization",
            },
        }
    return {
        "local_file": asset.as_posix(),
        "local_sha256": sha256_file(asset),
        "filename_stem": normalize_name(asset.name),
        "match": match,
    }


def build_manifest(assets: Path, corpus: Path, *, size: int) -> dict[str, object]:
    asset_files = [p for p in sorted(assets.rglob("*")) if p.suffix.lower() in SUPPORTED_ASSET_SUFFIXES]
    corpus_revision = git_revision(corpus)
    results = [audit_asset(asset, corpus, size=size) for asset in asset_files]

    counts = {status: 0 for status in STATUS_ORDER}
    for result in results:
        match = result.get("match")
        status = match.get("status") if isinstance(match, dict) else "UNRESOLVED"
        counts[str(status)] = counts.get(str(status), 0) + 1

    return {
        "schema_version": "redwar-game-icons-provenance-v1",
        "source_of_truth": {
            "repository": CORPUS_REPOSITORY,
            "license_url": CORPUS_LICENSE_URL,
            "license": CORPUS_LICENSE,
            "corpus_revision": corpus_revision,
        },
        "rendering_convention": {
            "size": "256x256",
            "background": "black",
            "shape": "svgsquare",
            "type": "gradient",
            "gradient": "plain",
            "icon_color": "black",
            "frame": "reset/back-to-zero/reset-background",
        },
        "summary": {
            "assets_audited": len(results),
            **{key.lower().replace(" ", "_"): value for key, value in counts.items()},
        },
        "assets": results,
        "policy": {
            "filename_only_match_is_not_attribution": True,
            "low_confidence_matches_require_manual_review": True,
            "unresolved_assets_must_not_receive_invented_authorship": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit RedWar PNGs against the official Game Icons SVG corpus")
    parser.add_argument("--assets", type=Path, default=Path("ui/assets"))
    parser.add_argument("--corpus", type=Path, required=True, help="Pinned checkout of https://github.com/game-icons/icons")
    parser.add_argument("--output", type=Path, default=Path("tools/licensing/game_icons_manifest.json"))
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE)
    args = parser.parse_args()

    if not args.assets.is_dir():
        raise SystemExit(f"assets directory does not exist: {args.assets}")
    if not args.corpus.is_dir():
        raise SystemExit(f"corpus directory does not exist: {args.corpus}")

    manifest = build_manifest(args.assets, args.corpus, size=args.size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
