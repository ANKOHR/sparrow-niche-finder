# Local acceptance evidence

Measured on 2026-10-01 using Python 3.12 on this Windows CPU environment.

- `python -m pytest -q`: 28 passed, 0.29 seconds in the final test run.
- Installed CLI demo: `snf fixtures --out demo`, `snf run --input demo`, `snf report --format md` completed in 0.748974 seconds total, including three process startups. Below the five-second acceptance limit.
- Synthetic truth: 200 observations, 35 responses, four markets, Alpha alone qualifies. All market and comparator counts, exact rates, lifts, and totals match independent arithmetic. Zero false positives on this planted fixture.
- The separate five-record example ran through the installed CLI and returned five observations. It is illustrative synthetic data.
- Repeated run snapshots and JSON reports are byte-identical in the test suite. Corrupting Alpha responses changes the computed result and removes qualification.
- Empty inputs, missing files, malformed JSON, schema drift, duplicate identifiers and JSON keys, invalid UTF-8, future dates relative to as_of, unsupported negative values, long Unicode and Windows path strings, and atomic report write failure are covered.

These are local build measurements, not evidence of real market demand, time saved, revenue, or commercial readiness. Runtime is environment-specific. No real-use trial has been performed. The two-week verdict is pending that evidence window, as recorded in VERDICT.md. No publishing was performed.
