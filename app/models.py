from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
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
        refresh_token (str): Текущий refresh-токен пользователя.
        last_login (datetime): Время последнего входа пользователя в систему.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, unique=True, index=True)
    pas = Column(String)
    office = Column(String)
    birthdate = Column(DateTime)
    document = Column(String)
    role = Column(String)
    refresh_token = Column(String, nullable=True)
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
        is_read (bool): Статус прочитанности сообщения.
        priority (str): Приоритет сообщения (например, "primary", "danger").
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    message_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")


class Notification(Base):
    """
    Модель уведомления.

    Атрибуты:
        id (int): Уникальный идентификатор уведомления.
        notification_time (datetime): Время отправки уведомления.
        notification (str): Текст уведомления.
        notification_sender_id (int): ID пользователя-отправителя.
        notification_receiver_id (int): ID пользователя-получателя.
        is_read (bool): Статус прочитанности уведомления.
        priority (str): Приоритет уведомления (например, "primary", "danger").
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_time = Column(DateTime, nullable=False)
    notification = Column(String, nullable=False)
    notification_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")
