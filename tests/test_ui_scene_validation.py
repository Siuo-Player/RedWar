from pathlib import Path

from tools.ui_scene_validation import capture, SCENES


def test_registered_scenes_capture_to_png(tmp_path: Path):
    for scene in SCENES:
        path = capture(scene, tmp_path)
        assert path.exists()
        assert path.suffix == ".png"
        assert path.stat().st_size > 100
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
