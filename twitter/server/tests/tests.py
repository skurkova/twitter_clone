from typing import Any

import pytest
from db.models import User  # type: ignore
from factories import UserFactory
from faker import Faker
from flask_sqlalchemy import SQLAlchemy

fake = Faker("en_US")


def test_create_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование создание твита
    """
    tweet_data = {
        "tweet_data": "Hello, World!",
        "tweet_media_ids": [1],
    }
    resp = client.post("/api/tweets", data=tweet_data, headers=headers)
    assert resp.status_code == 201


def test_download_files_from_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование загрузки файла из твита
    """
    with open("server/db/images/Hello World.png", "r") as file:
        resp = client.post("/api/medias", data=file, headers=headers)
        assert resp.status_code == 201
        assert resp.data.decode() is not None


def test_error_download_files_from_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при загрузке файла из твита
    """
    resp = client.post("/api/medias", data=None, headers=headers)
    assert resp.status_code == 400
    assert resp.data.decode() == {
        "result": False,
        "error_type": "InvalidInput",
        "error_message": "File not found",
    }


@pytest.mark.parametrize("route", ["/api/tweets", "/api/users/me", "/api/users/1"])
def test_route_status(client: Any, headers: dict, route: str) -> None:
    """
    Тестирование GET-роутов
    """
    resp = client.get(route, headers=headers)
    assert resp.status_code == 200
    assert resp.data.decode() is not None


def test_delete_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование удаления твита
    """
    resp = client.delete("/api/tweets/2", headers=headers)
    assert resp.status_code == 201
    assert resp.data.decode() == {"result": True}


def test_error_delete_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при удалении несуществующего твита
    """
    resp = client.delete("/api/tweets/5", headers=headers)
    assert resp.status_code == 400
    assert resp.data.decode() == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Tweet not found.",
    }


def test_add_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование добавления лайка твиту
    """
    resp = client.post("/api/tweets/1/likes", headers=headers)
    assert resp.status_code == 201
    assert resp.data.decode() == {"result": True}


def test_error_add_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при добавлении лайка несуществующему твиту
    """
    resp = client.post("/api/tweets/5/likes", headers=headers)
    assert resp.status_code == 400
    assert resp.data.decode() == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Tweet not found.",
    }


def test_delete_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование удаления лайка твиту
    """
    resp = client.delete("/api/tweets/1/likes", headers=headers)
    assert resp.status_code == 201
    assert resp.data.decode() == {"result": True}


def test_error_delete_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при удалении несуществующего лайка твиту
    """
    resp = client.delete("/api/tweets/5/likes", headers=headers)
    assert resp.status_code == 400
    assert resp.data.decode() == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Like not found.",
    }


def test_add_follow(client: Any, headers: dict) -> None:
    """
    Тестирование подписки на другого пользователя
    """
    resp = client.post("/api/users/2/follow", headers=headers)
    assert resp.status_code == 201
    assert resp.data.decode() == {"result": True}


def test_delete_follow(client: Any, headers: dict) -> None:
    """
    Тестирование отписки от пользователя
    """
    resp = client.delete("/api/users/2/follow", headers=headers)
    assert resp.status_code == 201
    assert resp.data.decode() == {"result": True}


def test_error_delete_follow(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки удаления несуществующей подписки на пользователя
    """
    resp = client.delete("/api/users/3/follow", headers=headers)
    assert resp.status_code == 400
    assert resp.data.decode() == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Follow not found.",
    }


def test_creat_user_factory(db: SQLAlchemy) -> None:
    """
    Тестирование создания фабрики пользователя
    """
    user = UserFactory()
    db.session.add(user)
    db.session.commit()
    assert user.id is not None
    assert len(db.session.query(User).all()) == 3
