import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.database.connection import get_db
from app.models.lesson import Lesson
from app.models.user import User, UserRole
from app.schemas import LessonCreate, LessonUpdate

router = APIRouter(prefix="/api/lessons", tags=["lessons"])


def lesson_dict(l: Lesson, include_meta: bool = False) -> dict:
    data = {
        "id": l.id,
        "title_ru": l.title_ru,
        "title_tg": l.title_tg,
        "title_en": l.title_en or "",
        "content_ru": l.content_ru,
        "content_tg": l.content_tg,
        "content_en": l.content_en or "",
        "category": l.category,
        "order_index": l.order_index,
        "image_urls": json.loads(l.image_urls or "[]"),
    }
    if include_meta:
        data["is_published"] = bool(l.is_published)
        data["author_id"] = l.author_id
    return data


@router.get("/")
def list_lessons(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    q = db.query(Lesson).order_by(Lesson.order_index)
    if user and user.role in (UserRole.teacher, UserRole.admin):
        pass
    else:
        q = q.filter(Lesson.is_published == True)
    return [lesson_dict(l) for l in q.all()]


@router.get("/{lesson_id}")
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if not lesson.is_published:
        if not user or user.role not in (UserRole.admin, UserRole.teacher):
            raise HTTPException(status_code=404, detail="Lesson not found")
        if user.role == UserRole.teacher and lesson.author_id != user.id:
            raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson_dict(lesson)


@router.post("/")
def create_lesson(
    data: LessonCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.teacher)),
):
    payload = data.model_dump()
    urls = payload.pop("image_urls", [])
    lesson = Lesson(**payload, author_id=user.id, is_published=False, image_urls=json.dumps(urls))
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson_dict(lesson, include_meta=True)


@router.patch("/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.teacher)),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Not your lesson")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(lesson, k, v)
    db.commit()
    return lesson_dict(lesson, include_meta=True)


@router.delete("/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.admin, UserRole.teacher)),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Not your lesson")
    db.delete(lesson)
    db.commit()
    return {"message": "Deleted"}
