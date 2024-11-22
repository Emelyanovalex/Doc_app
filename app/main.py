import uuid
import uvicorn
import jwt
import asyncio
import sys
from fastapi import FastAPI, Depends, HTTPException, Path, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from app.models import Base, User
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.auth import oauth2_scheme, get_current_user, is_admin, SECRET_KEY, ALGORITHM
from app.database import engine, get_db
from app.crud import pwd_context, create_user
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import UserCreate
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
import logging
from app.websocket_manager import manager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SOSO",
    version="0.0.1",
    openapi_url="/openapi.json",
    docs_url="/",
)
origins = [
    "http://192.168.1.108:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.1.170:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

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
            birthdate=None,
            document="ADMIN_DOC",
            last_login=None,
        )
        db.add(admin_user)
        db.commit()
        print("Администратор успешно создан.")

@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Ожидание сообщений от клиента
            print(f"Received message from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

@app.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()  # Получение данных от клиента (опционально)
            print(f"Received message from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected from /ws/messages")


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    user_auth = auth.authenticate_user(db, form_data.username, form_data.password)

    if not user_auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = str(uuid.uuid4())  # Уникальный идентификатор сессии
    tokens = auth.create_tokens(data={"sub": user_auth.login}, session_id=session_id)

    crud.update_refresh_token(db, user_auth.id, tokens["refresh_token"])

    return {
        "id": user_auth.id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "role": user_auth.role,
        "token_type": "bearer",
    }


@app.post("/token/refresh")
def refresh_tokens(refresh_token: str, db: Session = Depends(get_db)) -> dict:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        login = payload.get("sub")
        session_id = payload.get("session_id")

        if login is None or session_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = crud.get_user_by_login(db, login=login)
    if not user or not crud.verify_refresh_token(db, user.id, refresh_token):
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    # Генерация новой пары токенов
    tokens = auth.create_tokens(data={"sub": login}, session_id=session_id)
    crud.update_refresh_token(db, user.id, tokens["refresh_token"])

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
    }


@app.post("/endpoint")
async def receive_data(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")

    if not data:
        raise HTTPException(status_code=400, detail="Request body is empty")

    if "login" not in data or "password" not in data:
        raise HTTPException(status_code=400, detail="Login and password are required")

    # Аутентификация пользователя
    user_auth = auth.authenticate_user(db, data["login"], data["password"])
    if not user_auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Генерация Access Token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": data["login"]}, expires_delta=access_token_expires
    )

    logger.info(f"Access token expires in: {access_token_expires}")
    logger.info(f"Login: {data['login']}")

    # Возвращаем данные без необходимости обновления токенов в базе
    return {
        "id": user_auth.id,
        "access_token": access_token,
        "expires_in_seconds": access_token_expires.total_seconds(),
        "role": user_auth.role,
    }


@app.get("/all_users", response_model=List[schemas.User])
def get_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="User authentication failed")

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


@app.get("/users", response_model=List[schemas.User])
def get_users(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    limit: int = 10,  # Ограничение по умолчанию
    offset: int = 0,  # Смещение по умолчанию
):
    # Проверяем текущего пользователя
    current_user = auth.get_current_user(token, db)
    auth.is_admin(current_user)  # Доступ только администраторам

    # Получаем пользователей с пагинацией
    users = crud.get_users_with_pagination(db=db, limit=limit, offset=offset)

    return users


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
        raise HTTPException(
            status_code=405,detail=f"User with ID {user_id} not found"
        )

    return {"detail": f"User with ID {user_id} successfully deleted"}


# @app.post("/messages", response_model=schemas.Message)
# def send_message(
#     message_data: schemas.Message,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     if current_user.id != message_data.message_sender_id:
#         raise HTTPException(
#             status_code=403, detail="You can only send messages as yourself"
#         )
#     new_message = crud.create_message(
#         db=db,
#         sender_id=current_user.id,
#         receiver_id=message_data.message_receiver_id,
#         message=message_data.message,
#         priority=message_data.priority,
#     )
#     return new_message

@app.post("/messages", response_model=schemas.Message)
async def send_message(
    message_data: schemas.Message,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.id != message_data.message_sender_id:
        raise HTTPException(
            status_code=403, detail="You can only send messages as yourself"
        )

    new_message = await crud.create_message_and_broadcast(
        db=db,
        sender_id=current_user.id,
        receiver_id=message_data.message_receiver_id,
        message=message_data.message,
        priority=message_data.priority,
    )
    return new_message

@app.post("/messages/{message_id}/read", response_model=schemas.Message)
def mark_as_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """
    Отметить сообщение как прочитанное.
    """
    message = crud.mark_message_as_read(db, message_id, current_user.id)
    return message


@app.get("/messages_by_id", response_model=list[schemas.Message])
def get_messages_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    messages_data = crud.get_messages_by_receiver_id(db, user_id)
    if not messages_data:
        raise HTTPException(status_code=404, detail="Messages not found")
    return messages_data


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


# @app.post("/notifications", response_model=schemas.Notification)
# def create_notification(
#     notification_data: schemas.Notification,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user),
# ):
#     if current_user.id != notification_data.notification_sender_id:
#         raise HTTPException(
#             status_code=403, detail="You can only send notifications as yourself"
#         )
#
#     # Передаем объект текущего пользователя (current_user), а не его ID
#     new_notification = crud.create_notification(
#         db=db,
#         sender_id=current_user.id,
#         receiver_id=notification_data.notification_receiver_id,
#         notification=notification_data.notification,
#         priority=notification_data.priority,
#     )
#     return new_notification
@app.post("/notifications", response_model=schemas.Notification)
async def create_notification(
    notification_data: schemas.Notification,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.id != notification_data.notification_sender_id:
        raise HTTPException(
            status_code=403, detail="You can only send notifications as yourself"
        )

    new_notification = await crud.create_notification_and_broadcast(
        db=db,
        sender_id=current_user.id,
        receiver_id=notification_data.notification_receiver_id,
        notification=notification_data.notification,
        priority=notification_data.priority,
    )
    return new_notification


@app.get("/notifications_by_id", response_model=list[schemas.Notification])
def get_notifications_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    notifications_data = crud.get_notification_by_receiver_id(db, user_id)
    if not notifications_data:
        raise HTTPException(status_code=404, detail="Notifications not found")
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
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")