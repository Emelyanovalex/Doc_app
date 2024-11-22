from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from fastapi import HTTPException
import asyncio
from app.websocket_manager import manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Пользователи
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_login(db: Session, login: str) -> models.User:
    return db.query(models.User).filter(models.User.login == login).first()

def get_user_by_token(db: Session, token: str):
    return db.query(models.User).filter(models.User.token == token).first()

def authenticate_user(db: Session, login: str, password: str):
    user = get_user_by_login(db, login)
    if not user or not pwd_context.verify(password, user.pas):
        return None
    # Обновляем last_login
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.pas)  # Хэширование пароля
    db_user = models.User(
        name=user.name,
        login=user.login,
        office=user.office,
        birthdate=user.birthdate,
        document=user.document,
        role=user.role,  # Используем роль из данных
        pas=hashed_password,
        last_login=datetime.now(),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


def get_all_users(db: Session):
    return db.query(models.User).all()


def update_refresh_token(db: Session, user_id: int, refresh_token: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    user.refresh_token = refresh_token
    db.commit()
    db.refresh(user)
    return user


def verify_refresh_token(db: Session, user_id: int, refresh_token: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return user and user.refresh_token == refresh_token


# Сообщения
# def create_message(
#     db: Session,
#     sender_id: int,
#     receiver_id: int,
#     message: str,
#     priority: str = "primary",
# ):
#     db_message = models.Message(
#         message_time=datetime.now(),
#         message=message,
#         message_sender_id=sender_id,
#         message_receiver_id=receiver_id,
#         is_read=False,
#         priority=priority
#     )
#     db.add(db_message)
#     db.commit()
#     db.refresh(db_message)
#     return db_message

async def create_message_and_broadcast(
    db: Session,
    sender_id: int,
    receiver_id: int,
    message: str,
    priority: str = "primary",
):
    # Создаём сообщение в базе данных
    db_message = models.Message(
        message_time=datetime.now(),
        message=message,
        message_sender_id=sender_id,
        message_receiver_id=receiver_id,
        is_read=False,
        priority=priority,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Формируем данные для WebSocket
    message_data = {
        "type": "message",
        "id": db_message.id,
        "message": db_message.message,
        "sender_id": db_message.message_sender_id,
        "receiver_id": db_message.message_receiver_id,
        "time": db_message.message_time.isoformat(),
        "priority": db_message.priority,
    }

    # Отправляем сообщение через WebSocket
    await manager.broadcast(str(message_data))

    return db_message

def get_messages_by_user(db: Session, user_id: int):
    return db.query(models.Message).filter((models.Message.message_sender_id == user_id) |
        (models.Message.message_receiver_id == user_id)
    ).all()

def get_messages_by_receiver_id(db: Session, user_id: int) -> list[schemas.Message]:
    return db.query(models.Message).filter(models.Message.message_receiver_id == user_id).all()

def get_messages_for_user(db: Session, user_id: int):
    return db.query(models.Message).filter(models.Message.message_receiver_id == user_id).all()


def get_message_by_id(db: Session, message_id: int):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def delete_message(db: Session, message_id: int) -> bool:
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        return False

    db.delete(message)
    db.commit()
    return True


# # Уведомления
# def create_notification(
#     db: Session,
#     sender_id: int,
#     receiver_id: int,
#     notification: str,
#     priority: str = "primary",
# ):
#     db_notification = models.Notification(
#         notification_time=datetime.now(),
#         notification=notification,
#         notification_sender_id=sender_id,  # передаем ID отправителя
#         notification_receiver_id=receiver_id,  # передаем ID получателя
#         is_read=False,
#         priority=priority,
#     )
#     db.add(db_notification)
#     db.commit()
#     db.refresh(db_notification)
#     return db_notification
async def create_notification_and_broadcast(
    db: Session,
    sender_id: int,
    receiver_id: int,
    notification: str,
    priority: str = "primary",
):
    # Создаём уведомление
    db_notification = models.Notification(
        notification_time=datetime.now(),
        notification=notification,
        notification_sender_id=sender_id,
        notification_receiver_id=receiver_id,
        is_read=False,
        priority=priority,
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # Формируем данные для WebSocket
    notification_data = {
        "type": "notification",
        "id": db_notification.id,
        "notification": db_notification.notification,
        "sender_id": db_notification.notification_sender_id,
        "receiver_id": db_notification.notification_receiver_id,
        "time": db_notification.notification_time.isoformat(),
        "priority": db_notification.priority,
    }

    # Отправляем уведомление через WebSocket
    await manager.broadcast(str(notification_data))

    return db_notification


def get_notifications_for_user(db: Session, user_id: int):
    return db.query(models.Notification).filter(models.Notification.notification_receiver_id == user_id).all()


def get_notification_by_id(db: Session, notification_id: int):
    return db.query(models.Notification).filter(models.Notification.id == notification_id).first()


def get_notification_by_receiver_id(db: Session, user_id: int) -> list[schemas.Message]:
    return db.query(models.Notification).filter(models.Notification.notification_receiver_id == user_id).all()


def delete_notification(db: Session, notification_id: int) -> bool:
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        return False

    db.delete(notification)
    db.commit()
    return True


def get_user_messages(db: Session, user_id: int):
    return db.query(models.Message).filter(
        (models.Message.message_sender_id == user_id) |
        (models.Message.message_receiver_id == user_id)
    ).all()


def get_user_notifications(db: Session, user_id: int):
    return db.query(models.Notification).filter(
        (models.Notification.notification_sender_id == user_id) |
        (models.Notification.notification_receiver_id == user_id)
    ).all()


def mark_message_as_read(db: Session, message_id: int, user_id: int):
    message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.message_receiver_id == user_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized")

    message.is_read = True
    db.commit()
    db.refresh(message)
    return message


def get_users_with_pagination(db: Session, limit: int, offset: int):
    return db.query(models.User).offset(offset).limit(limit).all()


def get_messages_with_pagination(db: Session, user_id: int, limit: int, offset: int):
    return db.query(models.Message).filter(
        (models.Message.message_sender_id == user_id) |
        (models.Message.message_receiver_id == user_id)
    ).offset(offset).limit(limit).all()


def get_notifications_with_pagination(db: Session, user_id: int, limit: int, offset: int):
    return db.query(models.Notification).filter(
        models.Notification.notification_receiver_id == user_id
    ).offset(offset).limit(limit).all()
