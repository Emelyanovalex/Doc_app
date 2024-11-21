from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    id: int
    name: str
    login: str
    office: Optional[str] = None
    birthdate: Optional[datetime] = None
    document: Optional[str] = None
    role: Optional[str] = "user"
    token: Optional[str] = None  # Поле для токена
    last_login: Optional[datetime] = None


class UserCreate(UserBase):
    pas: str  # Пароль при создании

class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class Message(BaseModel):
    id: int
    message_time: datetime
    message: str
    message_sender_id: int
    message_receiver_id: int
    is_read: bool
    priority: str

    class Config:
        from_attributes = True


class Notification(BaseModel):
    id: int
    notification: str
    notification_time: datetime
    notification_sender: int  # Ожидаем ID отправителя, а не объект
    notification_receiver: int  # Ожидаем ID получателя
    is_read: bool
    priority: str

    class Config:
        from_attributes = True