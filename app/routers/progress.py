import json

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database.connection import get_db
from app.models.formula import CalculationHistory
from app.models.result import Result
from app.models.test import Test
from app.models.user import User

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/me")
def my_progress(user: User = Depends(require_user), db: Session = Depends(get_db)):
    results = (
        db.query(Result)
        .filter(Result.user_id == user.id, Result.activity_type == "test")
        .order_by(Result.created_at.desc())
        .limit(20)
        .all()
    )
    test_titles = {t.id: t for t in db.query(Test).all()}
    tests_done = []
    for r in results:
        test = test_titles.get(r.test_id)
        tests_done.append(
            {
                "test_id": r.test_id,
                "title_ru": test.title_ru if test else "",
                "title_tg": test.title_tg if test else "",
                "title_en": getattr(test, "title_en", None) or (test.title_ru if test else ""),
                "score": r.score,
                "max_score": r.max_score,
                "percentage": round(r.score / r.max_score * 100, 1) if r.max_score else 0,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )

    calc_count = (
        db.query(func.count(CalculationHistory.id))
        .filter(CalculationHistory.user_id == user.id)
        .scalar()
    )
    by_op = (
        db.query(CalculationHistory.operation_type, func.count(CalculationHistory.id))
        .filter(CalculationHistory.user_id == user.id)
        .group_by(CalculationHistory.operation_type)
        .all()
    )

    avg_score = (
        db.query(func.avg(Result.score / Result.max_score * 100))
        .filter(Result.user_id == user.id, Result.activity_type == "test", Result.max_score > 0)
        .scalar()
    )

    return {
        "tests": tests_done,
        "calculations_count": calc_count or 0,
        "calculations_by_type": {op: cnt for op, cnt in by_op},
        "avg_test_percentage": round(float(avg_score or 0), 1),
    }
