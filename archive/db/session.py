from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from config import defaults as config

engine = create_engine(config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True,pool_recycle=1500)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)