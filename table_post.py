from database import Base, SessionLocal
from sqlalchemy import Table, Column, Integer, String

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    topic = Column(String)

