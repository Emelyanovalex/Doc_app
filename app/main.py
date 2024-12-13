import datetime
import uvicorn
import logging

from fastapi import FastAPI, Depends, Path, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.models import Base, User
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.auth import oauth2_scheme, get_current_user, is_admin
from app.database import engine, get_db
from app.crud import pwd_context, create_user, save_message
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import UserCreate
from typing import List, Optional
from app.websocket_manager import manager
from app.exceptions import INVALID_CREDENTIALS, BAD_REQUEST, METHOD_NOT_ALLOWED, FORBIDDEN, MESSAGE_NOT_FOUND, \
    NOTIFICATION_NOT_FOUND, USER_NOT_FOUND

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Documentatition",
    version="0.1",
    openapi_url="/openapi.json",
    docs_url="/",
)
origins = [
    "http://192.168.1.107:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

active_connections = []

def create_admin():
    # Инициализация базы данных (создание таблиц, если их еще нет)
    Base.metadata.create_all(bind=engine)

    # Данные администратора
    admin_login = "admin"
    admin_password = "admin123"  # Замените на более надежный пароль

    with Session(engine) as db:
        # Проверяем, существует ли пользователь с логином admin
        existing_admin = db.query(User).filter_by(login=admin_login).first()
        if existing_admin:
            print("Администратор уже существует.")
            return

        # Хэшируем пароль и создаем запись администратора
        hashed_password = pwd_context.hash(admin_password)
        admin_user = User(
            name="Administrator",
            login=admin_login,
            pas=hashed_password,
            office="HQ",
            role="admin",
            birthdate=datetime.datetime.now(),
            last_login=datetime.datetime.now(),
        )
        db.add(admin_user)
        db.commit()
        print("Администратор успешно создан.")

@app.websocket("/items/{item_id}/ws")
async def websocket_endpoint(websocket: WebSocket, item_id: int):
    """
    Эндпоинт WebSocket для взаимодействия с клиентами в рамках конкретного item_id.

    Аргументы:
        websocket (WebSocket): Соединение WebSocket.
        item_id (int): Идентификатор элемента.
    """
    # Подключение клиента к WebSocket
    await manager.connect(websocket, item_id)
    print(f"Client connected to item {item_id}")

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            print(f"Received from item {item_id}: {data}")

            # Рассылаем сообщение всем подключённым клиентам внутри группы item_id
            await manager.broadcast(f"Item {item_id}: {data}", item_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, item_id)
        print(f"Client disconnected from item {item_id}")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_auth = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user_auth:
        raise INVALID_CREDENTIALS

    access_token = auth.create_access_token(data={"sub": user_auth.login})

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/endpoint")
async def receive_data(request: Request, db: Session = Depends(get_db)):
    """
    Эндпоинт для аутентификации пользователя и возврата непрочитанных сообщений.

    Аргументы:
        request (Request): Объект запроса от клиента.
        db (Session): Сессия базы данных.

    Возвращает:
        dict: Информация о пользователе, токене и непрочитанных сообщениях.
    """
    try:
        data = await request.json()
    except Exception:
        raise BAD_REQUEST

    if not data:
        raise BAD_REQUEST

    if "login" not in data or "password" not in data:
        raise BAD_REQUEST

    # Аутентификация пользователя
    user_auth = auth.authenticate_user(db, data["login"], data["password"])
    if not user_auth:
        raise INVALID_CREDENTIALS

    # Генерация Access Token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": data["login"]}, expires_delta=access_token_expires
    )

    # Получение непрочитанных сообщений с именами отправителей
    unread_messages = crud.get_unread_messages_with_sender_name(db, user_auth.id)

    # Логирование
    logger.info(f"Access token expires in: {access_token_expires}")
    logger.info(f"Login: {data['login']}")

    # Возвращаем данные
    return [
        {
        "id": user_auth.id,
        "name": user_auth.name,
        "token": access_token,
        "role": user_auth.role,
        "ttl": access_token_expires.total_seconds(),
        "unread_messages": unread_messages,
    }
]

@app.get("/all_users", response_model=List[schemas.User])
def get_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)
    if not current_user:
        raise INVALID_CREDENTIALS

    # Проверяем, что текущий пользователь является администратором
    auth.is_admin(current_user)

    # Получаем всех пользователей
    users = crud.get_all_users(db=db)

    # Генерация токенов для каждого пользователя
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    users_with_tokens = []
    for user in users:
        access_token = auth.create_access_token(
            data={"sub": user.login}, expires_delta=access_token_expires
        )
        user_data = user.__dict__.copy()
        user_data["token"] = access_token  # Вставляем сгенерированный токен
        users_with_tokens.append(user_data)

    return users_with_tokens

@app.get("/users/filter", response_model=List[schemas.User])
def filter_users(
    name: Optional[str] = None,
    role: Optional[str] = None,
    office: Optional[str] = None,
    sort_by: str = "id",
    sort_order: str = "asc",
    limit: int = 10,
    offset: int = 0,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Фильтрует и сортирует пользователей по имени, роли, офису и другим параметрам.

    Аргументы:
        name (Optional[str]): Фильтр по имени (подстрока).
        role (Optional[str]): Фильтр по роли.
        office (Optional[str]): Фильтр по офису (подстрока).
        sort_by (str): Поле для сортировки. По умолчанию "id".
        sort_order (str): Порядок сортировки ("asc" или "desc"). По умолчанию "asc".
        limit (int): Максимальное количество записей. По умолчанию 10.
        offset (int): Смещение для пагинации. По умолчанию 0.
        token (str): Токен доступа для авторизации.
        db (Session): Сессия базы данных.

    Возвращает:
        List[schemas.User]: Список отфильтрованных и отсортированных пользователей с токенами.
    """
    current_user = auth.get_current_user(token, db)
    auth.is_admin(current_user)  # Доступ только администраторам

    users = crud.filter_users(
        db=db, name=name, role=role, office=office, sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset
    )

    # Добавляем токен каждому пользователю
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    users_with_tokens = []
    for user in users:
        access_token = auth.create_access_token(
            data={"sub": user.login}, expires_delta=access_token_expires
        )
        user_data = user.__dict__.copy()
        user_data["token"] = access_token
        users_with_tokens.append(user_data)

    return users_with_tokens

@app.get("/users", response_model=List[schemas.User])
def get_users(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Возвращает список всех пользователей с токенами и поддержкой пагинации.

    Аргументы:
        limit (int): Максимальное количество записей. По умолчанию 10.
        offset (int): Смещение для пагинации. По умолчанию 0.
        db (Session): Синхронная сессия базы данных.

    Возвращает:
        List[schemas.User]: Список пользователей с токенами.
    """
    users = db.query(models.User).offset(offset).limit(limit).all()

    # Добавляем токен каждому пользователю
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    users_with_tokens = []
    for user in users:
        access_token = auth.create_access_token(
            data={"sub": user.login}, expires_delta=access_token_expires
        )
        user_data = user.__dict__.copy()
        user_data["token"] = access_token
        users_with_tokens.append(user_data)

    return users_with_tokens

@app.post("/admin/register_user", response_model=schemas.User, status_code=201)
def admin_register_user(
    user_data: UserCreate,
    current_user: schemas.User = Depends(get_current_user),  # Текущий пользователь
    db: Session = Depends(get_db),
):
    # Проверяем, является ли текущий пользователь администратором
    is_admin(current_user)

    # Регистрируем нового пользователя
    new_user = create_user(db, user_data)

    return new_user

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int = Path(..., title="ID пользователя для удаления"),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)
    auth.is_admin(current_user)  # Проверяем, что это администратор

    # Удаляем пользователя
    result = crud.delete_user(db, user_id)
    if not result:
        raise METHOD_NOT_ALLOWED

    return {"detail": f"Пользователь ID {user_id} успешно удален"}


@app.post("/message_row", response_model=dict)
async def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Эндпоинт для отправки сообщения.

    Аргументы:
        message_data (MessageCreate): Данные сообщения.
        db (Session): Сессия базы данных.
        current_user (User): Текущий пользователь.

    Возвращает:
        dict: Имя отправителя и идентификатор сообщения.
    """
    # Проверяем, что текущий пользователь отправляет сообщение от своего имени
    if current_user.id != message_data.message_sender:
        raise FORBIDDEN

    # Сохраняем сообщение
    db_message = await save_message(
        db=db,
        message_sender=message_data.message_sender,
        message_receiver=message_data.message_receiver,
        message=message_data.message,
        message_status=message_data.message_status,
    )

    # Получаем имя отправителя
    sender = db.query(models.User).filter(models.User.id == message_data.message_sender).first()

    if sender:
        return {
            "message_id": db_message.id,
            "name": sender.name,
        }
    else:
        raise USER_NOT_FOUND


@app.post("/message_status")
async def receive_message_status(request: Request, db: Session = Depends(get_db)):
    """
    Обновляет статус сообщений между отправителем и получателем.

    Аргументы:
        request (Request): Запрос с данными для обновления статуса.
        db (Session): Сессия базы данных.

    Возвращает:
        JSONResponse: Сообщение об успехе.
    """
    data = await request.json()

    try:
        # Обновляем статус сообщений в таблице messages
        db.query(models.Message).filter(
            models.Message.message_receiver == data['message_receiver'],
            models.Message.message_sender == data['message_sender']
        ).update({"message_status": data['message_status']})

        db.commit()

        # Возвращаем успешное сообщение вне зависимости от результата
        return JSONResponse(content={"detail": "Message status updated successfully."})
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Database error: {error}")

@app.post("/messages/{message_id}/read", response_model=schemas.Message)
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """
    Эндпоинт для отметки сообщения как прочитанного.

    Аргументы:
        message_id (int): ID сообщения.
        db (Session): Сессия базы данных.
        current_user (schemas.User): Текущий авторизованный пользователь.

    Возвращает:
        schemas.Message: Обновлённое сообщение.
    """
    return crud.mark_message_as_read(db, message_id, current_user.id)

@app.get("/messages_by_id", response_model=list[schemas.Message])
def get_messages_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    messages_data = crud.get_messages_by_receiver_id(db, user_id)
    if not messages_data:
        raise MESSAGE_NOT_FOUND
    return messages_data

@app.post("/messages")
async def get_all_users_and_targeted_messages(
    token: str = Depends(oauth2_scheme),  # Получение токена из заголовка Authorization
    db: Session = Depends(get_db)
):
    """
    Эндпоинт для получения информации обо всех пользователях (кроме текущего) и их сообщений,
    которые отправлены текущему пользователю или отправлены текущим пользователем.

    Аргументы:
        token (str): JWT токен для аутентификации пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        list: Список пользователей с их сообщениями.
    """
    # Аутентификация текущего пользователя
    current_user = auth.get_current_user(token, db)

    # Получаем всех пользователей, кроме текущего
    other_users = db.query(models.User).filter(models.User.id != current_user.id).all()

    # Формируем данные для ответа
    users_with_messages = []
    for user in other_users:
        # Получаем только сообщения между текущим пользователем и этим пользователем
        user_messages = db.query(models.Message).filter(
            ((models.Message.message_sender == current_user.id) & (models.Message.message_receiver == user.id)) |
            ((models.Message.message_sender == user.id) & (models.Message.message_receiver == current_user.id))
        ).all()

        # Форматируем сообщения
        formatted_messages = [
            {
                "message_id": msg.id,
                "message_sender": msg.message_sender,
                "message_receiver": msg.message_receiver,
                "message_time": msg.message_time.strftime('%d-%m-%Y %H:%M:%S'),
                "message": msg.message,
                "message_status": msg.message_status,
            }
            for msg in user_messages
        ]

        users_with_messages.append({
            "id": user.id,
            "name": user.name,
            "office": user.office,
            "last_login": user.last_login.strftime('%d-%m-%Y %H:%M:%S') if user.last_login else None,
            "last_messages": formatted_messages
        })

    return users_with_messages

@app.get("/all_messages", response_model=list[schemas.Message])
def get_all_users_messages(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    messages = crud.get_messages_by_user(db, current_user.id)
    return messages

@app.get("/messages", response_model=List[schemas.Message])
def get_messages(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    limit: int = 10,  # Ограничение по умолчанию
    offset: int = 0,  # Смещение по умолчанию
):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)

    # Получаем сообщения с пагинацией
    messages = crud.get_messages_with_pagination(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )

    return messages

@app.post("/notifications", response_model=schemas.Notification)
async def create_notification(
    notification_data: schemas.Notification,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.id != notification_data.notification_sender_id:
        raise FORBIDDEN

    new_notification = await crud.create_notification_and_broadcast(
        db=db,
        sender=current_user.id,
        receiver=notification_data.notification_receiver_id,
        notification=notification_data.notification,
    )
    return new_notification

@app.get("/notifications_by_id", response_model=list[schemas.Notification])
def get_notifications_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    notifications_data = crud.get_notification_by_receiver_id(db, user_id)
    if not notifications_data:
        raise NOTIFICATION_NOT_FOUND
    return notifications_data

@app.get("/all_notifications", response_model=list[schemas.Notification])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    notifications = crud.get_user_notifications(db, user_id=current_user.id)
    return notifications

@app.get("/notifications", response_model=List[schemas.Notification])
def get_notifications(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    limit: int = 10,  # Ограничение по умолчанию
    offset: int = 0,  # Смещение по умолчанию
):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)

    # Получаем уведомления с пагинацией
    notifications = crud.get_notifications_with_pagination(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )
    return notifications


if __name__ == "__main__":
    create_admin()
    uvicorn.run("main:app", host="192.168.1.107", port=5173, log_level="info")
    # uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")