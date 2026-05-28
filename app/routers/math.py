from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.middleware.rate_limit import limiter
from app.models.achievement import Achievement, UserAchievement
from app.models.formula import CalculationHistory
from app.models.user import User
from app.schemas import (
    CheckDerivativeRequest,
    DerivativeRequest,
    FunctionEvalRequest,
    IntegralRequest,
    LimitRequest,
    MultiPlotRequest,
    NumericEvalRequest,
    PlotRequest,
    TangentRequest,
    TaylorRequest,
)
from app.services.math_service import MathService
from app.services.pdf_service import build_derivative_pdf
from app.utils.expression_validator import validate_expression

router = APIRouter(prefix="/api/math", tags=["math"])


def _validated_plot(data: PlotRequest) -> PlotRequest:
    data.expression = validate_expression(data.expression)
    return data


@router.post("/plot")
@limiter.limit("30/minute")
def plot(
    request: Request,
    data: PlotRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    data = _validated_plot(data)
    result = MathService.plot_data(data.expression, data.x_min, data.x_max, data.points)
    intersections = MathService.intersections(data.expression, data.x_min, data.x_max)
    result["intersections"] = intersections
    _save_history(db, user, "plot", data.expression, result.get("expression", ""))
    _try_achievement(db, user, "first_plot")
    return result


@router.post("/plot-multi")
@limiter.limit("20/minute")
def plot_multi(
    request: Request,
    data: MultiPlotRequest,
    user: User | None = Depends(get_current_user),
):
    exprs = [validate_expression(e) for e in data.expressions]
    return MathService.multi_plot(exprs, data.x_min, data.x_max, data.points)


@router.post("/derivative")
@limiter.limit("30/minute")
def derivative(
    request: Request,
    data: DerivativeRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    data.expression = validate_expression(data.expression)
    result = MathService.derivative(data.expression, data.order)
    plot = MathService.plot_data(data.expression)
    deriv_plot = MathService.plot_data(result["derivative"])
    result["function_plot"] = plot
    result["derivative_plot"] = deriv_plot
    _save_history(db, user, "derivative", data.expression, result["derivative"])
    _count_derivative_achievements(db, user)
    return result


@router.post("/derivative/pdf")
@limiter.limit("10/minute")
def derivative_pdf(request: Request, data: DerivativeRequest):
    data.expression = validate_expression(data.expression)
    result = MathService.derivative(data.expression, data.order)
    pdf_bytes = build_derivative_pdf(data.expression, result["steps"], result["derivative"])
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=derivative.pdf"},
    )


@router.post("/tangent")
@limiter.limit("30/minute")
def tangent(request: Request, data: TangentRequest):
    data.expression = validate_expression(data.expression)
    plot = MathService.plot_data(data.expression)
    tangent_data = MathService.tangent_line(data.expression, data.x0, data.x_range)
    return {"plot": plot, "tangent": tangent_data}


@router.post("/integral")
@limiter.limit("30/minute")
def integral(
    request: Request,
    data: IntegralRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    data.expression = validate_expression(data.expression)
    result = MathService.definite_integral(data.expression, data.a, data.b, data.method)
    plot = MathService.plot_data(data.expression, data.a, data.b)
    result["function_plot"] = plot
    _save_history(db, user, "integral", data.expression, str(result["value"]))
    _try_achievement(db, user, "integral_explorer")
    return result


@router.post("/integral/indefinite")
@limiter.limit("30/minute")
def indefinite_integral(request: Request, data: DerivativeRequest, db: Session = Depends(get_db), user: User | None = Depends(get_current_user)):
    data.expression = validate_expression(data.expression)
    result = MathService.indefinite_integral(data.expression)
    _save_history(db, user, "indefinite", data.expression, result["antiderivative"])
    return result


@router.post("/limit")
@limiter.limit("30/minute")
def compute_limit(request: Request, data: LimitRequest, db: Session = Depends(get_db), user: User | None = Depends(get_current_user)):
    data.expression = validate_expression(data.expression)
    result = MathService.limit(data.expression, data.point, data.direction)
    _save_history(db, user, "limit", data.expression, result["value"])
    return result


@router.post("/taylor")
@limiter.limit("20/minute")
def taylor(request: Request, data: TaylorRequest):
    data.expression = validate_expression(data.expression)
    return MathService.taylor_series(data.expression, data.x0, data.order)


@router.post("/check-derivative")
@limiter.limit("40/minute")
def check_derivative(request: Request, data: CheckDerivativeRequest):
    data.expression = validate_expression(data.expression)
    data.user_answer = validate_expression(data.user_answer)
    return MathService.check_derivative(data.expression, data.user_answer)


@router.api_route("/evaluate", methods=["GET", "POST"])
@limiter.limit("60/minute")
def evaluate(request: Request, expression: str, x: float):
    expression = validate_expression(expression)
    return {"value": MathService.evaluate(expression, x)}


@router.post("/evaluate-numeric")
@limiter.limit("60/minute")
def evaluate_numeric(
    request: Request,
    data: NumericEvalRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    result = MathService.evaluate_numeric(data.expression)
    _save_history(db, user, "calculator", data.expression, str(result["value"]))
    return result


@router.post("/evaluate-function")
@limiter.limit("60/minute")
def evaluate_function(request: Request, data: FunctionEvalRequest, db: Session = Depends(get_db), user: User | None = Depends(get_current_user)):
    expr = validate_expression(data.expression)
    value = MathService.evaluate(expr, data.x)
    plot = MathService.plot_data(expr, data.x - 3, data.x + 3)
    return {"value": value, "x": data.x, "plot": plot}


@router.post("/calculator/derivative-at")
@limiter.limit("40/minute")
def derivative_at(request: Request, data: FunctionEvalRequest):
    data.expression = validate_expression(data.expression)
    return MathService.calculator_derivative_at(data.expression, data.x)


def _save_history(db: Session, user: User | None, op: str, inp: str, out: str):
    if not user:
        return
    db.add(CalculationHistory(user_id=user.id, operation_type=op, input_expression=inp, result_expression=out))
    db.commit()


def _try_achievement(db: Session, user: User | None, code: str):
    if not user:
        return
    ach = db.query(Achievement).filter(Achievement.code == code).first()
    if not ach:
        return
    exists = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == ach.id)
        .first()
    )
    if not exists:
        db.add(UserAchievement(user_id=user.id, achievement_id=ach.id))
        db.commit()


def _count_derivative_achievements(db: Session, user: User | None):
    if not user:
        return
    count = (
        db.query(CalculationHistory)
        .filter(CalculationHistory.user_id == user.id, CalculationHistory.operation_type == "derivative")
        .count()
    )
    if count >= 5:
        _try_achievement(db, user, "derivative_master")
