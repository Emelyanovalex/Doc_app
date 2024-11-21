import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Path, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.models import Base, User
from sqlalchemy.orm import Session
from app import crud, schemas, auth, models
from app.auth import oauth2_scheme, get_current_user, is_admin
from app.database import engine, get_db
from app.crud import pwd_context, create_user
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import UserCreate



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

# [{},{}....]
# Регистрация пользователей
# @app.post("/create_user", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     # Проверка на существование пользователя с таким же логином
#     db_user = crud.get_user_by_login(db, login=user.login)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Login already registered")
#
#     # Создание нового пользователя
#     new_user = crud.create(db=db, user=user)
#     return new_user


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    user_auth = auth.authenticate_user(db, form_data.username, form_data.password)  # form_data.username содержит login

    if not user_auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user_auth.login}, expires_delta=access_token_expires)

    # Обновляем токен пользователя в базе данных
    updated_user = crud.update_user_token(db, user_auth.id, access_token)

    return {
        "id": updated_user.id,
        "access_token": updated_user.token,  # Возвращаем токен из базы
        "role": updated_user.role,
        "token_type": "bearer",
    }


@app.post("/endpoint")
async def receive_data(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    if not data:
        raise HTTPException(status_code=400)

    user_auth = auth.authenticate_user(db, data["login"], data["password"])
    if not user_auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": data["login"]}, expires_delta=access_token_expires)

    print(access_token_expires)

    print("login:", data["login"])
    updated_user = crud.update_user_token(db, user_auth.id, access_token)

    return {
        "id": updated_user.id,
        "token": updated_user.token,  # Возвращаем токен из базы
        "time" : access_token_expires,
        "role": updated_user.role
    }

@app.get("/users", response_model=list[schemas.User])
def get_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = auth.get_current_user(token, db)  # Проверяем токен и извлекаем пользователя
    if not user:
        raise HTTPException(status_code=401, detail="User authentication failed")


    users = crud.get_all_users(db=db)
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


@app.post("/messages/", response_model=schemas.Message)
def send_message(
    message_data: schemas.Message,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_message = crud.create_message(
        db=db,
        sender_id=current_user.id,
        receiver_id=message_data.message_receiver_id,
        message=message_data.message,
        priority=message_data.priority,
    )
    return new_message


@app.get("/all_messages", response_model=list[schemas.Message])
def get_all_users_messages(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    messages = crud.get_messages_by_user(db, current_user.id)
    return messages


@app.post("/notifications", response_model=schemas.Notification)
def create_notification(
    notification_data: schemas.Notification,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    if current_user.id != notification_data.notification_sender:
        raise HTTPException(
            status_code=403, detail="You can only send notifications as yourself"
        )

    # Передаем объект текущего пользователя (current_user), а не его ID
    new_notification = crud.create_notification(
        db=db,
        sender_id=current_user.id,
        receiver_id=notification_data.notification_receiver,
        notification=notification_data.notification,
        priority=notification_data.priority,
    )
    return new_notification



@app.get("/notifications", response_model=list[schemas.Notification])
def get_user_notifications(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    notifications = crud.get_user_notifications(db, user_id=current_user.id)
    return notifications


@app.get("/notifications_by_id", response_model=list[schemas.Notification])
def get_notifications_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    notifications_data = crud.get_notification_by_receiver_id(db, user_id)
    if not notifications_data:
        raise HTTPException(status_code=404, detail="Notifications not found")
    return notifications_data


if __name__ == "__main__":
    create_admin()
    uvicorn.run("main:app", host="192.168.1.170", port=5173, log_level="info")