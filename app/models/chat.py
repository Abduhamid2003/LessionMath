from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database.connection import Base


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(String(20), nullable=False)  # direct | class
    class_id = Column(Integer, ForeignKey("class_groups.id"), nullable=True)
    title = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"
    __table_args__ = (UniqueConstraint("room_id", "user_id", name="uq_room_member"),)

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPresence(Base):
    __tablename__ = "user_presence"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Integer, default=0)
