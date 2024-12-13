from typing import Optional
from fastapi.responses import JSONResponse
from app.models import Message, User
from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from fastapi import HTTPException
from app.websocket_manager import manager
from app.exceptions import MESSAGE_NOT_FOUND, USER_NOT_FOUND

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


def filter_users(
        db: Session,
        name: Optional[str] = None,
        role: Optional[str] = None,
        office: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0
) -> list[models.User]:
    """
    Фильтрует и сортирует пользователей по заданным критериям.

    Аргументы:
        db (Session): Сессия базы данных.
        name (Optional[str]): Фильтр по имени.
        role (Optional[str]): Фильтр по роли.
        office (Optional[str]): Фильтр по офису.
        sort_by (str): Поле для сортировки. По умолчанию "id".
        sort_order (str): Порядок сортировки ("asc" или "desc"). По умолчанию "asc".
        limit (int): Максимальное количество записей.
        offset (int): Смещение для пагинации.

    Возвращает:
        list[models.User]: Список отфильтрованных и отсортированных пользователей.
    """
    query = db.query(models.User)

    if name:
        query = query.filter(models.User.name.ilike(f"%{name}%"))
    if role:
        query = query.filter(models.User.role == role)
    if office:
        query = query.filter(models.User.office.ilike(f"%{office}%"))

    # Сортировка
    sort_field = getattr(models.User, sort_by, None)
    if not sort_field:
        raise HTTPException(status_code=400, detail=f"Поле '{sort_by}' не существует для сортировки.")

    if sort_order == "desc":
        sort_field = sort_field.desc()
    elif sort_order != "asc":
        raise HTTPException(status_code=400, detail="Порядок сортировки должен быть 'asc' или 'desc'.")

    query = query.order_by(sort_field)

    return query.offset(offset).limit(limit).all()


def update_message_status(db: Session, message_id: int, new_status: str):
    """
    Обновляет статус сообщения.

    Аргументы:
        db (Session): Сессия базы данных.
        message_id (int): ID сообщения.
        new_status (str): Новый статус ("unread" или "read").

    Возвращает:
        models.Message: Обновлённое сообщение.
    """
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        raise MESSAGE_NOT_FOUND

    message.message_status = new_status
    db.commit()
    db.refresh(message)
    return message


async def create_message_and_broadcast(
    db: Session,
    sender: int,
    receiver: int,
    message: str,
):
    # Создаём сообщение в базе данных
    db_message = models.Message(
        message_time=datetime.now(),
        message=message,
        message_sender=sender,
        message_receiver=receiver,
        message_status="unread",
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    # Формируем данные для WebSocket
    message_data = {
        "type": "message",
        "id": db_message.id,
        "message": db_message.message,
        "sender_id": db_message.message_sender,
        "receiver_id": db_message.message_receiver,
        "time": db_message.message_time.isoformat(),
    }

    # Отправляем сообщение через WebSocket
    await manager.broadcast(str(message_data))

    return db_message

def get_messages_by_user(db: Session, user_id: int):
    return db.query(models.Message).filter((models.Message.message_sender == user_id) |
        (models.Message.message_receiver == user_id)
    ).all()

def get_messages_by_receiver_id(db: Session, user_id: int) -> list[schemas.Message]:
    return db.query(models.Message).filter(models.Message.message_receiver == user_id).all()

def get_messages_for_user(db: Session, user_id: int):
    return db.query(models.Message).filter(models.Message.message_receiver == user_id).all()


def get_message_by_id(db: Session, message_id: int):
    return db.query(models.Message).filter(models.Message.id == message_id).first()

def delete_message(db: Session, message_id: int) -> bool:
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message:
        return False

    db.delete(message)
    db.commit()
    return True


async def create_notification_and_broadcast(
    db: Session,
    sender: int,
    receiver: int,
    notification: str,
):
    # Создаём уведомление
    db_notification = models.Notification(
        notification_time=datetime.now(),
        notification=notification,
        notification_sender=sender,
        notification_receiver=receiver,
        notification_status="unread",
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)

    # Формируем данные для WebSocket
    notification_data = {
        "type": "notification",
        "id": db_notification.id,
        "notification": db_notification.notification,
        "sender": db_notification.notification_sender,
        "receiver": db_notification.notification_receiver,
        "time": db_notification.notification_time.isoformat(),
    }

    # Отправляем уведомление через WebSocket
    await manager.broadcast(str(notification_data))

    return db_notification


def get_notifications_for_user(db: Session, user_id: int):
    return db.query(models.Notification).filter(models.Notification.notification_receiver == user_id).all()


def get_notification_by_id(db: Session, notification_id: int):
    return db.query(models.Notification).filter(models.Notification.id == notification_id).first()


def get_notification_by_receiver_id(db: Session, user_id: int) -> list[schemas.Message]:
    return db.query(models.Notification).filter(models.Notification.notification_receiver== user_id).all()


def delete_notification(db: Session, notification_id: int) -> bool:
    notification = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if not notification:
        return False

    db.delete(notification)
    db.commit()
    return True


def get_user_messages(db: Session, user_id: int):
    return db.query(models.Message).filter(
        (models.Message.message_sender == user_id) |
        (models.Message.message_receiver == user_id)
    ).all()


def get_user_notifications(db: Session, user_id: int):
    return db.query(models.Notification).filter(
        (models.Notification.notification_sender == user_id) |
        (models.Notification.notification_receiver == user_id)
    ).all()


def mark_message_as_read(db: Session, message_id: int, user_id: int):
    """
    Отмечает сообщение как прочитанное, если оно принадлежит текущему пользователю.

    Аргументы:
        db (Session): Сессия базы данных.
        message_id (int): ID сообщения.
        user_id (int): ID текущего пользователя.

    Возвращает:
        models.Message: Обновлённое сообщение.

    Исключения:
        HTTPException: Если сообщение не найдено или пользователь не авторизован.
    """
    message = db.query(models.Message).filter(
        models.Message.id == message_id,
        models.Message.message_receiver == user_id  # Убедитесь, что пользователь является получателем
    ).first()

    if not message:
        raise MESSAGE_NOT_FOUND

    message.message_status = "read"  # Установить статус как "прочитано"
    db.commit()
    db.refresh(message)
    return message


def get_unread_messages_with_sender_name(db: Session, user_id: int):
    """
    Получает список непрочитанных сообщений для пользователя с именами отправителей.

    Аргументы:
        db (Session): Сессия базы данных.
        user_id (int): ID пользователя.

    Возвращает:
        list[dict]: Список непрочитанных сообщений с именами отправителей.
    """
    # Соединяем таблицы messages и users
    messages = (
        db.query(models.Message, models.User.name.label("sender_name"))
        .join(models.User, models.Message.message_sender == models.User.id)
        .filter(models.Message.message_receiver == user_id, models.Message.message_status == "unread")
        .all()
    )

    # Формируем ответ
    return [
        {
            "message_id": message.Message.id,
            "message_sender": message.Message.message_sender,
            "name": message.sender_name,
            "message_time": message.Message.message_time.strftime('%d-%m-%Y %H:%M:%S'),
            "message": message.Message.message,
        }
        for message in messages
    ]


def get_all_user_messages(db: Session, user_id: int):
    """
    Получает все сообщения пользователя (отправленные и полученные).

    Аргументы:
        db (Session): Сессия базы данных.
        user_id (int): ID пользователя.

    Возвращает:
        list[dict]: Список всех сообщений или пустая структура, если сообщений нет.
    """
    messages = (
        db.query(
            models.Message.id.label("message_id"),
            models.Message.message.label("message"),
            models.Message.message_time.label("message_time"),
            models.Message.message_sender.label("message_sender"),
            models.Message.message_receiver.label("message_receiver"),
            models.Message.message_status.label("message_status"),
        )
        .filter((models.Message.message_sender == user_id) | (models.Message.message_receiver == user_id))
        .all()
    )

    # Если сообщений нет, вернуть пустую структуру
    if not messages:
        return [{
            "message_id": None,
            "message_sender": None,
            "message_receiver": None,
            "message_time": None,
            "message": None,
            "message_status": None,
        }]

    # Форматируем данные
    return [
        {
            "message_id": msg.message_id,
            "message_sender": msg.message_sender,
            "message_receiver": msg.message_receiver,
            "message_time": msg.message_time.strftime('%d-%m-%Y %H:%M:%S') if msg.message_time else None,
            "message": msg.message,
            "message_status": msg.message_status,
        }
        for msg in messages
    ]


def get_users_with_pagination(db: Session, limit: int, offset: int):
    return db.query(models.User).offset(offset).limit(limit).all()


def get_messages_with_pagination(db: Session, user_id: int, limit: int, offset: int):
    return db.query(models.Message).filter(
        (models.Message.message_sender == user_id) |
        (models.Message.message_receiver == user_id)
    ).offset(offset).limit(limit).all()


def get_notifications_with_pagination(db: Session, user_id: int, limit: int, offset: int):
    return db.query(models.Notification).filter(
        models.Notification.notification_receiver == user_id
    ).offset(offset).limit(limit).all()

async def save_message(
    db: Session,
    message_sender: int,
    message_receiver: int,
    message: str,
    message_status: str = "unread",
) -> models.Message:
    """
    Сохраняет сообщение в базе данных и возвращает объект сообщения.
    """
    # Создаём объект сообщения
    db_message = models.Message(
        message_time=datetime.now(),
        message=message,
        message_sender=message_sender,
        message_receiver=message_receiver,
        message_status=message_status,
    )
    # Сохраняем сообщение в базе данных
    db.add(db_message)
    db.commit()
    db.refresh(db_message)  # Получаем обновлённый объект из базы данных

    # Уведомляем через WebSocket
    notification_data = {
        "detail": "New message",
        "message_id": db_message.id,
        "sender_id": message_sender,
        "receiver_id": message_receiver,
        "message": message,
        "time": db_message.message_time.isoformat(),
    }
    # Рассылка уведомлений по WebSocket
    await manager.broadcast(str(notification_data), item_id=message_receiver)

    return db_message
