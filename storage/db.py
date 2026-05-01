from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from config import DATABASE_URL

_engine = None
_SessionFactory = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine

def init_db():
    Base.metadata.create_all(get_engine())

def get_session():
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(get_engine())
    return _SessionFactory()
