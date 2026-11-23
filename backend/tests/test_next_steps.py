from app.clinical_ai.next_steps import build_next_steps


def test_low_ferritin_suggests_iron_panel():
    out = build_next_steps([{"test_name": "Ferritin", "test_code": "FER", "result_value": "5", "flag": "low"}])
    assert any("TIBC" in t["test"] for t in out["suggested_tests"])
    assert out["advisory_only"] and out["doctor_review_required"] and not out["diagnosis_automation"]


def test_normal_has_no_suggestions():
    out = build_next_steps([{"test_name": "Glucose", "result_value": "5", "flag": "normal"}])
    assert out["suggested_tests"] == [] and out["abnormal"] == []


def test_critical_counted_and_unknown_test_listed():
    out = build_next_steps([
        {"test_name": "Kali", "result_value": "7", "flag": "critical_high"},
        {"test_name": "Xet nghiem la", "result_value": "1", "flag": "high"},
    ])
    assert len(out["critical"]) == 1
    assert "Xet nghiem la" in out["no_rule_for"]
