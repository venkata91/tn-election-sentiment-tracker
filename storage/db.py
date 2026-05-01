from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.models import Base
from config import DATABASE_URL

_engine = None
_Session = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
    return _engine

def init_db():
    Base.metadata.create_all(get_engine())

def get_session():
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine())
    return _Session()
