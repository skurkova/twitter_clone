import os
from typing import Any

import pytest
from db.models import User  # type: ignore
from faker import Faker
from flask_sqlalchemy import SQLAlchemy
from tests.factories import UserFactory  # type: ignore

fake = Faker("en_US")


def test_create_tweet(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование создание твита
    """
    tweet_data = {
        "tweet_data": "Hello, World!",
        "tweet_media_ids": [1],
    }
    resp = client.post("/api/tweets", data=tweet_data, headers=headers)

    assert resp.status_code == 201
    assert resp.json["result"] is True
    assert "tweet_id" in resp.json


def test_download_files_from_tweet(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование загрузки файла из твита
    """
    file = open(os.path.join("tests/images", "Hello!.png"), "rb")
    resp = client.post("/api/medias", data={"file": (file, "Hello!.png")}, headers=headers)

    assert resp.status_code == 201
    assert resp.json["result"] is True
    assert "media_id" in resp.json


def test_error_download_files_from_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при загрузке файла из твита
    """
    resp = client.post("/api/medias", data={"file": (None, "")}, headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "File not found",
    }


@pytest.mark.parametrize("route", ["/api/tweets", "/api/users/me", "/api/users/1"])
def test_route_status(client: Any, headers: dict, route: str) -> None:
    """
    Тестирование GET-роутов
    """
    resp = client.get(route, headers=headers)

    assert resp.status_code == 200
    assert resp.json is not None


def test_delete_tweet(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование удаления твита
    """
    resp = client.delete("/api/tweets/1", headers=headers)

    assert resp.status_code == 201
    assert resp.json == {"result": True}


def test_error_delete_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при удалении несуществующего твита
    """
    resp = client.delete("/api/tweets/5", headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Tweet not found.",
    }


def test_add_likes_tweet(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование добавления лайка твиту
    """
    resp = client.post("/api/tweets/2/likes", headers=headers)

    assert resp.status_code == 201
    assert resp.json == {"result": True}


def test_error_add_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при добавлении лайка несуществующему твиту
    """
    resp = client.post("/api/tweets/5/likes", headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Tweet not found.",
    }


def test_delete_likes_tweet(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование удаления лайка твиту
    """
    resp = client.delete("/api/tweets/2/likes", headers=headers)

    assert resp.status_code == 201
    assert resp.json == {"result": True}


def test_error_delete_likes_tweet(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки при удалении несуществующего лайка твиту
    """
    resp = client.delete("/api/tweets/5/likes", headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Like not found.",
    }


def test_add_follow(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование подписки на другого пользователя
    """
    resp = client.post(f"/api/users/3/follow", headers=headers)

    assert resp.status_code == 201
    assert resp.json == {"result": True}


def test_error_add_follow(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование ошибки подписки на самого себя
    """
    resp = client.post(f"/api/users/1/follow", headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "FollowError",
        "error_message": "You can't follow to yourself."
    }


def test_delete_follow(client: Any, db: SQLAlchemy, headers: dict) -> None:
    """
    Тестирование отписки от пользователя
    """
    resp = client.delete(f"/api/users/2/follow", headers=headers)

    assert resp.status_code == 201
    assert resp.json == {"result": True}


def test_error_delete_follow(client: Any, headers: dict) -> None:
    """
    Тестирование ошибки удаления несуществующей подписки на пользователя
    """
    resp = client.delete("/api/users/3/follow", headers=headers)

    assert resp.status_code == 400
    assert resp.json == {
        "result": False,
        "error_type": "NotFound",
        "error_message": "Follow not found.",
    }


def test_creat_user_factory(db: SQLAlchemy) -> None:
    """
    Тестирование создания фабрики пользователя
    """
    user = UserFactory()
    if user not in db.session.query(User).all():
        db.session.add(user)
        db.session.commit()
    assert user.id is not None
    assert len(db.session.query(User).all()) == 4
