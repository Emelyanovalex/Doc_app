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
        message_sender (int): ID пользователя-отправителя.
        message_receiver (int): ID пользователя-получателя.
        message_status (str): Статус сообщения (например, "unread", "read").
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    message_sender = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_receiver = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_status = Column(String, default="unread", nullable=False)

