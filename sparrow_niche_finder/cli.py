"""Local CLI; no network access or model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from .core import SchemaError, analyze
from .fixtures import generate
from .report import render

class InputError(ValueError):
    pass

def read_json(path, comments=False):
    """Read local JSON, preserving source lines and rejecting ambiguous keys."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except UnicodeError:
        raise InputError(f"ParseError: {path}: line 1: expected UTF-8") from None
    cleaned = "\n".join("" if comments and line.lstrip().startswith("#") else line
                        for line in raw.splitlines())
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON field {key!r}")
            value[key] = item
        return value
    try:
        value = json.loads(cleaned, object_pairs_hook=unique_object)
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from None
    except ValueError as exc:
        raise InputError(f"ParseError: {path}: line 1 (document): {exc}") from None
    return value, raw

def load_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}; use snf fixtures --out demo or supply an input directory")
    path = directory / "observations.json"
    if not path.exists():
        if any(directory.iterdir()):
            raise InputError(f"MissingInput: {path}; input requires observations.json")
        return {"synthetic": False, "entered_by": "no data supplied", "as_of": "2026-09-30", "records": []}, []
    data, raw = read_json(path, comments=True)
    try:
        from .core import validate
        validate(data)
    except SchemaError as exc:
        raise InputError(f"SchemaError: {path}: line 1 (field path below): {exc}") from None
    return data, [{"file": path.name, "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()}]

def compute(directory):
    data, sources = load_input(directory)
    result = analyze(data)
    result["sources"] = [s["file"] + " sha256=" + s["sha256"] for s in sources]
    return result

def atomic_write(path, content):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError(f"WriteError: {path}: {exc.strerror or type(exc).__name__}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def parser():
    p = argparse.ArgumentParser(description="Compare observed market responses from local inputs. No forecasts or savings estimates.")
    subs = p.add_subparsers(dest="command", required=True)
    f = subs.add_parser("fixtures", help="Generate 200 labelled synthetic observations", epilog="Example: snf fixtures --out demo")
    f.add_argument("--out", required=True)
    r = subs.add_parser("run", help="Compute and save observed comparisons", epilog="Example: snf run --input demo")
    r.add_argument("--input", required=True)
    r.add_argument("--state", default=".snf/results.json")
    rep = subs.add_parser("report", help="Render saved results and provenance", epilog="Example: snf report --format md")
    rep.add_argument("--format", choices=("md", "json"), default="md")
    rep.add_argument("--state", default=".snf/results.json")
    rep.add_argument("--out")
    for command, help_text, example in (("compare", "Compare each market with all remaining observations", "snf compare --input demo"), ("niches", "Show only markets satisfying the explicit qualification rule", "snf niches --input demo")):
        sub = subs.add_parser(command, help=help_text, description=help_text, epilog="Example: " + example)
        sub.add_argument("--input", required=True)
        sub.add_argument("--format", choices=("md", "json"), default="md")
    return p

def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("SYNTHETIC illustrative fixture: 200 observations generated; no real market evidence.")
        elif args.command == "run":
            result = compute(args.input)
            Path(args.state).parent.mkdir(parents=True, exist_ok=True)
            atomic_write(args.state, json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
            print(render(result, "md"), end="")
        elif args.command == "report":
            try:
                result, _ = read_json(args.state)
            except FileNotFoundError:
                raise InputError(f"MissingInput: {args.state}; run snf run --input <dir> first") from None
            try:
                output = render(result, args.format)
            except (KeyError, TypeError, AttributeError) as exc:
                raise InputError(f"SchemaError: {args.state}: line 1: invalid result field {exc}; rerun snf run --input <dir>") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        else:
            result = compute(args.input)
            if args.command == "niches":
                result["markets"] = [m for m in result["markets"] if m["qualifies"]]
            print(render(result, args.format), end="")
        return 0
    except (InputError, SchemaError, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        message = str(exc).replace(chr(0x2014), "-")
        print(f"snf error: {message}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
