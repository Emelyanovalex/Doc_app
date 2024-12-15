from typing import Any, Union
from fastapi import Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.crud import pwd_context
from app.database import get_db
from app import crud
from datetime import datetime, timedelta
import os
from fastapi.security import OAuth2PasswordBearer
from app.exceptions import InvalidCredentialsException, ForbiddenException
# Константы для генерации токенов
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  # Секретный ключ для шифрования JWT токенов.
ALGORITHM = os.getenv("ALGORITHM", "HS256")          # Алгоритм шифрования JWT токенов.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))  # Время жизни access-токена в минутах.
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 43200))  # 30 дней
# Определяем схему авторизации через токен
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def authenticate_user(db: Session, login: str, password: str) -> Union[None, Any]:
    """
    Проверяет учетные данные пользователя.

    Аргументы:
        db (Session): Сессия базы данных.
        login (str): Логин пользователя.
        password (str): Пароль пользователя.

    Возвращает:
        Union[None, Any]: Объект пользователя, если аутентификация успешна, иначе None.
    """
    user = crud.get_user_by_login(db, login)
    if not user or not pwd_context.verify(password, user.pas):
        return None
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user

def check_user_session_token(db: Session, id: int, token: str) -> bool:
    """
    Проверяет соответствие токена пользователя.

    Аргументы:
        db (Session): Сессия базы данных.
        id (int): ID пользователя.
        token (str): Токен для проверки.

    Возвращает:
        bool: True, если токен соответствует, иначе False.
    """
    user = crud.get_user(db, id)
    return user and token == user.token

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Создаёт access-токен.

    Аргументы:
        data (dict): Данные для кодирования в токене.
        expires_delta (timedelta, optional): Время действия токена. По умолчанию используется ACCESS_TOKEN_EXPIRE_MINUTES.

    Возвращает:
        str: Закодированный JWT access-токен.
    """
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Any:
    """
    Извлекает текущего пользователя на основе токена.

    Аргументы:
        token (str): Токен доступа пользователя.
        db (Session): Сессия базы данных.

    Возвращает:
        Any: Объект пользователя, если аутентификация успешна.

    Исключения:
        HTTPException: Если токен недействителен или пользователь не найден.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        exp = payload.get("exp")

        if login is None or datetime.now().timestamp() > exp:
            raise InvalidCredentialsException
    except JWTError:
        raise InvalidCredentialsException

    user = crud.get_user_by_login(db, login=login)
    if user is None:
        raise InvalidCredentialsException

    return user

def is_admin(user: Any) -> None:
    """
    Проверяет, является ли пользователь администратором.

    Аргументы:
        user (Any): Объект пользователя.

    Исключения:
        HTTPException: Если пользователь не является администратором.
    """
    if user.role != "admin":
        raise ForbiddenException
