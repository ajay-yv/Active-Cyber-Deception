from dataclasses import dataclass
from uuid import uuid4

from app.db.engines import SecuritySessionLocal
from app.models.security import AIDecision


@dataclass(frozen=True)
class AIDecisionRecord:
    id: str
    session_id: str
    route: str
    action: str
    score: int
    reason: str
    anomaly_score: float
    anomaly_flag: int
    random_forest_label: str
    random_forest_confidence: float
    attack_probability: float
    xgboost_confidence: float
    risk_score: float
    attacker_ip: str | None = None
    user_agent: str | None = None


class AIDecisionRepository:
    def add(self, record: AIDecisionRecord) -> AIDecisionRecord:
        with SecuritySessionLocal() as session:
            session.add(
                AIDecision(
                    id=record.id,
                    session_id=record.session_id,
                    route=record.route,
                    action=record.action,
                    score=record.score,
                    reason=record.reason,
                    anomaly_score=record.anomaly_score,
                    anomaly_flag=record.anomaly_flag,
                    random_forest_label=record.random_forest_label,
                    random_forest_confidence=record.random_forest_confidence,
                    attack_probability=record.attack_probability,
                    xgboost_confidence=record.xgboost_confidence,
                    risk_score=record.risk_score,
                    attacker_ip=record.attacker_ip or "",
                    user_agent=record.user_agent or "",
                )
            )
            session.commit()
        return record

    def list_all(self) -> list[AIDecisionRecord]:
        with SecuritySessionLocal() as session:
            rows = session.query(AIDecision).order_by(AIDecision.created_at.asc()).all()
        return [
            AIDecisionRecord(
                id=row.id,
                session_id=row.session_id,
                route=row.route,
                action=row.action,
                score=row.score,
                reason=row.reason,
                anomaly_score=float(getattr(row, "anomaly_score", 0.0)),
                anomaly_flag=int(getattr(row, "anomaly_flag", 0)),
                random_forest_label=getattr(row, "random_forest_label", "normal"),
                random_forest_confidence=float(getattr(row, "random_forest_confidence", 0.0)),
                attack_probability=float(getattr(row, "attack_probability", 0.0)),
                xgboost_confidence=float(getattr(row, "xgboost_confidence", 0.0)),
                risk_score=float(getattr(row, "risk_score", 0.0)),
                attacker_ip=getattr(row, "attacker_ip", None),
                user_agent=getattr(row, "user_agent", None),
            )
            for row in rows
        ]


ai_decision_repository = AIDecisionRepository()
