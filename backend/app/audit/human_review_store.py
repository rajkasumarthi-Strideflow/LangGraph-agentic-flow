from typing import Any

from app.database import SessionLocal, init_db
from app.models.db import HumanReviewORM


def _review_to_dict(review: HumanReviewORM) -> dict[str, Any]:
    return {
        "id": review.id,
        "workflow_id": review.workflow_id,
        "escalation_id": review.escalation_id,
        "reviewer_id": review.reviewer_id,
        "decision": review.decision,
        "reason": review.reason,
        "status": review.status,
        "created_at": review.created_at.isoformat(),
    }


def save_human_review(
    workflow_id: str,
    escalation_id: str | None,
    reviewer_id: str,
    decision: str,
    reason: str | None,
    status: str,
) -> dict[str, Any]:
    init_db()
    with SessionLocal() as db:
        review = HumanReviewORM(
            workflow_id=workflow_id,
            escalation_id=escalation_id,
            reviewer_id=reviewer_id,
            decision=decision,
            reason=reason,
            status=status,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return _review_to_dict(review)


def get_human_reviews(workflow_id: str) -> list[dict[str, Any]]:
    init_db()
    with SessionLocal() as db:
        reviews = (
            db.query(HumanReviewORM)
            .filter(HumanReviewORM.workflow_id == workflow_id)
            .order_by(HumanReviewORM.created_at.asc(), HumanReviewORM.id.asc())
            .all()
        )
        return [_review_to_dict(review) for review in reviews]


def clear_human_reviews() -> None:
    init_db()
    with SessionLocal() as db:
        db.query(HumanReviewORM).delete()
        db.commit()
