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

class Task(Base):
    """
    Модель задачи.

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
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255), nullable=False)
    task_content = Column(String, nullable=False)
    task_executor = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    task_director = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    task_progress = Column(String(50), default="in_progress", nullable=False)
    task_date = Column(DateTime, default=func.now(), nullable=False)
    task_deadline = Column(DateTime)
    task_status = Column(String(50), nullable=False)
    task_priority = Column(String(50))
    task_executor_role = Column(Integer, nullable=False)


