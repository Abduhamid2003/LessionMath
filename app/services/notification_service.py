from sqlalchemy.orm import Session

from app.models.class_group import ClassEnrollment
from app.models.notification import Notification
from app.models.user import User, UserRole


def notify_students(
    db: Session,
    message: str,
    link: str = "",
    class_id: int | None = None,
) -> int:
    if class_id:
        enrollments = db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).all()
        user_ids = [e.student_id for e in enrollments]
    else:
        user_ids = [u.id for u in db.query(User).filter(User.role == UserRole.student).all()]

    count = 0
    for uid in user_ids:
        db.add(Notification(user_id=uid, message=message, link=link))
        count += 1
    if count:
        db.commit()
    return count
