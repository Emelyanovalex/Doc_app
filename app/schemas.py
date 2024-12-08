from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    UNREAD = "unread"
    READ = "read"


class GetUserMessagesRequest(BaseModel):
    user_id: int


# Схемы для пользователя
class UserBase(BaseModel):
    """
    Базовая схема пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        name (str): Имя пользователя.
        login (str): Логин пользователя.
        office (Optional[str]): Офис, к которому относится пользователь.
        birthdate (Optional[datetime]): Дата рождения пользователя.
        document (Optional[str]): Документ пользователя.
        role (Optional[str]): Роль пользователя (по умолчанию "user").
        token (Optional[str]): Токен доступа (опционально).
        last_login (Optional[datetime]): Дата и время последнего входа.
    """
    id: int
    name: str
    login: str
    office: Optional[str] = Field(None, description="Офис пользователя")
    birthdate: Optional[datetime] = Field(None, description="Дата рождения пользователя")
    role: Optional[str] = Field("user", description="Роль пользователя (по умолчанию 'user')")
    token: Optional[str] = Field(None, description="Токен доступа")
    last_login: Optional[datetime] = Field(None, description="Последний вход пользователя")


class UserCreate(BaseModel):
    """
    Схема для создания нового пользователя.

    Атрибуты:
        name (str): Имя пользователя.
        login (str): Логин пользователя.
        pas (str): Пароль пользователя.
        office (Optional[str]): Офис пользователя (опционально).
        birthdate (Optional[datetime]): Дата рождения (опционально).
        document (Optional[str]): Документ пользователя (опционально).
        role (Optional[str]): Роль пользователя (по умолчанию "user").
    """
    name: str
    login: str
    pas: str
    office: Optional[str] = None
    birthdate: Optional[datetime] = None
    role: Optional[str] = "user"


class User(UserBase):
    """
    Полная схема пользователя с атрибутами из базы данных.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
    """
    id: int

    class Config:
        from_attributes = True


# Схемы для сообщений
class Message(BaseModel):
    """
    Схема сообщения.

    Атрибуты:
        id (int): Уникальный идентификатор сообщения.
        message (str): Текст сообщения.
        message_time (datetime): Время отправки сообщения.
        message_sender_id (int): ID отправителя.
        message_receiver_id (int): ID получателя.
        is_read (bool): Статус прочитанности сообщения.
        priority (PriorityEnum): Приоритет сообщения.
    """
    id: int
    message: str
    message_time: datetime
    message_sender: int = Field(..., description="ID отправителя")
    message_receiver: int = Field(..., description="ID получателя")
    message_status: StatusEnum = Field(StatusEnum.UNREAD, description="Статус сообщения")

    class Config:
        from_attributes = True


# Схемы для уведомлений
class Notification(BaseModel):
    """
    Схема уведомления.

    Атрибуты:
        id (int): Уникальный идентификатор уведомления.
        notification (str): Текст уведомления.
        notification_time (datetime): Время отправки уведомления.
        notification_sender_id (int): ID отправителя уведомления.
        notification_receiver_id (int): ID получателя уведомления.
        is_read (bool): Статус прочитанности уведомления.
        priority (PriorityEnum): Приоритет уведомления.
    """
    id: int
    notification: str
    notification_time: datetime
    notification_sender: int = Field(..., description="ID отправителя уведомления")
    notification_receiver: int = Field(..., description="ID получателя уведомления")
    notification_status: StatusEnum = Field(StatusEnum.UNREAD, description="Статус уведомления")

    class Config:
        from_attributes = True
