import copy
import pytest
from sparrow_niche_finder.core import analyze, SchemaError
from sparrow_niche_finder.fixtures import fixture_data, expectations

def test_fixture_ground_truth_matches_hand_computed():
    result = analyze(fixture_data())
    expected = expectations()
    assert result["totals"] == expected["totals"]
    for row in result["markets"]:
        assert row["response_rate"] == expected["rates"][row["market"]]
        assert row["other_response_rate"] == expected["other_rates"][row["market"]]
        assert row["lift"] == expected["lifts"][row["market"]]
        assert row["observations"] == 50
        assert row["responses"] == (20 if row["market"] == "Alpha" else 5)
        assert row["other_observations"] == 150
        assert row["other_responses"] == (15 if row["market"] == "Alpha" else 30)

@pytest.mark.parametrize("mutation", ["negative", "future", "long", "duplicate", "amount", "dash", "control"])
def test_rejects_adversarial_values(mutation):
    data = fixture_data()
    row = data["records"][0]
    if mutation == "negative": row["responded"] = -1
    if mutation == "future": row["date"] = "2026-10-01"
    if mutation == "long": row["market"] = "x" * 4097
    if mutation == "duplicate": data["records"][1]["id"] = row["id"]
    if mutation == "amount": row["amount"] = -20
    if mutation == "dash": row["market"] = chr(0x2014)
    if mutation == "control": row["market"] = "a\nb"
    with pytest.raises(SchemaError): analyze(data)

def test_corrupted_ground_truth_changes_computation():
    data = fixture_data()
    for row in data["records"][:20]: row["responded"] = False
    result = analyze(data)
    assert result["totals"]["responses"] == 15
    assert result["totals"]["qualifying_markets"] == 0

def test_handles_unicode_and_long_inputs():
    data = fixture_data()
    value = "東京 café C:\\Users\\henry " + "z" * 3000
    for row in data["records"][:50]: row["market"] = value
    assert any(m["market"] == value for m in analyze(data)["markets"])

def test_zero_baseline_and_single_market():
    data = fixture_data()
    for row in data["records"][50:]: row["responded"] = False
    alpha = analyze(data)["markets"][0]
    assert alpha["qualifies"] and alpha["lift"] is None
    data["records"] = data["records"][:50]
    assert not analyze(data)["markets"][0]["qualifies"]

def test_tiny_hand_written_input():
    data = {"synthetic": True, "as_of": "2026-09-30", "entered_by": "hand-written synthetic example", "records": [
        {"id": "1", "market": "A", "date": "2026-09-01", "responded": True},
        {"id": "2", "market": "A", "date": "2026-09-01", "responded": False},
        {"id": "3", "market": "B", "date": "2026-09-01", "responded": True},
        {"id": "4", "market": "B", "date": "2026-09-01", "responded": False},
        {"id": "5", "market": "B", "date": "2026-09-01", "responded": False}]}
    result = analyze(data)
    assert result["totals"] == {"observations": 5, "responses": 2, "markets": 2, "qualifying_markets": 0}
    assert [m["response_rate"] for m in result["markets"]] == ["1/2", "1/3"]
