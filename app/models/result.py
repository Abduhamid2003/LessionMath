from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.database.connection import Base


class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    score = Column(Float, default=0)
    max_score = Column(Float, default=100)
    activity_type = Column(String(50), default="test")
    details = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
