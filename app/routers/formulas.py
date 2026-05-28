from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database.connection import get_db
from app.models.formula import CalculationHistory, Formula
from app.models.user import User
from app.schemas import FormulaCreate

router = APIRouter(prefix="/api/formulas", tags=["formulas"])


@router.get("/history")
def history(user: User = Depends(require_user), db: Session = Depends(get_db), limit: int = 50):
    items = (
        db.query(CalculationHistory)
        .filter(CalculationHistory.user_id == user.id)
        .order_by(CalculationHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "operation_type": h.operation_type,
            "input": h.input_expression,
            "result": h.result_expression,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in items
    ]


@router.get("/favorites")
def favorites(user: User = Depends(require_user), db: Session = Depends(get_db)):
    items = db.query(Formula).filter(Formula.user_id == user.id, Formula.is_favorite == True).all()
    return [{"id": f.id, "expression": f.expression, "label": f.label} for f in items]


@router.post("/favorites")
def add_favorite(data: FormulaCreate, user: User = Depends(require_user), db: Session = Depends(get_db)):
    formula = Formula(
        user_id=user.id,
        expression=data.expression,
        label=data.label,
        is_favorite=True,
    )
    db.add(formula)
    db.commit()
    return {"id": formula.id, "message": "Saved"}
