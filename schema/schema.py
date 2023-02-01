import datetime
from typing import Optional

from pydantic import BaseModel, Field   # импортировали нужные библиотеки

class UserGet(BaseModel):   # В SQLAlchemy был очень похожий
    id: int
    gender: int
    age: int
    country: str
    city: str
    exp_group: int
    os: str
    source: str

    class Config:
        orm_mode = True

class PostGet(BaseModel):
    id: int
    text: str
    topic: str

    class Config:
        orm_mode = True

class FeedGet(BaseModel):
    post_id: int
    user_id: int
    time: datetime.datetime
    action: str
    user: UserGet
    post: PostGet

    class Config:
        orm_mode = True