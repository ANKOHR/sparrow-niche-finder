"""Labelled synthetic data, constructed without randomness (no seed needed)."""
import json
from pathlib import Path

HEADER = "# SYNTHETIC fixture, illustrative observations, not real market evidence\n"

def fixture_data():
    records = []
    for market, responses in (("Alpha", 20), ("Beta", 5), ("Gamma", 5), ("Delta", 5)):
        for i in range(50):
            records.append({"id": f"{market}-{i:03}", "market": market, "date": "2026-09-01", "responded": i < responses})
    return {"synthetic": True, "as_of": "2026-09-30", "entered_by": "synthetic generator", "records": records}

def expectations():
    # Independent hand arithmetic: 20+5+5+5=35; Alpha 20/50 vs 15/150.
    return {"synthetic": True, "totals": {"observations": 200, "responses": 35, "markets": 4, "qualifying_markets": 1},
            "qualifying_markets": ["Alpha"], "rates": {"Alpha": "2/5", "Beta": "1/10", "Gamma": "1/10", "Delta": "1/10"},
            "other_rates": {"Alpha": "1/10", "Beta": "1/5", "Gamma": "1/5", "Delta": "1/5"},
            "lifts": {"Alpha": "4/1", "Beta": "1/2", "Gamma": "1/2", "Delta": "1/2"}}

def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, value in (("observations.json", fixture_data()), ("expectations.json", expectations())):
        target = out / name
        if target.exists():
            raise FileExistsError(f"refusing to overwrite {target}")
    for name, value in (("observations.json", fixture_data()), ("expectations.json", expectations())):
        (out / name).write_text(HEADER + json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
