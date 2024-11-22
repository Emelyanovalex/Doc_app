from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from app.database import Base
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, unique=True, index=True)
    pas = Column(String)  # Хранит хэш пароля
    office = Column(String)
    birthdate = Column(DateTime)  # Дата рождения
    document = Column(String)  # Поле для документа
    role = Column(String)
    refresh_token = Column(String, nullable=True)  # Только Refresh Token
    last_login = Column(DateTime, nullable=False, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    message_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_time = Column(DateTime, nullable=False)
    notification = Column(String, nullable=False)
    notification_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")
