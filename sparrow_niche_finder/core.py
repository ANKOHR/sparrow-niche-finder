"""Pure comparisons. Hypothetical savings are deliberately never calculated."""
from collections import defaultdict
from datetime import date
from fractions import Fraction

class SchemaError(ValueError):
    """Input violates the documented observation schema."""

def validate(data):
    if not isinstance(data, dict):
        raise SchemaError("root: expected object")
    required = {"synthetic", "as_of", "entered_by", "records"}
    if set(data) != required:
        raise SchemaError("root fields: missing=" + ",".join(sorted(required - set(data))) + "; unexpected=" + ",".join(sorted(set(data) - required)))
    if type(data["synthetic"]) is not bool:
        raise SchemaError("synthetic: expected boolean")
    def day(value, field):
        try:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError()
            return parsed
        except (ValueError, TypeError):
            raise SchemaError(field + ": expected YYYY-MM-DD") from None
    cutoff = day(data["as_of"], "as_of")
    def label(value, field):
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            raise SchemaError(field + ": expected nonblank string, maximum 4096 characters")
        if any(ord(c) < 32 or c == chr(0x2014) for c in value):
            raise SchemaError(field + ": control characters and em dash characters are forbidden")
    label(data["entered_by"], "entered_by")
    if not isinstance(data["records"], list):
        raise SchemaError("records: expected list")
    seen = set()
    for index, row in enumerate(data["records"]):
        prefix = f"records[{index}]"
        if not isinstance(row, dict) or set(row) != {"id", "market", "date", "responded"}:
            raise SchemaError(prefix + ": expected fields id, market, date, responded; offending fields=" + (",".join(sorted(set(row) ^ {"id", "market", "date", "responded"})) if isinstance(row, dict) else "row"))
        for field in ("id", "market"):
            label(row[field], prefix + "." + field)
        if row["id"] in seen:
            raise SchemaError(prefix + ".id: duplicate id " + row["id"])
        seen.add(row["id"])
        if day(row["date"], prefix + ".date") > cutoff:
            raise SchemaError(prefix + ".date: future date relative to as_of")
        if type(row["responded"]) is not bool:
            raise SchemaError(prefix + ".responded: expected boolean")
    return data

def ratio(numerator, denominator):
    if not denominator:
        return None
    value = Fraction(numerator, denominator)
    return f"{value.numerator}/{value.denominator}"

def analyze(data, min_observations=10, min_responses=5, min_lift=Fraction(2)):
    validate(data)
    if type(min_observations) is not int or min_observations < 1:
        raise SchemaError("min_observations: expected positive integer")
    if type(min_responses) is not int or min_responses < 1:
        raise SchemaError("min_responses: expected positive integer")
    if min_lift < 1:
        raise SchemaError("min_lift: must be at least 1")
    groups = defaultdict(lambda: [0, 0])
    for row in data["records"]:
        groups[row["market"]][0] += 1
        groups[row["market"]][1] += int(row["responded"])
    observations = len(data["records"])
    responses = sum(count[1] for count in groups.values())
    markets = []
    for market, (n, r) in sorted(groups.items()):
        other_n, other_r = observations - n, responses - r
        rate = Fraction(r, n)
        baseline = Fraction(other_r, other_n) if other_n else None
        lift = rate / baseline if baseline else None
        # A zero-response comparator can qualify by exact cross multiplication.
        qualifies = n >= min_observations and r >= min_responses and other_n > 0 and rate > baseline and rate >= min_lift * baseline
        markets.append({"market": market, "observations": n, "responses": r,
                        "response_rate": ratio(r, n), "other_observations": other_n,
                        "other_responses": other_r, "other_response_rate": ratio(other_r, other_n),
                        "lift": ratio(lift.numerator, lift.denominator) if lift is not None else None,
                        "qualifies": qualifies})
    return {"provenance": {"synthetic": data["synthetic"], "entered_by": data["entered_by"], "as_of": data["as_of"]},
            "rules": {"min_observations": min_observations, "min_responses": min_responses,
                      "min_lift": ratio(min_lift.numerator, min_lift.denominator)},
            "totals": {"observations": observations, "responses": responses, "markets": len(markets),
                       "qualifying_markets": sum(m["qualifies"] for m in markets)},
            "markets": markets, "honesty": "Observed input counts only. No predictions. Time or money saved is unmeasured; hypothetical savings are not calculated."}
