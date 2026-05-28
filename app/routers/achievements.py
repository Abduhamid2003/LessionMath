from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_user
from app.database.connection import get_db
from app.models.achievement import Achievement, UserAchievement
from app.models.user import User

router = APIRouter(prefix="/api/achievements", tags=["achievements"])


@router.get("/")
def list_achievements(db: Session = Depends(get_db)):
    items = db.query(Achievement).all()
    return [
        {
            "id": a.id,
            "code": a.code,
            "title_ru": a.title_ru,
            "title_tg": a.title_tg,
            "title_en": getattr(a, "title_en", None) or a.title_ru,
            "description_ru": a.description_ru,
            "description_tg": a.description_tg,
            "description_en": getattr(a, "description_en", None) or a.description_ru,
            "icon": a.icon,
            "points": a.points,
        }
        for a in items
    ]


@router.get("/me")
def my_achievements(user: User = Depends(require_user), db: Session = Depends(get_db)):
    earned_ids = {
        ua.achievement_id
        for ua in db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
    }
    all_ach = db.query(Achievement).all()
    return [
        {
            "id": a.id,
            "code": a.code,
            "title_ru": a.title_ru,
            "title_tg": a.title_tg,
            "title_en": getattr(a, "title_en", None) or a.title_ru,
            "description_ru": a.description_ru,
            "description_tg": a.description_tg,
            "description_en": getattr(a, "description_en", None) or a.description_ru,
            "icon": a.icon,
            "points": a.points,
            "earned": a.id in earned_ids,
        }
        for a in all_ach
    ]
