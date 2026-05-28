from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title_ru = Column(String(300), nullable=False)
    title_tg = Column(String(300), default="")
    title_en = Column(String(300), default="")
    description_ru = Column(Text, default="")
    description_tg = Column(Text, default="")
    description_en = Column(Text, default="")
    category = Column(String(100), default="derivatives")
    max_score = Column(Integer, default=100)
    is_published = Column(Boolean, default=False)
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_ru = Column(Text, nullable=False)
    question_tg = Column(Text, default="")
    question_en = Column(Text, default="")
    options_ru = Column(Text, nullable=False)
    options_tg = Column(Text, default="[]")
    options_en = Column(Text, default="[]")
    correct_answer = Column(Integer, nullable=False)
    points = Column(Integer, default=10)
    hint_ru = Column(Text, default="")
    hint_tg = Column(Text, default="")
    hint_en = Column(Text, default="")

    test = relationship("Test", back_populates="questions")
