from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatRoom, ChatRoomMember, UserPresence
from app.models.class_group import ClassEnrollment, ClassGroup
from app.models.user import User, UserRole


def touch_presence(db: Session, user_id: int, online: bool = True):
    row = db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
    if not row:
        row = UserPresence(user_id=user_id)
        db.add(row)
    row.last_seen = datetime.utcnow()
    row.is_online = 1 if online else 0
    db.commit()


def is_user_online(db: Session, user_id: int, seconds: int = 90) -> bool:
    row = db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
    if not row or not row.last_seen:
        return False
    threshold = datetime.utcnow() - timedelta(seconds=seconds)
    return row.last_seen >= threshold and bool(row.is_online)


def get_or_create_class_room(db: Session, class_group: ClassGroup) -> ChatRoom:
    room = db.query(ChatRoom).filter(ChatRoom.room_type == "class", ChatRoom.class_id == class_group.id).first()
    if room:
        return room
    room = ChatRoom(room_type="class", class_id=class_group.id, title=class_group.name)
    db.add(room)
    db.flush()
    enrollments = db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_group.id).all()
    member_ids = {class_group.teacher_id, *(e.student_id for e in enrollments)}
    for uid in member_ids:
        db.add(ChatRoomMember(room_id=room.id, user_id=uid))
    db.commit()
    db.refresh(room)
    return room


def get_or_create_direct_room(db: Session, user_a: int, user_b: int) -> ChatRoom:
    rooms = db.query(ChatRoom).filter(ChatRoom.room_type == "direct").all()
    pair = {user_a, user_b}
    for room in rooms:
        members = {m.user_id for m in db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room.id).all()}
        if members == pair:
            return room
    room = ChatRoom(room_type="direct", title="Direct chat")
    db.add(room)
    db.flush()
    db.add(ChatRoomMember(room_id=room.id, user_id=user_a))
    db.add(ChatRoomMember(room_id=room.id, user_id=user_b))
    db.commit()
    db.refresh(room)
    return room


def user_rooms(db: Session, user: User) -> list[ChatRoom]:
    member_room_ids = [m.room_id for m in db.query(ChatRoomMember).filter(ChatRoomMember.user_id == user.id).all()]
    if not member_room_ids:
        if user.role == UserRole.teacher:
            for c in db.query(ClassGroup).filter(ClassGroup.teacher_id == user.id).all():
                get_or_create_class_room(db, c)
        elif user.role == UserRole.student:
            for en in db.query(ClassEnrollment).filter(ClassEnrollment.student_id == user.id).all():
                cg = db.query(ClassGroup).filter(ClassGroup.id == en.class_id).first()
                if cg:
                    get_or_create_class_room(db, cg)
        member_room_ids = [m.room_id for m in db.query(ChatRoomMember).filter(ChatRoomMember.user_id == user.id).all()]
    return db.query(ChatRoom).filter(ChatRoom.id.in_(member_room_ids)).order_by(ChatRoom.id.desc()).all() if member_room_ids else []
