from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    login = Column(String, unique=True, index=True)
    pas = Column(String)  # Хранит хэш пароля
    office = Column(String)
    birthdate = Column(DateTime)  # Дата рождения
    document = Column(String)  # Поле для документа
    role = Column(String)  # Роль пользователя (например, admin, user)
    token = Column(String, nullable=True)  # Поле для хранения access_token
    last_login = Column(DateTime, nullable=True)  # Последний вход


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    message_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    message_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")

    message_sender = relationship("User", foreign_keys=[message_sender_id])
    message_receiver = relationship("User", foreign_keys=[message_receiver_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_time = Column(DateTime, nullable=False)
    notification = Column(String, nullable=False)
    notification_sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    priority = Column(String, default="primary")

    notification_sender = relationship("User", foreign_keys=[notification_sender_id])
    notification_receiver = relationship("User", foreign_keys=[notification_receiver_id])