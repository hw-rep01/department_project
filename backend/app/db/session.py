from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    # بركة اتصال مُقاسة: افتراض SQLAlchemy (5 اتصالات + 10 فائض) صغير لأحمال الواجهة المتزامنة.
    # SQLite يستخدم NullPool الضمني فلا تُمرَّر إعدادات البركة.
    **(
        {}
        if settings.is_sqlite
        else {
            "pool_size": 20,
            "max_overflow": 20,
            "pool_recycle": 1800,
            "pool_timeout": 30,
        }
    ),
    future=True,
)


if settings.is_sqlite:

    @event.listens_for(engine, "connect")
    def _tune_sqlite(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # WAL يسمح بالقراءة أثناء الكتابة، وsynchronous=NORMAL يقلل مزامنة القرص مع بقائه آمناً
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-20000")  # ~20MB صفحة ذاكرة مؤقتة
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
