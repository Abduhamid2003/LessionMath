import json

from sqlalchemy.orm import Session

from app.auth.security import get_password_hash
from app.models.achievement import Achievement
from app.models.lesson import Lesson
from app.models.test import Test, TestQuestion
from app.models.user import User, UserRole


def seed_database(db: Session) -> None:
    if db.query(User).first():
        return

    admin = User(
        email="admin@calculus.local",
        username="admin",
        hashed_password=get_password_hash("admin123"),
        full_name="Administrator",
        role=UserRole.admin,
    )
    teacher = User(
        email="teacher@calculus.local",
        username="teacher",
        hashed_password=get_password_hash("teacher123"),
        full_name="Teacher Demo",
        role=UserRole.teacher,
    )
    student = User(
        email="student@calculus.local",
        username="student",
        hashed_password=get_password_hash("student123"),
        full_name="Student Demo",
        role=UserRole.student,
    )
    db.add_all([admin, teacher, student])
    db.flush()

    lessons = [
        Lesson(
            title_ru="Введение в производные",
            title_tg="Муқаддима ба ҳосилаҳо",
            content_ru="Производная функции показывает скорость изменения функции в точке.",
            content_tg="Ҳосилаи функсия суръати тағйири функсияро дар нуқта нишон медиҳад.",
            category="derivatives",
            order_index=1,
            is_published=True,
            author_id=teacher.id,
        ),
        Lesson(
            title_ru="Определённый интеграл",
            title_tg="Интеграли муайян",
            content_ru="Определённый интеграл равен площади под графиком функции на отрезке [a, b].",
            content_tg="Интеграли муайян баробари майдони зери графики функсия дар қитъаи [a, b] аст.",
            category="integrals",
            order_index=2,
            is_published=True,
            author_id=teacher.id,
        ),
        Lesson(
            title_ru="Касательная к графику",
            title_tg="Мамаси ба график",
            content_ru="Уравнение касательной: y = f'(x₀)(x - x₀) + f(x₀).",
            content_tg="Муодилаи мамас: y = f'(x₀)(x - x₀) + f(x₀).",
            category="derivatives",
            order_index=3,
            is_published=True,
            author_id=teacher.id,
        ),
    ]
    db.add_all(lessons)

    test = Test(
        title_ru="Тест: Производные",
        title_tg="Санҷиш: Ҳосилаҳо",
        description_ru="Базовый тест по производным",
        description_tg="Санҷиши асосии ҳосилаҳо",
        category="derivatives",
        max_score=30,
        is_published=True,
        author_id=admin.id,
    )
    db.add(test)
    db.flush()

    questions = [
        TestQuestion(
            test_id=test.id,
            question_ru="Производная x² равна:",
            question_tg="Ҳосилаи x² баробар аст ба:",
            options_ru=json.dumps(["2x", "x", "x²", "2"]),
            options_tg=json.dumps(["2x", "x", "x²", "2"]),
            correct_answer=0,
            hint_ru="Используйте правило степени",
            hint_tg="Қоидаи дараҷаро истифода баред",
        ),
        TestQuestion(
            test_id=test.id,
            question_ru="Производная sin(x) равна:",
            question_tg="Ҳосилаи sin(x) баробар аст ба:",
            options_ru=json.dumps(["cos(x)", "-cos(x)", "sin(x)", "-sin(x)"]),
            options_tg=json.dumps(["cos(x)", "-cos(x)", "sin(x)", "-sin(x)"]),
            correct_answer=0,
        ),
        TestQuestion(
            test_id=test.id,
            question_ru="Производная e^x равна:",
            question_tg="Ҳосилаи e^x баробар аст ба:",
            options_ru=json.dumps(["e^x", "xe^x", "ln(x)", "1"]),
            options_tg=json.dumps(["e^x", "xe^x", "ln(x)", "1"]),
            correct_answer=0,
        ),
    ]
    db.add_all(questions)

    achievements = [
        Achievement(
            code="first_plot",
            title_ru="Первый график",
            title_tg="Графики аввалин",
            description_ru="Постройте свой первый график",
            description_tg="Графики аввалини худро созед",
            icon="chart-line",
            points=10,
        ),
        Achievement(
            code="derivative_master",
            title_ru="Мастер производных",
            title_tg="Устоди ҳосилаҳо",
            description_ru="Вычислите 5 производных",
            description_tg="5 ҳосиларо ҳисоб кунед",
            icon="function",
            points=25,
        ),
        Achievement(
            code="integral_explorer",
            title_ru="Исследователь интегралов",
            title_tg="Кашфкунандаи интегралҳо",
            description_ru="Вычислите определённый интеграл",
            description_tg="Интеграли муайянро ҳисоб кунед",
            icon="integral",
            points=25,
        ),
    ]
    db.add_all(achievements)
    db.commit()
