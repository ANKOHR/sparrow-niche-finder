import json
import time
from pathlib import Path
from sparrow_niche_finder.cli import main
from sparrow_niche_finder.fixtures import generate

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    start = time.perf_counter()
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "SYNTHETIC" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report", "--format", "json"]) == 0
    assert '"observations": 0' in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "observations.json").write_text('{\n"records": bad}', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "observations.json" in error and "line 2" in error
    assert "Traceback" not in error

def test_determinism_byte_identical(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    assert main(["run", "--input", "demo"]) == 0
    first = Path(".snf/results.json").read_bytes()
    assert main(["run", "--input", "demo"]) == 0
    assert Path(".snf/results.json").read_bytes() == first
    capsys.readouterr()
    main(["report", "--format", "json"])
    a = capsys.readouterr().out
    main(["report", "--format", "json"])
    assert capsys.readouterr().out == a

def test_cli_smoke_all_subcommands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["fixtures", "--out", "demo"]) == 0
    for command in ("run", "compare", "niches"):
        assert main([command, "--input", "demo"]) == 0
    for format in ("json", "md"):
        assert main(["report", "--format", format]) == 0
    import pytest
    for command in ("fixtures", "run", "report", "compare", "niches"):
        with pytest.raises(SystemExit) as exc: main([command, "--help"])
        assert exc.value.code == 0

def test_missing_input_and_schema_drift(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err
    generate(tmp_path)
    path = tmp_path / "observations.json"
    data = json.loads("\n".join(path.read_text().splitlines()[1:]))
    data["records"][0]["responded"] = -1
    path.write_text(json.dumps(data), encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "records[0].responded" in capsys.readouterr().err

def test_report_write_failure_is_atomic(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    generate(tmp_path / "demo")
    main(["run", "--input", "demo"])
    (tmp_path / "target").mkdir()
    assert main(["report", "--out", "target"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == [".snf", "demo", "target"]

def test_corrupt_state_has_named_file_and_line(tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text('{\n bad}', encoding="utf-8")
    assert main(["report", "--state", str(state)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "state.json" in error and "line 2" in error
    state.write_text('{}', encoding="utf-8")
    assert main(["report", "--state", str(state)]) == 2
    assert "SchemaError" in capsys.readouterr().err

def test_duplicate_json_fields_rejected(tmp_path, capsys):
    (tmp_path / "observations.json").write_text('{"synthetic": true, "synthetic": false}', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "duplicate JSON field" in error

def test_invalid_utf8_named_error(tmp_path, capsys):
    (tmp_path / "observations.json").write_bytes(bytes([255]))
    assert main(["run", "--input", str(tmp_path)]) == 2
    assert "ParseError" in capsys.readouterr().err
