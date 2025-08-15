import os

import pytest
from api.main import create_app  # type: ignore
from db.models import Follow, Like, Tweet, User  # type: ignore
from db.models import db as _db  # type: ignore
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy


@pytest.fixture()
def app() -> Flask:
    """
    Фикстура экземпляра Flask-приложения для тестирования
    """
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg2://admin:admin@db:5432/twitter_test",
        "UPLOAD_FOLDER": "tests/test_uploads"
    }
    _app = create_app(test_config)

    with _app.app_context():
        os.makedirs(_app.config["UPLOAD_FOLDER"], exist_ok=True)
        _db.create_all()

        users_test = [
            User(name="Test User", api_key="test-api-key"),
            User(name="Test User_2", api_key="api-key_2"),
            User(name="Test User_3", api_key="api-key_3"),
        ]
        for user_test in users_test:
            if user_test not in _db.session.query(User).all():
                _db.session.add(user_test)
                _db.session.commit()

        tweets_test = [
            Tweet(user_id=1, content="Hello!", medias_ids=[], count_likes=0),
            Tweet(user_id=2, content="Hello, Friends!", medias_ids=[], count_likes=1)
        ]
        _db.session.bulk_save_objects(tweets_test)
        _db.session.commit()

        like = Like(user_id=1, tweet_id=2)
        _db.session.add(like)
        _db.session.commit()

        follower = Follow(follower_id=1, followed_id=2)
        _db.session.add(follower)
        _db.session.commit()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """
    Фикстура тестового клиента для Flask-приложения
    """
    client = app.test_client()
    yield client


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    """
    Фикстура тестовой базы данных
    """
    with app.app_context():
        yield _db


@pytest.fixture
def headers() -> dict:
    """
    Фикстура заголовка запроса
    """
    yield {"api-key": "test-api-key"}
