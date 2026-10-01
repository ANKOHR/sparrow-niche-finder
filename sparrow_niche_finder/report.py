"""Deterministic reports with explicit data provenance."""
import json

def banner(result):
    p = result["provenance"]
    kind = "SYNTHETIC fixtures, illustrative data" if p["synthetic"] else "REAL input, declared by the input author (not independently verified)"
    if "sources" in result and not result["sources"]:
        kind = "EMPTY input, no observations supplied"
    return f"Data provenance: {kind}; entered_by={p['entered_by']}; as_of={p['as_of']}; sources=" + ", ".join(result.get("sources", []))

def render(result, format="md"):
    if format == "json":
        return json.dumps({"banner": banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if format != "md":
        raise ValueError("format: expected md or json")
    lines = ["# Sparrow Niche Finder", "", banner(result), "", result["honesty"], "",
             "Rules: " + json.dumps(result["rules"], sort_keys=True), "", "Totals: " + json.dumps(result["totals"], sort_keys=True), "",
             "| Market | Observations | Responses | Rate | Other observations | Other responses | Other rate | Lift | Qualifies |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for m in result["markets"]:
        name = m["market"].replace("&", "&amp;").replace("|", "&#124;").replace("<", "&lt;").replace(">", "&gt;")
        values = [name] + [str(m[k]) if m[k] is not None else "undefined" for k in ("observations", "responses", "response_rate", "other_observations", "other_responses", "other_response_rate", "lift", "qualifies")]
        lines.append("| " + " | ".join(values) + " |")
    lines += ["", "Rates and lifts are exact fractions. Undefined lift means a zero or absent comparator. Qualification is descriptive, not a statistical significance test."]
    return "\n".join(lines) + "\n"
