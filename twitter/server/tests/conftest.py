import pytest

from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from twitter.server.api.main import create_app
from twitter.server.db.models import Tweet, User
from twitter.server.db.models import db as _db


@pytest.fixture()
def app() -> Flask:
    """
    Фикстура экземпляра Flask-приложения для тестирования
    """
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with _app.app_context():
        _db.create_all()
        users = [
            User(id=1, name="Ivan Petrov", api_key="api-key 1"),
            User(id=2, name="Sergey Romanov", api_key="api-key 2"),
        ]

        tweet = Tweet(
            id=1, user_id=1, content="Hello, World!", medias_ids=[], count_likes=0
        )

        _db.session.bulk_save_objects(users)
        _db.session.add(tweet)
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
