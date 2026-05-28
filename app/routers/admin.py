import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.connection import get_db
from app.models.formula import CalculationHistory, Formula
from app.models.lesson import Lesson
from app.models.result import Result
from app.models.test import Test, TestQuestion
from app.models.user import User, UserRole
from app.schemas import LessonCreate, LessonUpdate, TestCreate, TestQuestionCreate

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: int,
    role: UserRole = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role
    db.commit()
    return {"message": "Updated"}


@router.patch("/users/{user_id}/active")
def toggle_active(
    user_id: int,
    active: bool = Query(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = active
    db.commit()
    return {"message": "Updated"}


@router.get("/statistics")
def statistics(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    return {
        "users_count": db.query(func.count(User.id)).scalar(),
        "results_count": db.query(func.count(Result.id)).scalar(),
        "calculations_count": db.query(func.count(CalculationHistory.id)).scalar(),
        "formulas_count": db.query(func.count(Formula.id)).scalar(),
        "lessons_count": db.query(func.count(Lesson.id)).scalar(),
        "tests_count": db.query(func.count(Test.id)).scalar(),
        "avg_test_score": db.query(func.avg(Result.score)).filter(Result.activity_type == "test").scalar() or 0,
    }


@router.get("/lessons")
def admin_lessons(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    lessons = db.query(Lesson).order_by(Lesson.order_index).all()
    return [_lesson_dict(l) for l in lessons]


@router.put("/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(lesson, k, v)
    db.commit()
    return _lesson_dict(lesson)


@router.delete("/lessons/{lesson_id}")
def admin_delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return {"message": "Deleted"}


@router.post("/lessons/import")
def import_lessons(
    payload: list[LessonCreate],
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    created = []
    for item in payload:
        lesson = Lesson(**item.model_dump(), author_id=admin.id)
        db.add(lesson)
        db.flush()
        created.append(lesson.id)
    db.commit()
    return {"created": created, "count": len(created)}


@router.get("/tests")
def admin_tests(db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.admin))):
    tests = db.query(Test).all()
    return [
        {
            "id": t.id,
            "title_ru": t.title_ru,
            "title_tg": t.title_tg,
            "title_en": t.title_en or "",
            "category": t.category,
            "question_count": len(t.questions),
        }
        for t in tests
    ]


@router.post("/tests")
def create_test(
    data: TestCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    test = Test(**data.model_dump(), author_id=admin.id)
    db.add(test)
    db.commit()
    db.refresh(test)
    return {"id": test.id}


@router.post("/tests/{test_id}/questions")
def add_question(
    test_id: int,
    data: TestQuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    q = TestQuestion(
        test_id=test_id,
        question_ru=data.question_ru,
        question_tg=data.question_tg or data.question_ru,
        question_en=data.question_en or data.question_ru,
        options_ru=json.dumps(data.options_ru),
        options_tg=json.dumps(data.options_tg or data.options_ru),
        options_en=json.dumps(data.options_en or data.options_ru),
        correct_answer=data.correct_answer,
        points=data.points,
        hint_ru=data.hint_ru,
        hint_tg=data.hint_tg,
        hint_en=data.hint_en,
    )
    db.add(q)
    db.commit()
    return {"id": q.id}


@router.delete("/tests/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    db.delete(test)
    db.commit()
    return {"message": "Deleted"}


def _lesson_dict(lesson: Lesson) -> dict:
    return {
        "id": lesson.id,
        "title_ru": lesson.title_ru,
        "title_tg": lesson.title_tg,
        "title_en": lesson.title_en or "",
        "content_ru": lesson.content_ru,
        "content_tg": lesson.content_tg,
        "content_en": lesson.content_en or "",
        "category": lesson.category,
        "order_index": lesson.order_index,
    }
