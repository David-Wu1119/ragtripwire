import json

from ragtripwire.report import print_report, write_json
from ragtripwire.runner import AttackResult


def test_print_report_exit_codes_for_high_medium_and_clean_results():
    clean = [
        AttackResult(
            attack_id="a",
            severity="high",
            title="A",
            query="q",
            response_text="safe",
            passed=True,
        )
    ]
    medium = [
        AttackResult(
            attack_id="b",
            severity="medium",
            title="B",
            query="q",
            response_text="bad",
            triggered_canaries=["x"],
            passed=False,
        )
    ]
    high = [
        AttackResult(
            attack_id="c",
            severity="high",
            title="C",
            query="q",
            response_text="bad",
            triggered_canaries=["x"],
            passed=False,
        )
    ]

    assert print_report(clean) == 0
    assert print_report(medium) == 1
    assert print_report(high) == 2


def test_write_json_redacts_raw_response_and_summarizes(tmp_path):
    report_path = tmp_path / "report.json"
    results = [
        AttackResult(
            attack_id="direct-instruction-override",
            severity="high",
            title="Direct instruction override",
            query="q",
            response_text="x" * 5000,
            triggered_canaries=["x"],
            passed=False,
            raw_response={"secret": "do not serialize"},
        )
    ]

    write_json(results, str(report_path))
    payload = json.loads(report_path.read_text(encoding="utf-8"))

    assert payload["summary"] == {"total": 1, "resisted": 0, "injected": 1, "errored": 0}
    assert payload["results"][0]["raw_response"] is None
    assert len(payload["results"][0]["response_text"]) == 4000
