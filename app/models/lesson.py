from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database.connection import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title_ru = Column(String(300), nullable=False)
    title_tg = Column(String(300), default="")
    title_en = Column(String(300), default="")
    content_ru = Column(Text, nullable=False)
    content_tg = Column(Text, default="")
    content_en = Column(Text, default="")
    category = Column(String(100), default="general")
    order_index = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    image_urls = Column(Text, default="[]")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
