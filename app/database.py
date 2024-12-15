from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# URL подключения к базе данных
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost/dbname")

# Создание движка базы данных
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Настройка сессии для взаимодействия с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

def get_db():
    """
    Предоставляет сессию базы данных для выполнения операций.

    Использование:
        Сессия предоставляется через зависимость (Depends) в FastAPI.

    Пример:
        db: Session = Depends(get_db)

    Возвращает:
        Generator: Генератор, предоставляющий сессию базы данных и закрывающий её по завершении.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
