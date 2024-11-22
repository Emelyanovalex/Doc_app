from typing import Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.crud import pwd_context
from app.database import get_db
from app import  crud
from datetime import datetime, timedelta
import os
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_tokens(data: dict, session_id: str):
    # Генерация access и refresh токенов
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    data.update({"session_id": session_id})

    access_token = create_access_token(data, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "refresh_token": refresh_token}



def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
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


def authenticate_user(db: Session, login: str, password: str):
    user = crud.get_user_by_login(db, login)
    if not user or not pwd_context.verify(password, user.pas):
        return None
    user.last_login = datetime.now()
    db.commit()
    db.refresh(user)
    return user


def check_user_session_token(db: Session, id: int, token: str) -> bool | Any:
    user = crud.get_user(db, id)
    if not user:
        return False

    return token == user.token


def is_admin(user: Any):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: Admin role required.",
        )