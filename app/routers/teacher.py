import json
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database.connection import get_db
from app.models.class_group import ClassEnrollment, ClassGroup
from app.models.lesson import Lesson
from app.models.result import Result
from app.models.test import Test, TestQuestion
from app.models.user import User, UserRole
from app.routers.lessons import lesson_dict
from app.schemas import (
    LessonCreate,
    LessonUpdate,
    TestCreate,
    TestImportPayload,
    TestQuestionCreate,
    TestQuestionUpdate,
    TestUpdate,
)
from app.services.notification_service import notify_students

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class EnrollStudent(BaseModel):
    username: str


def _can_edit_test(user: User, test: Test) -> bool:
    if user.role == UserRole.admin:
        return True
    return test.author_id is not None and test.author_id == user.id


def _lesson_payload_to_model(data: dict) -> dict:
    payload = dict(data)
    urls = payload.pop("image_urls", None)
    if urls is not None:
        payload["image_urls"] = json.dumps(urls)
    return payload


def _test_summary(test: Test) -> dict:
    total_points = sum(q.points for q in test.questions)
    return {
        "id": test.id,
        "title_ru": test.title_ru,
        "title_tg": test.title_tg,
        "title_en": test.title_en or "",
        "description_ru": test.description_ru,
        "category": test.category,
        "question_count": len(test.questions),
        "total_points": total_points,
        "author_id": test.author_id,
        "is_published": bool(test.is_published),
        "class_id": test.class_id,
    }


def _test_detail(test: Test) -> dict:
    data = _test_summary(test)
    data["description_tg"] = test.description_tg
    data["description_en"] = test.description_en or ""
    data["questions"] = [
        {
            "id": q.id,
            "question_ru": q.question_ru,
            "question_tg": q.question_tg,
            "question_en": q.question_en or "",
            "options_ru": json.loads(q.options_ru),
            "options_tg": json.loads(q.options_tg or "[]"),
            "options_en": json.loads(q.options_en or q.options_ru),
            "correct_answer": q.correct_answer,
            "points": q.points,
            "hint_ru": q.hint_ru,
            "hint_tg": q.hint_tg,
            "hint_en": q.hint_en or "",
        }
        for q in test.questions
    ]
    return data


@router.get("/lessons")
def list_my_lessons(
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    q = db.query(Lesson).order_by(Lesson.order_index)
    if user.role == UserRole.teacher:
        q = q.filter(Lesson.author_id == user.id)
    lessons = q.all()
    return [lesson_dict(l, include_meta=True) for l in lessons]


@router.get("/lessons/{lesson_id}/preview")
def preview_lesson(
    lesson_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your lesson")
    return lesson_dict(lesson)


@router.post("/lessons")
def create_lesson(
    data: LessonCreate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    payload = _lesson_payload_to_model(data.model_dump())
    lesson = Lesson(**payload, author_id=user.id, is_published=False)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson_dict(lesson, include_meta=True)


@router.patch("/lessons/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonUpdate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Not your lesson")
    updates = data.model_dump(exclude_unset=True)
    if "image_urls" in updates:
        lesson.image_urls = json.dumps(updates.pop("image_urls"))
    for k, v in updates.items():
        setattr(lesson, k, v)
    db.commit()
    return lesson_dict(lesson, include_meta=True)


@router.post("/lessons/{lesson_id}/publish")
def publish_lesson(
    lesson_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your lesson")
    lesson.is_published = True
    db.commit()
    count = notify_students(db, f"Новый урок: {lesson.title_ru}", link=f"/learning?lesson={lesson.id}")
    return {"message": "Published", "notified": count}


@router.post("/lessons/{lesson_id}/unpublish")
def unpublish_lesson(
    lesson_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your lesson")
    lesson.is_published = False
    db.commit()
    return {"message": "Unpublished"}


@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
        raise HTTPException(status_code=400, detail="Invalid image type")
    name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/static/uploads/{name}"}


@router.delete("/lessons/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    if user.role == UserRole.teacher and lesson.author_id not in (None, user.id):
        raise HTTPException(status_code=403, detail="Not your lesson")
    db.delete(lesson)
    db.commit()
    return {"message": "Deleted"}


@router.get("/tests")
def list_my_tests(
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    q = db.query(Test)
    if user.role == UserRole.teacher:
        q = q.filter(Test.author_id == user.id)
    tests = q.order_by(Test.created_at.desc()).all()
    return [_test_summary(t) for t in tests]


@router.get("/tests/{test_id}")
def get_test(
    test_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not your test")
    return _test_detail(test)


@router.post("/tests")
def create_test(
    data: TestCreate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = Test(**data.model_dump(), author_id=user.id, is_published=False)
    db.add(test)
    db.commit()
    db.refresh(test)
    return _test_summary(test)


@router.post("/tests/import")
def import_test(
    data: TestImportPayload,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = Test(
        title_ru=data.title_ru,
        title_tg=data.title_tg or data.title_ru,
        title_en=data.title_en or "",
        description_ru=data.description_ru,
        category=data.category,
        class_id=data.class_id,
        author_id=user.id,
        is_published=False,
    )
    db.add(test)
    db.flush()
    for qd in data.questions:
        if qd.correct_answer < 0 or qd.correct_answer >= len(qd.options_ru):
            raise HTTPException(status_code=400, detail="Invalid correct_answer in import")
        db.add(
            TestQuestion(
                test_id=test.id,
                question_ru=qd.question_ru,
                question_tg=qd.question_tg or qd.question_ru,
                question_en=qd.question_en or qd.question_ru,
                options_ru=json.dumps(qd.options_ru),
                options_tg=json.dumps(qd.options_tg or qd.options_ru),
                options_en=json.dumps(qd.options_en or qd.options_ru),
                correct_answer=qd.correct_answer,
                points=qd.points,
                hint_ru=qd.hint_ru,
                hint_tg=qd.hint_tg,
                hint_en=qd.hint_en,
            )
        )
    db.commit()
    db.refresh(test)
    return {"id": test.id, **_test_detail(test)}


@router.post("/tests/{test_id}/duplicate")
def duplicate_test(
    test_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    source = db.query(Test).filter(Test.id == test_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Test not found")
    if not _can_edit_test(user, source):
        raise HTTPException(status_code=403, detail="Not your test")
    copy = Test(
        title_ru=source.title_ru + " (копия)",
        title_tg=source.title_tg,
        title_en=source.title_en,
        description_ru=source.description_ru,
        description_tg=source.description_tg,
        description_en=source.description_en,
        category=source.category,
        class_id=source.class_id,
        author_id=user.id,
        is_published=False,
    )
    db.add(copy)
    db.flush()
    for q in source.questions:
        db.add(
            TestQuestion(
                test_id=copy.id,
                question_ru=q.question_ru,
                question_tg=q.question_tg,
                question_en=q.question_en,
                options_ru=q.options_ru,
                options_tg=q.options_tg,
                options_en=q.options_en,
                correct_answer=q.correct_answer,
                points=q.points,
                hint_ru=q.hint_ru,
                hint_tg=q.hint_tg,
                hint_en=q.hint_en,
            )
        )
    db.commit()
    db.refresh(copy)
    return _test_summary(copy)


@router.post("/tests/{test_id}/publish")
def publish_test(
    test_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test or not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not allowed")
    if not test.questions:
        raise HTTPException(status_code=400, detail="Add questions before publishing")
    test.is_published = True
    db.commit()
    count = notify_students(
        db,
        f"Новый тест: {test.title_ru}",
        link="/learning",
        class_id=test.class_id,
    )
    return {"message": "Published", "notified": count}


@router.post("/tests/{test_id}/unpublish")
def unpublish_test(
    test_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test or not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not allowed")
    test.is_published = False
    db.commit()
    return {"message": "Unpublished"}


@router.patch("/tests/{test_id}")
def update_test(
    test_id: int,
    data: TestUpdate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not your test")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(test, k, v)
    db.commit()
    return _test_summary(test)


@router.delete("/tests/{test_id}")
def delete_test(
    test_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not your test")
    db.delete(test)
    db.commit()
    return {"message": "Deleted"}


@router.post("/tests/{test_id}/questions")
def add_question(
    test_id: int,
    data: TestQuestionCreate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not your test")
    if data.correct_answer < 0 or data.correct_answer >= len(data.options_ru):
        raise HTTPException(status_code=400, detail="Invalid correct_answer index")

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
    db.refresh(q)
    return {"id": q.id, "message": "Question added"}


@router.patch("/tests/{test_id}/questions/{question_id}")
def update_question(
    test_id: int,
    question_id: int,
    data: TestQuestionUpdate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test or not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not allowed")
    q = db.query(TestQuestion).filter(TestQuestion.id == question_id, TestQuestion.test_id == test_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        if k.startswith("options_"):
            setattr(q, k, json.dumps(v))
        else:
            setattr(q, k, v)
    if data.options_ru is not None and data.correct_answer is not None:
        if data.correct_answer < 0 or data.correct_answer >= len(data.options_ru):
            raise HTTPException(status_code=400, detail="Invalid correct_answer")
    db.commit()
    return {"message": "Updated"}


@router.delete("/tests/{test_id}/questions/{question_id}")
def delete_question(
    test_id: int,
    question_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test or not _can_edit_test(user, test):
        raise HTTPException(status_code=403, detail="Not allowed")
    q = db.query(TestQuestion).filter(TestQuestion.id == question_id, TestQuestion.test_id == test_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": "Deleted"}


@router.get("/classes")
def list_classes(
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    q = db.query(ClassGroup)
    if user.role == UserRole.teacher:
        q = q.filter(ClassGroup.teacher_id == user.id)
    classes = q.all()
    result = []
    for c in classes:
        count = db.query(ClassEnrollment).filter(ClassEnrollment.class_id == c.id).count()
        result.append({"id": c.id, "name": c.name, "student_count": count})
    return result


@router.post("/classes")
def create_class(
    data: ClassCreate,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    group = ClassGroup(name=data.name, teacher_id=user.id)
    db.add(group)
    db.commit()
    db.refresh(group)
    from app.services.chat_service import get_or_create_class_room

    get_or_create_class_room(db, group)
    return {"id": group.id, "name": group.name}


@router.post("/classes/{class_id}/enroll")
def enroll_student(
    class_id: int,
    data: EnrollStudent,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Class not found")
    if user.role == UserRole.teacher and group.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Not your class")
    student = db.query(User).filter(User.username == data.username, User.role == UserRole.student).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    exists = (
        db.query(ClassEnrollment)
        .filter(ClassEnrollment.class_id == class_id, ClassEnrollment.student_id == student.id)
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="Already enrolled")
    db.add(ClassEnrollment(class_id=class_id, student_id=student.id))
    db.commit()
    from app.models.chat import ChatRoom, ChatRoomMember
    from app.services.chat_service import get_or_create_class_room

    room = get_or_create_class_room(db, group)
    exists = (
        db.query(ChatRoomMember)
        .filter(ChatRoomMember.room_id == room.id, ChatRoomMember.user_id == student.id)
        .first()
    )
    if not exists:
        db.add(ChatRoomMember(room_id=room.id, user_id=student.id))
        db.commit()
    return {"message": "Enrolled", "student_id": student.id}


@router.get("/classes/{class_id}/progress")
def class_progress(
    class_id: int,
    user: User = Depends(require_role(UserRole.teacher, UserRole.admin)),
    db: Session = Depends(get_db),
):
    group = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Class not found")
    if user.role == UserRole.teacher and group.teacher_id != user.id:
        raise HTTPException(status_code=403, detail="Not your class")

    enrollments = db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).all()
    students = []
    for en in enrollments:
        st = db.query(User).filter(User.id == en.student_id).first()
        if not st:
            continue
        results = db.query(Result).filter(Result.user_id == st.id, Result.activity_type == "test").all()
        avg = 0.0
        if results:
            avg = sum(r.score / r.max_score * 100 for r in results if r.max_score) / len(results)
        students.append(
            {
                "id": st.id,
                "username": st.username,
                "full_name": st.full_name,
                "tests_taken": len(results),
                "avg_percentage": round(avg, 1),
            }
        )
    return {"class_id": class_id, "name": group.name, "students": students}
