from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# Перечисление для приоритета
class PriorityEnum(str, Enum):
    PRIMARY = "primary"
    DANGER = "danger"


# Схемы пользователя
class UserBase(BaseModel):
    id: int
    name: str
    login: str
    office: Optional[str] = Field(None, description="Офис пользователя")
    birthdate: Optional[datetime] = Field(None, description="Дата рождения пользователя")
    document: Optional[str] = Field(None, description="Документ пользователя")
    role: Optional[str] = Field("user", description="Роль пользователя (по умолчанию 'user')")
    token: Optional[str] = Field(None, description="Токен доступа")
    last_login: Optional[datetime] = Field(None, description="Последний вход пользователя")


class UserCreate(BaseModel):
    name: str
    login: str
    pas: str  # Пароль при создании
    office: Optional[str] = None
    birthdate: Optional[datetime] = None
    document: Optional[str] = None
    role: Optional[str] = "user"


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# Схемы сообщений
class Message(BaseModel):
    id: int
    message: str
    message_time: datetime
    message_sender_id: int = Field(..., description="ID отправителя")
    message_receiver_id: int = Field(..., description="ID получателя")
    is_read: bool = Field(False, description="Статус прочитанности")
    priority: PriorityEnum = Field(PriorityEnum.PRIMARY, description="Приоритет сообщения")

    class Config:
        from_attributes = True


# Схемы уведомлений
class Notification(BaseModel):
    id: int
    notification: str
    notification_time: datetime
    notification_sender_id: int = Field(..., description="ID отправителя уведомления")
    notification_receiver_id: int = Field(..., description="ID получателя уведомления")
    is_read: bool = Field(False, description="Статус прочитанности уведомления")
    priority: PriorityEnum = Field(PriorityEnum.PRIMARY, description="Приоритет уведомления")

    class Config:
        from_attributes = True
