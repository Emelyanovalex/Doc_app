from typing import Any, Union
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.crud import pwd_context
from app.database import get_db
from app import crud
from datetime import datetime, timedelta
import os
from fastapi.security import OAuth2PasswordBearer

# Константы для генерации токенов
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", 1440))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Создает access-токен.

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

def create_refresh_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Создает refresh-токен.

    Аргументы:
        data (dict): Данные для кодирования в токене.
        expires_delta (timedelta, optional): Время действия токена. По умолчанию используется REFRESH_TOKEN_EXPIRE_MINUTES.

    Возвращает:
        str: Закодированный JWT refresh-токен.
    """
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_tokens(data: dict, session_id: str) -> dict:
    """
    Создает пару токенов (access и refresh).

    Аргументы:
        data (dict): Данные для кодирования в токенах.
        session_id (str): Уникальный идентификатор сессии.

    Возвращает:
        dict: Словарь с access- и refresh-токенами.
    """
    data.update({"session_id": session_id})
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data)
    }

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Any:
    """
    Получает текущего пользователя по access-токену.

    Аргументы:
        token (str): Токен для проверки.
        db (Session): Сессия базы данных.

    Возвращает:
        Any: Объект пользователя.

    Исключения:
        HTTPException: Если токен недействителен или пользователь не найден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        exp = payload.get("exp")

        if login is None or datetime.now().timestamp() > exp:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_login(db, login=login)
    if user is None:
        raise credentials_exception

    return user

def authenticate_user(db: Session, login: str, password: str) -> Union[None, Any]:
    """
    Проверяет учетные данные пользователя.

    Аргументы:
        db (Session): Сессия базы данных.
        login (str): Логин пользователя.
        password (str): Пароль пользователя.

    Возвращает:
        Union[None, Any]: Объект пользователя или None, если аутентификация не удалась.
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

def is_admin(user: Any) -> None:
    """
    Проверяет, является ли пользователь администратором.

    Аргументы:
        user (Any): Объект пользователя.

    Исключения:
        HTTPException: Если пользователь не является администратором.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль администратора.",
        )