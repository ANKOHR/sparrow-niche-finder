import json
from sparrow_niche_finder.core import analyze
from sparrow_niche_finder.fixtures import fixture_data, expectations
from sparrow_niche_finder.report import render

def test_report_matches_ground_truth_exact():
    result = json.loads(render(analyze(fixture_data()), "json"))
    assert result["totals"] == expectations()["totals"]
    assert sum(m["responses"] for m in result["markets"]) == result["totals"]["responses"]
    expected = expectations()
    for row in result["markets"]:
        market = row["market"]
        assert row["observations"] == 50
        assert row["responses"] == (20 if market == "Alpha" else 5)
        assert row["other_observations"] == 150
        assert row["other_responses"] == (15 if market == "Alpha" else 30)
        assert row["response_rate"] == expected["rates"][market]
        assert row["other_response_rate"] == expected["other_rates"][market]
        assert row["lift"] == expected["lifts"][market]

def test_report_zero_false_positives():
    result = json.loads(render(analyze(fixture_data()), "json"))
    assert [m["market"] for m in result["markets"] if m["qualifies"]] == ["Alpha"]

def test_report_carries_provenance_banner():
    for format in ("md", "json"):
        assert "SYNTHETIC fixtures" in render(analyze(fixture_data()), format)
    data = fixture_data()
    data["synthetic"] = False
    data["entered_by"] = "Henry"
    assert "REAL input" in render(analyze(data))
    assert "Henry" in render(analyze(data))

def test_hypothetical_figures_labelled():
    for format in ("md", "json"):
        output = render(analyze(fixture_data()), format)
        assert "unmeasured" in output and "hypothetical savings are not calculated" in output

def test_no_em_dashes_in_outputs():
    for format in ("md", "json"):
        assert chr(0x2014) not in render(analyze(fixture_data()), format)
