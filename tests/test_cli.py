import json

import pytest

import pre_execution_validator as pev


def test_public_api_is_still_false(capsys):
    assert pev.check_if_script_ran_before_it_ran() is False
    assert "NO_PRIOR_EXECUTION_DETECTED" in capsys.readouterr().out


def test_cli_plain_text_when_not_a_terminal(capsys, monkeypatch):
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert pev.main(["--quiet"]) == 0
    out = capsys.readouterr().out
    assert "Final Answer: False" in out
    assert "\033[" not in out


def test_no_color_beats_force_color(capsys, monkeypatch):
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("NO_COLOR", "1")
    pev.main(["--quiet"])
    assert "\033[" not in capsys.readouterr().out


def test_force_color_colors_the_answer(capsys, monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    pev.main(["--quiet"])
    assert "\033[1;31mFalse\033[0m" in capsys.readouterr().out


def test_json_report(capsys):
    assert pev.main(["--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["prior_execution_detected"] is False
    assert data["result"] == "NO_PRIOR_EXECUTION_DETECTED"
    assert data["confidence"] == 1.0
    assert len(data["reasoning_chain"]) == 5


def test_version(capsys):
    with pytest.raises(SystemExit) as e:
        pev.main(["--version"])
    assert e.value.code == 0
    assert pev.FRAMEWORK_VERSION in capsys.readouterr().out
