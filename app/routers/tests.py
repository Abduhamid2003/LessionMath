import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_user
from app.database.connection import get_db
from app.models.class_group import ClassEnrollment
from app.models.result import Result
from app.models.test import Test, TestQuestion
from app.models.user import User, UserRole
from app.schemas import TestSubmit

router = APIRouter(prefix="/api/tests", tags=["tests"])


def _visible_tests_query(db: Session, user: User | None):
    q = db.query(Test)
    if user and user.role in (UserRole.admin, UserRole.teacher):
        return q
    q = q.filter(Test.is_published == True)
    if user and user.role == UserRole.student:
        class_ids = [
            e.class_id
            for e in db.query(ClassEnrollment).filter(ClassEnrollment.student_id == user.id).all()
        ]
        if class_ids:
            q = q.filter((Test.class_id.is_(None)) | (Test.class_id.in_(class_ids)))
        else:
            q = q.filter(Test.class_id.is_(None))
    else:
        q = q.filter(Test.class_id.is_(None))
    return q


@router.get("/")
def list_tests(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    tests = _visible_tests_query(db, user).all()
    return [
        {
            "id": t.id,
            "title_ru": t.title_ru,
            "title_tg": t.title_tg,
            "title_en": t.title_en or "",
            "description_ru": t.description_ru,
            "description_tg": t.description_tg,
            "description_en": t.description_en or "",
            "category": t.category,
            "max_score": t.max_score,
            "question_count": len(t.questions),
            "class_id": t.class_id,
        }
        for t in tests
    ]


@router.get("/{test_id}")
def get_test(
    test_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    test = _visible_tests_query(db, user).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return {
        "id": test.id,
        "title_ru": test.title_ru,
        "title_tg": test.title_tg,
        "title_en": test.title_en or "",
        "description_ru": test.description_ru,
        "description_tg": test.description_tg,
        "description_en": test.description_en or "",
        "questions": [
            {
                "id": q.id,
                "question_ru": q.question_ru,
                "question_tg": q.question_tg,
                "question_en": q.question_en or "",
                "options_ru": json.loads(q.options_ru),
                "options_tg": json.loads(q.options_tg or "[]"),
                "options_en": json.loads(q.options_en or q.options_ru),
                "hint_ru": q.hint_ru,
                "hint_tg": q.hint_tg,
                "hint_en": q.hint_en or "",
                "points": q.points,
            }
            for q in test.questions
        ],
    }


@router.post("/{test_id}/submit")
def submit_test(
    test_id: int,
    data: TestSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    test = _visible_tests_query(db, user).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    score = 0
    max_score = 0
    feedback = []

    for q in test.questions:
        max_score += q.points
        user_answer = data.answers.get(q.id)
        correct = user_answer == q.correct_answer
        if correct:
            score += q.points
        feedback.append({"question_id": q.id, "correct": correct, "points": q.points if correct else 0})

    result = Result(
        user_id=user.id,
        test_id=test.id,
        score=score,
        max_score=max_score,
        activity_type="test",
        details=json.dumps(feedback),
    )
    db.add(result)
    db.commit()

    return {
        "score": score,
        "max_score": max_score,
        "percentage": round(score / max_score * 100, 1) if max_score else 0,
        "feedback": feedback,
    }
