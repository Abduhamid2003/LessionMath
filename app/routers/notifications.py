from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database.connection import get_db
from app.models.notification import Notification
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/")
def list_notifications(user: User = Depends(require_user), db: Session = Depends(get_db), limit: int = 30):
    items = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    unread = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).count()
    return {
        "unread_count": unread,
        "items": [
            {
                "id": n.id,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    }


@router.post("/read-all")
def mark_all_read(user: User = Depends(require_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).update(
        {"is_read": True}
    )
    db.commit()
    return {"message": "OK"}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "OK"}
