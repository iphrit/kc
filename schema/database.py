from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

POSTGRES_DB_URL = os.environ["POSTGRES_DB_URL"]

engine = create_engine(POSTGRES_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()