from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class StatusEnum(str, Enum):
    """
    Перечисление статусов для сообщений и уведомлений.
    """
    UNREAD = "unread"
    READ = "read"

class UserBase(BaseModel):
    """
    Базовая схема пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        name (str): Имя пользователя.
        login (str): Логин пользователя.
        office (Optional[str]): Офис, к которому относится пользователь.
        birthdate (Optional[datetime]): Дата рождения пользователя.
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

class MessageCreate(BaseModel):
    """
    Схема для создания нового сообщения.

    Атрибуты:
        message (str): Текст сообщения.
        message_sender (int): ID отправителя.
        message_receiver (int): ID получателя.
        message_status (str): Статус сообщения.
    """
    message: str
    message_sender: int
    message_receiver: int
    message_status: StatusEnum = StatusEnum.UNREAD


class MessageStatus(BaseModel):
    """
    Схема для создания нового сообщения.

    Атрибуты:
        message_sender (int): ID отправителя.
        message_receiver (int): ID получателя.
        message_status (str): Статус сообщения.
    """
    message_sender: int
    message_receiver: int
    message_status: StatusEnum = StatusEnum.UNREAD


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
       message_status: Статус прочитанности сообщения.
    """
    id: int
    message: str
    message_time: datetime
    message_sender: int
    message_receiver: int
    message_status: StatusEnum

    class Config:
        from_attributes = True


# Схемы для задач
class TaskCreate(BaseModel):
    """
       Схема сообщения.

    Атрибуты:
        id (int): Уникальный идентификатор задачи.
        task_name (str): Название задачи.
        task_content (str): Содержимое задачи.
        task_executor (int): ID исполнителя задачи, ссылка на таблицу users.
        task_director (int): ID директора задачи, ссылка на таблицу users.
        task_progress (str): Прогресс выполнения задачи, по умолчанию "in_progress".
        task_date (datetime): Дата создания задачи.
        task_deadline (datetime): Дедлайн задачи.
        task_status (str): Статус задачи.
        task_priority (str): Приоритет задачи.
        task_executor_role (int): Роль исполнителя задачи.
    """
    task_name: str
    task_content: str
    task_executor: int
    task_director: int
    task_progress: Optional[str] = "in_progress"
    task_date: Optional[datetime] = Field(default_factory=datetime.now)
    task_deadline: Optional[datetime]
    task_status: str
    task_priority: Optional[str]
    task_executor_role: int

class TaskResponse(TaskCreate):
    id: int

    class Config:
        from_attributes = True
