# Sparrow Niche Finder

Sparrow Niche Finder (`snf`) discovers markets with disproportionately high **observed** response rates in explicit local inputs. It cannot discover markets outside those inputs, predict demand, or infer causation. This is a sellable response audit building block for Sparrow and small business owners.

## Quickstart

Python 3.10 or newer. No runtime dependencies, network calls, model calls, GPU workloads, or random generation.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
snf fixtures --out demo
snf run --input demo
snf report --format md
python -m pytest -q
```

Pytest must already be installed to run tests. The equivalent entry point is `python -m sparrow_niche_finder.cli`. Run commands from the same working directory or use `--state` to select the saved result explicitly.

If Windows installs `snf.exe` into a Scripts directory outside PATH, add that directory to your user PATH or use the module entry point above. Installation needs only locally available setuptools; set `PIP_NO_INDEX=1` and `PIP_DISABLE_PIP_VERSION_CHECK=1` to enforce offline pip operation.

The smallest runnable version is included in `examples/tiny/observations.json`: five hand-written synthetic observations, two responses, rates A=1/2 and B=1/3, and no qualifying markets under the default minimum sample rule. Run `snf run --input examples/tiny` followed by `snf report --format md`.

## Input format

Supply a directory containing `observations.json`. JSON is the supported observation format, not CSV or YAML. Blank lines and whole-line `#` comments are allowed. An empty directory yields a zero report. A nonempty directory without observations.json is an error. Other files are not observations; fixture expectations are never loaded by the engine.

```json
{
  "synthetic": false,
  "as_of": "2026-09-30",
  "entered_by": "Henry",
  "records": [
    {"id": "contact-1", "market": "Independent shops", "date": "2026-09-01", "responded": true}
  ]
}
```

This schema example is illustrative, not evidence of a real contact. Set `synthetic: true` for invented observations. Set false only for real observations entered by the named author. Real provenance is an author declaration, not independently verified. Henry's real trial data must be entered by him and retained locally, never shipped with this project.

All four top-level fields and all four observation fields are required; unknown fields fail validation. `id` is unique across the input. `id`, `market`, and `entered_by` are nonblank Unicode strings of at most 4096 characters. Strings retain exact spelling, whitespace, and case; inconsistent market names create separate groups. Controls and em dash characters are rejected. Dates use YYYY-MM-DD and observation dates must be no later than the explicit `as_of` cutoff. This reproducible cutoff defines future dates; it is not the machine clock. `responded` must be a JSON boolean, never a count or negative number. Amounts, savings, and any additional fields are unsupported and rejected. Nothing invalid is silently dropped.

Record one observation per eligible contact or experiment using a consistent response definition and observation window. Repeated people with distinct IDs can bias results; the tool cannot detect this. Nonresponders must be included. No denominator is invented.

## Rules and computed figures

Each market is compared against **all other observations combined**, excluding itself. The default descriptive rule requires at least 10 observations, at least 5 responses, a rate strictly above the comparator, and a rate at least twice the comparator. These thresholds are design choices, not measured optimal thresholds. They are reported in every report. Pure `analyze` also accepts explicit thresholds.

Counts are integers; rates and lift use reduced exact fractions, never rounded floating point values. Lift is market rate divided by comparator rate. If the comparator has no responses, lift is undefined; a positive market can still qualify through exact cross multiplication. With no comparator observations a market cannot qualify. Empty inputs produce zero totals. A single observation has equal weight in every group.

No significance, uncertainty, causal, or population claim is made. Selection bias, small samples, different channels, different response windows, and missing nonresponders can all distort a comparison. A flagged niche warrants manual review and a prospective experiment, not a promise of future performance.

## Subcommands

- `snf fixtures --out demo`: create 200 labelled synthetic observations and independent hand-computed expectations. Refuses to overwrite fixture files.
- `snf run --input demo --state .snf/results.json`: validate, compute, and save deterministic results atomically; also print the full report.
- `snf report --format md`: render the last saved result with provenance. Use `--format json`, `--state <path>`, or `--out report.md` for a local file.
- `snf compare --input demo --format json`: compute all market comparisons directly without saved state.
- `snf niches --input demo`: compute and display qualifying markets only. Totals still describe the complete input.

Each subcommand includes `--help` and an example. Reports read a snapshot; rerun after changing inputs. Source filenames and SHA-256 hashes identify the inputs used. Saved state is local computed output and should not be edited by hand.

## Architecture

```text
observations.json -> CLI parse and schema validation -> pure core.analyze
                                                        |
                                                        v
                                                .snf/results.json
                                                        |
                                                        v
                                                report.render -> MD / JSON
fixtures.generate -> observations.json + expectations.json (tests only)
```

Core performs no I/O. CLI handles input, named errors and atomic output writes. Fixtures use fixed explicit construction, no randomness and no seed. Sorting and exact arithmetic keep outputs byte-identical for identical input. Directory location is excluded from reports; the source filename and content hash remain explicit.

## Honesty boundary and fixture policy

Every generated fixture file contains a SYNTHETIC header comment and `synthetic: true`. Every synthetic report and fixture command output labels synthetic data as illustrative. Reports distinguish real declared input, synthetic input, and empty input. Time and money saved are unmeasured; hypothetical savings are explicitly not calculated. The tool has no savings estimator. No real-use evidence ships in this build.

The fixture has four markets, 50 observations each. Alpha has 20 responses, and Beta, Gamma, Delta have five each. Total: 200 observations, 35 responses. Alpha rate is 2/5 versus 1/10 for the remaining 150 observations, lift 4/1. Other markets have rate 1/10 versus 1/5, lift 1/2. Only Alpha qualifies. `expectations.json` records independent arithmetic rather than calling the engine. Tests also cover a hand-written five-record example, corrupted observations, Unicode, Windows path strings, and boundary failures.

## Failure modes

Malformed JSON produces ParseError with filename and exact line. Duplicate JSON fields and invalid UTF-8 are rejected with a document-level line 1 location. SchemaError names the filename and field path; its line 1 location identifies the document, while the indexed field path identifies the record. MissingInput provides a usage hint and nonzero exit. Report WriteError names the target and removes temporary files; existing files are replaced only after a complete write. Unsupported encodings, filesystem failures and corrupted state return nonzero errors without tracebacks. CLI validation errors exit 2. Reports cannot verify that author-labelled real data is authentic.

## Evidence and two-week improvement hook

See EVIDENCE.md for local acceptance evidence and LESSONS.md for domain lessons. The hypothesis tested here is that deterministic local response comparisons reproduce planted ground truth; this does not validate commercial demand.

Start a two-week trial only when Henry supplies real data. Keep trial observations and results outside version control. Record run count, date, number of hand-checked market rows and discrepancies. The primary metric is discrepant rows divided by hand-checked rows, including every count, rate and qualification. Zero checked rows means unmeasured, not zero error. At day 14, if error exceeds 10 percent, fix the largest documented cause and repeat the check, or kill with a recorded reason. If the tool is unused, record that fact and kill it.

## Verdict

Pending the two-week real-use evidence window. No commercial or daily-use verdict is invented at build time. At day 14 record one explicit verdict and reason in VERDICT.md: expand for daily use or revenue, integrate for heavy sibling overlap, commercialise if a buyer would pay as-is, maintain for portfolio evidence otherwise, kill if unused or acceptance criteria cannot be met. See VERDICT.md for the evidence checklist.
