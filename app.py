from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
from loguru import logger
import pandas as pd
import datetime
from catboost import CatBoostClassifier
import os
from dotenv import load_dotenv
load_dotenv()
from schema.table_post import Post
from schema.database import SessionLocal, engine
from schema.schema import PostGet
from src import batch_load_sql
MODEL_PATH = os.environ["MODEL_PATH"]

# Загрузка обученной модели
def load_model():
    model_path = MODEL_PATH
    loaded_model = CatBoostClassifier()
    loaded_model.load_model(model_path)
    return loaded_model


logger.info("loading model")
model = load_model()


# Загрузка признаков
def load_features() -> pd.DataFrame:
    # Данные о пользователях
    users_features_query = 'SELECT * FROM aka_features_users'
    users_features = batch_load_sql(users_features_query)

    # Данные о постах
    posts_features_query = 'SELECT * FROM aka_features_posts'
    posts_features = batch_load_sql(posts_features_query)

    # Данные о тех постах, которые пользователи уже лайкали, для исключения их из прогноза
    liked_posts_query = '''SELECT DISTINCT user_id, post_id 
                            FROM public.feed_data 
                            WHERE action = 'like'
                            '''
    liked_posts = batch_load_sql(liked_posts_query)

    return users_features, posts_features, liked_posts


logger.info("loading features")
features = load_features()


# Подключение к бд через сессию
def get_db():
    with SessionLocal() as db:
        return db


app = FastAPI()


@app.get('/post/recommendations/', response_model=List[PostGet])
def recommended_posts(id: int, time: datetime.datetime, limit: int = 5, db: Session = Depends(get_db)):
    """
    id - id пользователя, для которого нужно сделать рекомендации,
    time - момент времени, в который их нужно сделать
    limit - количество постов, которые нужно выдать
    """
    user_features, post_features, liked_posts = features

    # Фильтруем данные для конкретного пользователя с переданным id
    user_features = user_features.loc[user_features['user_id'] == id].drop('user_id', axis=1)
    liked_posts = liked_posts.loc[liked_posts['user_id'] == id].drop('user_id', axis=1)

    # Фильтруем посты на предмет того, видел их конкретный пользователь или нет
    post_features = post_features[~post_features.post_id.isin(liked_posts.post_id.values)]

    # Фильтруем посты за последнюю неделю
    post_features_new = post_features[post_features.release_date > time + datetime.timedelta(days=-7)]

    # Выбираем "свежие" посты если такие есть, в противном случае - любые
    post_features = post_features_new if post_features_new.shape[0] > 20 else post_features
    post_features = post_features.drop('release_date', axis=1)

    # Сводим в один датафрейм
    user_features['key'] = 1
    post_features['key'] = 1
    df_pred = user_features.merge(post_features, on='key').drop("key", axis=1).set_index(['post_id'])
    df_pred['hour'] = time.hour

    # Делаем предсказания
    logger.info("make predictions")
    y_pred = model.predict_proba(df_pred)

    # Выбираем посты с максимальной вероятностью лайка
    df_pred['predictions'] = y_pred[:, 1]
    recommended_posts = df_pred.sort_values(by='predictions')[-limit:].index

    # Выгружаем данные этих постов
    logger.info("download posts info")
    results = db.query(Post) \
        .where(Post.id.in_(recommended_posts)) \
        .all()
    db.close()

    return results

