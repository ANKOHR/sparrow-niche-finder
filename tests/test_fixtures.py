import json
from sparrow_niche_finder.fixtures import generate

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.iterdir():
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# SYNTHETIC")
        assert json.loads("\n".join(text.splitlines()[1:]))["synthetic"] is True
