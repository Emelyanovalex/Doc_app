from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext
from datetime import datetime
from app.websocket_manager import manager

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Пользователи
def get_user(db: Session, user_id: int):
    """
    Извлекает пользователя из базы данных по его ID.

    Аргументы:
        db (Session): Сессия базы данных.
        user_id (int): ID пользователя.

    Возвращает:
        User: Объект пользователя или None, если пользователь не найден.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_login(db: Session, login: str) -> models.User:
    """
    Извлекает пользователя из базы данных по логину.

    Аргументы:
        db (Session): Сессия базы данных.
        login (str): Логин пользователя.

    Возвращает:
        User: Объект пользователя или None, если пользователь не найден.
    """
    return db.query(models.User).filter(models.User.login == login).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    Создает нового пользователя в базе данных.

    Аргументы:
        db (Session): Сессия базы данных.
        user (UserCreate): Данные нового пользователя.

    Возвращает:
        User: Созданный объект пользователя.
    """
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
    """
    Удаляет пользователя из базы данных по его ID.

    Аргументы:
        db (Session): Сессия базы данных.
        user_id (int): ID пользователя.

    Возвращает:
        bool: True, если пользователь был успешно удалён, иначе False.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True

def get_unread_messages_with_sender_name(db: Session, user_id: int):
    """
    Получает список непрочитанных сообщений для пользователя с именами отправителей.

    Аргументы:
        db (Session): Сессия базы данных.
        user_id (int): ID пользователя.

    Возвращает:
        list[dict]: Список непрочитанных сообщений с именами отправителей.
    """
    messages = (
        db.query(models.Message, models.User.name.label("sender_name"))
        .join(models.User, models.Message.message_sender == models.User.id)
        .filter(models.Message.message_receiver == user_id, models.Message.message_status == "unread")
        .all()
    )

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

async def save_message(
    db: Session,
    message_sender: int,
    message_receiver: int,
    message: str,
    message_status: str = "unread",
) -> models.Message:
    """
    Сохраняет сообщение в базе данных и отправляет уведомление через WebSocket.

    Аргументы:
        db (Session): Сессия базы данных.
        message_sender (int): ID отправителя сообщения.
        message_receiver (int): ID получателя сообщения.
        message (str): Текст сообщения.
        message_status (str): Статус сообщения (по умолчанию "unread").

    Возвращает:
        Message: Объект сохранённого сообщения.
    """
    db_message = models.Message(
        message_time=datetime.now(),
        message=message,
        message_sender=message_sender,
        message_receiver=message_receiver,
        message_status=message_status,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    notification_data = {
        "detail": "New message",
        "message_id": db_message.id,
        "sender_id": message_sender,
        "receiver_id": message_receiver,
        "message": message,
        "time": db_message.message_time.isoformat(),
    }
    await manager.broadcast(str(notification_data), item_id=message_receiver)

    return db_message
