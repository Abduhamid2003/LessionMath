import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_user
from app.auth.security import decode_token
from app.database.connection import SessionLocal, get_db
from app.models.chat import ChatMessage, ChatRoom, ChatRoomMember
from app.models.class_group import ClassEnrollment, ClassGroup
from app.models.user import User, UserRole
from app.services.chat_service import (
    get_or_create_class_room,
    get_or_create_direct_room,
    is_user_online,
    touch_presence,
    user_rooms,
)
from app.ws.manager import chat_manager

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _student_class_ids(db: Session, student_id: int) -> set[int]:
    return {e.class_id for e in db.query(ClassEnrollment).filter(ClassEnrollment.student_id == student_id).all()}


def _student_has_teacher(db: Session, student_id: int, teacher_id: int) -> bool:
    for class_id in _student_class_ids(db, student_id):
        cg = db.query(ClassGroup).filter(ClassGroup.id == class_id, ClassGroup.teacher_id == teacher_id).first()
        if cg:
            return True
    return False


def _same_class(db: Session, student_a: int, student_b: int) -> bool:
    return bool(_student_class_ids(db, student_a) & _student_class_ids(db, student_b))


def _can_message(db: Session, user: User, other: User) -> bool:
    if user.id == other.id:
        return False
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.teacher:
        return other.role in (UserRole.student, UserRole.admin, UserRole.teacher)
    if user.role == UserRole.student:
        if other.role == UserRole.teacher:
            return _student_has_teacher(db, user.id, other.id)
        if other.role == UserRole.student:
            return _same_class(db, user.id, other.id)
        if other.role == UserRole.admin:
            return True
    return False


def _contactable_users_query(db: Session, user: User):
    q = db.query(User).filter(User.id != user.id, User.is_active.is_(True))
    if user.role == UserRole.admin:
        return q
    if user.role == UserRole.teacher:
        return q.filter(User.role.in_([UserRole.student, UserRole.admin, UserRole.teacher]))
    if user.role == UserRole.student:
        teacher_ids = set()
        classmate_ids = set()
        for class_id in _student_class_ids(db, user.id):
            cg = db.query(ClassGroup).filter(ClassGroup.id == class_id).first()
            if cg:
                teacher_ids.add(cg.teacher_id)
            for en in db.query(ClassEnrollment).filter(
                ClassEnrollment.class_id == class_id, ClassEnrollment.student_id != user.id
            ):
                classmate_ids.add(en.student_id)
        allowed_ids = teacher_ids | classmate_ids
        admin_ids = [u.id for u in db.query(User).filter(User.role == UserRole.admin).all()]
        allowed_ids |= set(admin_ids)
        if not allowed_ids:
            return q.filter(User.id == -1)
        return q.filter(User.id.in_(allowed_ids))
    return q.filter(User.id == -1)


class SendMessage(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def _room_dict(db: Session, room: ChatRoom, user: User) -> dict:
    members = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room.id).all()
    users_info = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            users_info.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "full_name": u.full_name,
                    "role": u.role.value,
                    "online": is_user_online(db, u.id),
                }
            )
    last = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room.id)
        .order_by(ChatMessage.created_at.desc())
        .first()
    )
    return {
        "id": room.id,
        "room_type": room.room_type,
        "title": room.title,
        "class_id": room.class_id,
        "members": users_info,
        "last_message": last.content if last else "",
        "last_at": last.created_at.isoformat() if last and last.created_at else None,
    }


@router.get("/rooms")
def list_rooms(user: User = Depends(require_user), db: Session = Depends(get_db)):
    rooms = user_rooms(db, user)
    return [_room_dict(db, r, user) for r in rooms]


@router.post("/presence")
def heartbeat(user: User = Depends(require_user), db: Session = Depends(get_db)):
    touch_presence(db, user.id, True)
    return {"status": "ok"}


@router.get("/contacts")
def search_contacts(
    q: str = Query("", max_length=100),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = _contactable_users_query(db, user)
    term = q.strip()
    if term:
        like = f"%{term}%"
        query = query.filter((User.username.ilike(like)) | (User.full_name.ilike(like)))
    users = query.order_by(User.username.asc()).limit(40).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "role": u.role.value,
            "online": is_user_online(db, u.id),
        }
        for u in users
    ]


@router.get("/students")
def list_students_for_teacher(user: User = Depends(require_user), db: Session = Depends(get_db)):
    if user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="Teachers only")
    q = db.query(User).filter(User.role == UserRole.student)
    return [{"id": s.id, "username": s.username, "full_name": s.full_name} for s in q.all()]


@router.post("/direct/with/{other_user_id}")
def open_direct_with(other_user_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    other = db.query(User).filter(User.id == other_user_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")
    if not _can_message(db, user, other):
        raise HTTPException(status_code=403, detail="Cannot message this user")
    room = get_or_create_direct_room(db, user.id, other.id)
    room.title = f"{other.full_name or other.username}"
    db.commit()
    return _room_dict(db, room, user)


@router.post("/direct/{student_id}")
def open_direct_chat(student_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    return open_direct_with(student_id, user, db)


@router.get("/rooms/{room_id}/messages")
def get_messages(
    room_id: int,
    limit: int = 100,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    member = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "sender_name": (lambda u: u.username if u else "?")(db.query(User).filter(User.id == m.sender_id).first()),
        }
        for m in msgs
    ]


@router.post("/rooms/{room_id}/messages")
async def post_message(
    room_id: int,
    data: SendMessage,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    member = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    msg = ChatMessage(room_id=room_id, sender_id=user.id, content=data.content.strip())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    payload = {
        "type": "message",
        "id": msg.id,
        "room_id": room_id,
        "sender_id": user.id,
        "sender_name": user.username,
        "content": msg.content,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
    await chat_manager.broadcast(room_id, payload)
    return payload


@router.get("/rooms/{room_id}/online")
def room_online(room_id: int, user: User = Depends(require_user), db: Session = Depends(get_db)):
    member = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member")
    ws_online = set(chat_manager.online_users(room_id))
    members = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room_id).all()
    result = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        if u:
            result.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "online": u.id in ws_online or is_user_online(db, u.id),
                }
            )
    return result


@router.websocket("/ws/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: int, token: str):
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4401)
        return
    user_id = int(payload.get("sub"))
    db = SessionLocal()
    try:
        member = db.query(ChatRoomMember).filter(ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user_id).first()
        if not member:
            await websocket.close(code=4403)
            return
        user = db.query(User).filter(User.id == user_id).first()
        await chat_manager.connect(room_id, user_id, websocket)
        touch_presence(db, user_id, True)
        await chat_manager.broadcast(
            room_id,
            {"type": "presence", "user_id": user_id, "username": user.username, "online": True},
        )
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            if data.get("type") == "ping":
                touch_presence(db, user_id, True)
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue
            if data.get("type") == "message":
                content = (data.get("content") or "").strip()
                if not content:
                    continue
                msg = ChatMessage(room_id=room_id, sender_id=user_id, content=content)
                db.add(msg)
                db.commit()
                db.refresh(msg)
                payload_msg = {
                    "type": "message",
                    "id": msg.id,
                    "room_id": room_id,
                    "sender_id": user_id,
                    "sender_name": user.username,
                    "content": content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                await chat_manager.broadcast(room_id, payload_msg)
    except WebSocketDisconnect:
        pass
    finally:
        chat_manager.disconnect(room_id, user_id)
        touch_presence(db, user_id, False)
        try:
            u = db.query(User).filter(User.id == user_id).first()
            await chat_manager.broadcast(
                room_id,
                {"type": "presence", "user_id": user_id, "username": u.username if u else "", "online": False},
            )
        except Exception:
            pass
        db.close()
