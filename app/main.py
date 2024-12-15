import datetime
import uvicorn
import logging

from fastapi import FastAPI, Depends, Path, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.exceptions import InvalidCredentialsException, BadRequestException, MethodNotAllowedException, \
    ForbiddenException, UserNotFoundException, InternalServerErrorException
from app.models import Base, User
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.auth import oauth2_scheme, get_current_user, is_admin
from app.database import engine, get_db
from app.crud import pwd_context, create_user, save_message
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import UserCreate
from app.websocket_manager import manager

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
        raise InvalidCredentialsException

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
        raise BadRequestException

    if not data:
        raise BadRequestException

    if "login" not in data or "password" not in data:
        raise BadRequestException

    # Аутентификация пользователя
    user_auth = auth.authenticate_user(db, data["login"], data["password"])
    if not user_auth:
        raise InvalidCredentialsException

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
        raise MethodNotAllowedException

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
        raise ForbiddenException

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
        raise UserNotFoundException


@app.post("/message_status")
async def update_all_messages_to_read(
        token: str = Depends(oauth2_scheme),  # Извлечение токена из заголовка
        db: Session = Depends(get_db)
):
    """
    Обновляет статус всех сообщений текущего пользователя на "read".

    Аргументы:
        token (str): JWT токен текущего пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        JSONResponse: Сообщение об успехе и количество обновлённых сообщений.
    """
    # Аутентификация текущего пользователя
    current_user = auth.get_current_user(token, db)

    try:
        # Обновляем статус всех сообщений, где текущий пользователь является получателем
        updated_rows = db.query(models.Message).filter(
            models.Message.message_receiver == current_user.id,
            models.Message.message_status == "unread"  # Фильтруем только непрочитанные сообщения
        ).update({"message_status": "read"})

        db.commit()  # Сохраняем изменения в базе данных

        return JSONResponse(content={"detail": "Message status updated successfully."})
    except Exception as error:
        raise InternalServerErrorException


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


if __name__ == "__main__":
    create_admin()
    # uvicorn.run("main:app", host="192.168.1.107", port=5173, log_level="info")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")