from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    """
    Модель пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        name (str): Имя пользователя.
        login (str): Логин (уникальный).
        pas (str): Хэшированный пароль.
        office (str): Офис, к которому относится пользователь.
        birthdate (datetime): Дата рождения пользователя.
        document (str): Документ, связанный с пользователем.
        role (str): Роль пользователя (например, "user", "admin").
        last_login (datetime): Время последнего входа пользователя в систему.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, unique=True, index=True)
    pas = Column(String)
    office = Column(String)
    birthdate = Column(DateTime)
    role = Column(String)
    last_login = Column(DateTime, nullable=False, server_default=func.now())


class Message(Base):
    """
    Модель сообщения.

    Атрибуты:
        id (int): Уникальный идентификатор сообщения.
        message_time (datetime): Время отправки сообщения.
        message (str): Текст сообщения.
        message_sender_id (int): ID пользователя-отправителя.
        message_receiver_id (int): ID пользователя-получателя.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    message_sender = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_receiver = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_status = Column(String, default="unread", nullable=False)


class Notification(Base):
    """
    Модель уведомления.

    Атрибуты:
        id (int): Уникальный идентификатор уведомления.
        notification_time (datetime): Время отправки уведомления.
        notification (str): Текст уведомления.
        notification_sender_id (int): ID пользователя-отправителя.
        notification_receiver_id (int): ID пользователя-получателя.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_time = Column(DateTime, nullable=False)
    notification = Column(String, nullable=False)
    notification_sender = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_receiver = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_status = Column(String, default="unread", nullable=False)
