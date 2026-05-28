from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.database.connection import Base


class Formula(Base):
    __tablename__ = "formulas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expression = Column(String(500), nullable=False)
    label = Column(String(200), default="")
    category = Column(String(100), default="custom")
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CalculationHistory(Base):
    __tablename__ = "calculation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    operation_type = Column(String(50), nullable=False)
    input_expression = Column(String(500), nullable=False)
    result_expression = Column(String(500), default="")
    parameters = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)
