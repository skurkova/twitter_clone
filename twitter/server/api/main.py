import os
from typing import Tuple, Union

from db.models import Follow, Like, Media, Tweet, User, db  # type: ignore
from faker import Faker
from flasgger import Swagger
from flask import Flask, jsonify, request, Response, send_from_directory
from tests.factories import UserFactory  # type: ignore
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

fake = Faker("en_US")
UPLOAD_FOLDER = "db/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def authenticate_user(api_key: str) -> Union[User, Tuple[Response, int]]:
    """
    Аутентификация пользователя по api_key в заголовках запроса
    """
    user = db.session.query(User).filter_by(api_key=api_key).first()
    if not user:
        return (
            jsonify(
                {
                    "result": False,
                    "error_type": "User unauthorized",
                    "error_message": "Invalid api-key",
                }
            ),
            401,
        )
    return user


def create_app() -> Flask:
    """
    Запуск приложения
    """
    app = Flask(__name__, static_folder="static", template_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql+psycopg2://admin:admin@db:5432/twitter"
    )
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    db.init_app(app)
    with app.app_context():
        db.create_all()
    Swagger(app, template_file="swagger_cals.yaml")

    @app.teardown_appcontext
    def shutdown_session(exception=None) -> None:
        db.session.remove()

    @app.route("/login")
    def read_main():
        return send_from_directory("static", "index.html")

    @app.route("/static/<path:path>")
    def send_static(path):
        return send_from_directory("static", path)

    @app.route("/js/<path:path>")
    def send_js(path):
        return send_from_directory("static/js", path)

    @app.route("/css/<path:path>")
    def send_css(path):
        return send_from_directory("static/css", path)

    @app.route("/api", methods=["GET"])
    def populating_db() -> Tuple[Response, int]:
        """
        Заполнить базу данных пользователями
        """
        user_test = User(name="test", api_key="test")
        users_api_keys = {user.api_key for user in db.session.query(User.api_key).all()}
        if user_test.api_key not in users_api_keys:
            db.session.add(user_test)

        for _ in range(20):
            user = UserFactory()
            users_api_keys = {
                user.api_key for user in db.session.query(User.api_key).all()
            }
            if user.api_key not in users_api_keys:
                db.session.add(user)
        db.session.commit()
        return (
            jsonify({"result": True, "message": "Database populated successfully"}),
            200,
        )

    @app.route("/api/tweets", methods=["POST"])
    def create_tweet() -> Tuple[Response, int]:
        """
        Создать новый твит
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        tweet_data = request.form.get("tweet_data")
        tweet_media_ids = request.form.get("tweet_media_ids", "[]")
        new_tweet = Tweet(
            user_id=user.id, content=tweet_data, medias_ids=tweet_media_ids
        )
        db.session.add(new_tweet)
        db.session.flush()

        for media_id in tweet_media_ids:
            media = db.session.query(Media).get(media_id)
            if media is not None:
                media.tweet_id = new_tweet.id
        db.session.commit()

        return jsonify({"result": True, "tweet_id": new_tweet.id}), 201

    @app.route("/api/medias", methods=["POST"])
    def download_files_from_tweet() -> Tuple[Response, int]:
        """
        Загрузить файлы из твита
        """
        file = request.files["file"]
        if file:
            file_name = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file_name)
            file.save(file_path)

            new_media = Media(filename=file_name, file_path=file_path)
            db.session.add(new_media)
            db.session.commit()
            return jsonify({"result": True, "media_id": new_media.id}), 201
        else:
            return (
                jsonify(
                    {
                        "result": False,
                        "error_type": "InvalidInput",
                        "error_message": "File not found",
                    }
                ),
                400,
            )

    @app.route("/api/tweets/<int:tweet_id>", methods=["DELETE"])
    def delete_tweet(tweet_id: int) -> Tuple[Response, int]:
        """
        Удалить твит
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        tweet = (
            db.session.query(Tweet)
            .filter_by(id=tweet_id, user_id=user.id)
            .one_or_none()
        )
        if not tweet:
            return (
                jsonify(
                    {
                        "result": False,
                        "error_type": "NotFound",
                        "error_message": "Tweet not found.",
                    }
                ),
                400,
            )
        else:
            db.session.delete(tweet)
            db.session.commit()
            return jsonify({"result": True}), 201

    @app.route("/api/tweets/<int:tweet_id>/likes", methods=["POST"])
    def add_likes_tweet(tweet_id: int) -> Tuple[Response, int]:
        """
        Поставить лайк на твит
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        tweet = db.session.query(Tweet).get(tweet_id)
        if not tweet:
            return (
                jsonify(
                    {
                        "result": False,
                        "error_type": "NotFound",
                        "error_message": "Tweet not found.",
                    }
                ),
                400,
            )
        else:
            tweet.count_likes += 1
            like = Like(user_id=user.id, tweet_id=tweet.id)
            db.session.add(like)
            db.session.commit()
            return jsonify({"result": True}), 201

    @app.route("/api/tweets/<int:tweet_id>/likes", methods=["DELETE"])
    def delete_likes_tweet(tweet_id: int) -> Tuple[Response, int]:
        """
        Убрать лайк с твита
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        tweet = db.session.query(Tweet).get(tweet_id)
        like = (
            db.session.query(Like)
            .filter_by(user_id=user.id, tweet_id=tweet_id)
            .one_or_none()
        )
        if not like:
            return (
                jsonify(
                    {
                        "result": False,
                        "error_type": "NotFound",
                        "error_message": "Like not found.",
                    }
                ),
                400,
            )
        else:
            if tweet.count_likes > 0:
                tweet.count_likes -= 1
                db.session.delete(like)
                db.session.commit()
                return jsonify({"result": True}), 201

    @app.route("/api/users/<int:user_id>/follow", methods=["POST"])
    def add_follow(user_id: int) -> Tuple[Response, int]:
        """
        Подписаться на другого пользователя
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        follow = Follow(follower_id=user.id, followed_id=user_id)
        db.session.add(follow)
        db.session.commit()
        return jsonify({"result": True}), 201

    @app.route("/api/users/<int:user_id>/follow", methods=["DELETE"])
    def delete_follow(user_id: int) -> Tuple[Response, int]:
        """
        Отписаться от другого пользователя
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        follow = (
            db.session.query(Follow)
            .filter_by(follower_id=user.id, followed_id=user_id)
            .one_or_none()
        )
        if not follow:
            return (
                jsonify(
                    {
                        "result": False,
                        "error_type": "NotFound",
                        "error_message": "Follow not found.",
                    }
                ),
                400,
            )
        else:
            db.session.delete(follow)
            db.session.commit()
            return jsonify({"result": True}), 201

    @app.route("/api/tweets", methods=["GET"])
    def get_tweets() -> Tuple[Response, int]:
        """
        Получить ленту с твитами
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        followed_users = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user.id).all()
        ]
        if not followed_users:
            return (
                jsonify(
                    {
                        "result": True,
                        "tweets": [],
                    }
                ),
                200,
            )

        tweets = (
            db.session.query(Tweet)
            .filter(Tweet.user_id.in_(followed_users))
            .order_by(Tweet.count_likes.desc())
            .all()
        )
        return (
            jsonify(
                {
                    "result": True,
                    "tweets": [tweet.to_json() for tweet in tweets],
                }
            ),
            200,
        )

    @app.route("/api/users/me", methods=["GET"])
    def get_my_profile() -> Tuple[Response, int]:
        """
        Получить информацию о своём профиле
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        followers = [
            f.follower_id
            for f in db.session.query(Follow).filter_by(followed_id=user.id).all()
        ]
        following = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user.id).all()
        ]

        if not followers:
            followers_users = []
        else:
            followers_users = [
                user.to_json()
                for user in db.session.query(User).filter(User.id.in_(followers)).all()
            ]

        if not following:
            following_users = []
        else:
            following_users = [
                user.to_json()
                for user in db.session.query(User).filter(User.id.in_(following)).all()
            ]

        return (
            jsonify(
                {
                    "result": True,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "followers": followers_users,
                        "following": following_users,
                    },
                }
            ),
            200,
        )

    @app.route("/api/users/<int:user_id>", methods=["GET"])
    def get_user_profile(user_id: int) -> Tuple[Response, int]:
        """
        Получить информацию о профиле по ID
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        if isinstance(user, tuple):
            return user

        user_data = db.session.query(User).filter_by(id=user_id).one_or_none()

        followers = [
            f.follower_id
            for f in db.session.query(Follow).filter_by(followed_id=user_id).all()
        ]
        following = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user_id).all()
        ]

        if not followers:
            followers_users = []
        else:
            followers_users = [
                user.to_json()
                for user in db.session.query(User).filter(User.id.in_(followers)).all()
            ]

        if not following:
            following_users = []
        else:
            following_users = [
                user.to_json()
                for user in db.session.query(User).filter(User.id.in_(following)).all()
            ]

        return (
            jsonify(
                {
                    "result": True,
                    "user": {
                        "id": user_data.id,
                        "name": user_data.name,
                        "followers": followers_users,
                        "following": following_users,
                    },
                }
            ),
            200,
        )

    return app
