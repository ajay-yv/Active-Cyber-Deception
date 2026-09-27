from app.repositories.ai_decision_repository import ai_decision_repository
from app.services import gateway
from app.services.gateway import evaluate_request


def test_local_injection_rule_cannot_be_downgraded_by_remote_gateway(monkeypatch) -> None:
    monkeypatch.setattr(
        gateway,
        "_fetch_remote_decision",
        lambda **_: gateway.GatewayDecision(route="real", action="allow", threat_score=5, reason="remote allow"),
    )

    decision = gateway.evaluate_request(
        role="hacker",
        session_id="rule-floor-session",
        device="simulation",
        browser="python-requests",
        operating_system="test",
        ip_address="127.0.0.1",
        country="unknown",
        path="/api/security/simulation/marker",
        body="TEST_SQL_INJECTION UNION SELECT 1",
    )

    assert decision.route == "synthetic"
    assert decision.action == "block"
    assert decision.threat_score >= 90
    assert "sql_injection_pattern" in decision.reason


def test_legitimate_request_routes_to_real():
    decision = evaluate_request(
        role="doctor",
        session_id="session-1",
        device="trusted",
        browser="chrome",
        operating_system="windows",
        ip_address="10.0.0.1",
        country="in",
    )
    assert decision.route == "real"
    assert decision.threat_score < 50


def test_hacker_request_routes_to_synthetic():
    decision = evaluate_request(
        role="hacker",
        session_id="anonymous",
        device="unknown",
        browser="curl",
        operating_system="unknown",
        ip_address="203.0.113.1",
        country="high-risk",
    )
    assert decision.route == "synthetic"
    assert decision.action in {"DECEIVE", "route_synthetic", "monitor", "block"}
    assert decision.threat_score >= 90


def test_decision_persists_ai_record_for_hacker_request() -> None:
    before = len(ai_decision_repository.list_all())
    decision = evaluate_request(
        role="hacker",
        session_id="anonymous",
        device="unknown",
        browser="curl",
        operating_system="unknown",
        ip_address="203.0.113.1",
        country="high-risk",
    )
    after = len(ai_decision_repository.list_all())
    assert decision.ai_label is not None
    assert decision.attack_probability is not None
    assert decision.action != ""
    assert after >= before + 1
