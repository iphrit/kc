from database import Base, SessionLocal
from sqlalchemy import Table, Column, Integer, String, func, TIMESTAMP, ForeignKey
from table_user import User
from table_post import Post
from sqlalchemy.orm import relationship

class Feed(Base):
    __tablename__ = "feed_action"
    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    action = Column(String)
    time = Column(TIMESTAMP)
    user = relationship("User")
    post = relationship("Post")