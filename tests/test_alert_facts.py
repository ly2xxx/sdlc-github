import json

import alert_facts as a

DATA = {"version": 1, "source": "dependabot", "read_at": "2026-11-16 21:52 UTC", "open": 120,
        "history": [{"read_at": "x", "open": 94}, {"read_at": "y", "open": 120}],
        "packages": [
            {"package": "torch", "current": "2.1.0", "fix_to": "2.13.0", "severity": "critical",
             "no_fix": [], "alerts": [{"id": f"CVE-{i}"} for i in range(12)]},
            {"package": "pandasai", "current": "0.2.15", "fix_to": "0.8.1", "severity": "critical",
             "no_fix": ["CVE-2024-12366"], "alerts": [{"id": "a"}, {"id": "b"}]}]}


def body(data):
    return "<!-- dependabot-monitor -->\n# x\n\n<details>\n\n```json\n" + json.dumps(data) + "\n```\n"


def test_facts_lines_name_each_package_target_count_and_worst(tmp_path, capsys):
    p = tmp_path / "issue.md"
    p.write_text(body(DATA))
    assert a.main([str(p), "--issue", "4"]) == 0
    out = capsys.readouterr().out
    flat = " ".join(out.split())
    assert flat.startswith("- Open alerts (issue #4, read 2026-11-16 21:52 UTC), 120 in 2 packages")
    assert "torch 2.1.0 → 2.13.0 (12, critical)" in flat
    assert "pandasai 0.2.15 → 0.8.1 (2, critical; no fix for CVE-2024-12366)" in flat
    assert "- History: 94 → 120 open alerts." in out
    assert all(len(line) <= 88 for line in out.splitlines())


def test_no_alerts_trivy_and_truncated_reports_say_so():
    text = a.facts({"open": 0, "packages": [], "read_at": "t", "source": "trivy", "truncated": True})
    flat = " ".join(text.split())
    assert "0 in 0 packages: none." in flat and "Trivy" in flat and "cut down" in flat


def test_a_body_without_data_fails(tmp_path):
    p = tmp_path / "issue.md"
    p.write_text("no data here")
    assert a.main([str(p)]) == 1
