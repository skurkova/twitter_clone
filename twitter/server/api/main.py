import os

from typing import Union, Tuple
from faker import Faker
from flasgger import Swagger
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

from twitter.server.db.models import Follow, Like, Media, Tweet, User, db
from twitter.server.tests.factories import UserFactory

fake = Faker("en_US")
UPLOAD_FOLDER = "server/db/uploads"
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
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "postgresql+psycopg2://admin:admin@db:5432/twitter"
    )
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    db.init_app(app)
    with app.app_context():
        db.create_all()
    Swagger(app, template_file="swagger.yaml")

    @app.teardown_appcontext
    def shutdown_session(exception=None) -> None:
        db.session.remove()

    @app.route("/", methods=["GET"])
    def populating_db() -> Tuple[Response, int]:
        """
        Заполнить базу данных пользователями
        """
        users = [UserFactory() for _ in range(20)]

        db.session.bulk_save_objects(users)
        db.session.commit()
        return jsonify({"result": True, "message": "Database populated successfully"}), 200

    @app.route("/api", methods=["GET"])
    def index() -> str:
        """
        Главная страница API.
        """
        return render_template("index.html")

    @app.route("/api/tweets", methods=["POST"])
    def create_tweet() -> Tuple[Response, int]:
        """
        Создать новый твит
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        tweet_data = request.form.get("tweet_data")
        tweet_media_ids = request.form.get("tweet_media_ids", "[]")
        new_tweet = Tweet(
            user_id=user.id, content=tweet_data, medias_ids=tweet_media_ids
        )
        db.session.add(new_tweet)
        db.session.flush()

        for media_id in tweet_media_ids:
            media = db.session.query(Media).get(media_id).one_or_none()
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

        tweet = (
            db.session.query(Tweet)
            .filter_by(id=tweet_id, user_id=user.id)
            .one_or_none()
        )
        if tweet is not None:
            db.session.delete(tweet)
            return jsonify({"result": True}), 201
        else:
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

    @app.route("/api/tweets/<int:tweet_id>/likes", methods=["POST"])
    def add_likes_tweet(tweet_id: int) -> Tuple[Response, int]:
        """
        Поставить лайк на твит
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        tweet = db.session.query(Tweet).get(tweet_id).one_or_none()
        if tweet is not None:
            tweet.count_likes += 1
            like = Like(user_id=user.id, tweet_id=tweet.id)
            db.session.add(like)
            db.session.commit()
            return jsonify({"result": True}), 201
        else:
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

    @app.route("/api/tweets/<int:tweet_id>/likes", methods=["DELETE"])
    def delete_likes_tweet(tweet_id: int) -> Tuple[Response, int]:
        """
        Убрать лайк с твита
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

        tweet = db.session.query(Tweet).get(tweet_id)
        like = (
            db.session.query(Like)
            .filter_by(user_id=user.id, tweet_id=tweet_id)
            .one_or_none()
        )
        if like is not None:
            if tweet.count_likes > 0:
                tweet.count_likes -= 1
                db.session.delete(like)
                db.session.commit()
                return jsonify({"result": True}), 201
        else:
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

    @app.route("/api/users/<int:user_id>/follow", methods=["POST"])
    def add_follow(user_id: int) -> Tuple[Response, int]:
        """
        Подписаться на другого пользователя
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)

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

        follow = (
            db.session.query(Follow)
            .filter_by(follower_id=user.id, followed_id=user_id)
            .one_or_none()
        )
        if follow is not None:
            db.session.delete(follow)
            db.session.commit()
            return jsonify({"result": True}), 201
        else:
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

    @app.route("/api/tweets", methods=["GET"])
    def get_tweets() -> Tuple[Response, int]:
        """
        Получить ленту с твитами
        """
        api_key = request.headers.get("api-key")
        user = authenticate_user(api_key)
        followed_users = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user.id).all()
        ]
        tweets = (
            db.session.query(Tweet)
            .filter_by(Tweet.user_id.in_(followed_users))
            .order_by(Tweet.count_likes.desc())
            .all()
        )
        return (
            jsonify(
                {
                    "result": True,
                    "tweets": [
                        {
                            "id": tweet.id,
                            "content": tweet.content,
                            "attachments": tweet.medias,
                            "author": tweet.author,
                            "likes": tweet.likes,
                        }
                        for tweet in tweets
                    ],
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

        followers = [
            f.follower_id
            for f in db.session.query(Follow).filter_by(followed_id=user.id).all()
        ]
        following = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user.id).all()
        ]

        followers_users = [
            user
            for user in db.session.query(User).filter(User.id.in_(followers)).all()
        ]
        following_users = [
            user
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

        user_data = db.session.query(User).filter_by(id=user_id)
        followers = [
            f.follower_id
            for f in db.session.query(Follow).filter_by(followed_id=user_id).all()
        ]
        following = [
            f.followed_id
            for f in db.session.query(Follow).filter_by(follower_id=user_id).all()
        ]

        followers_users = [
            user
            for user in db.session.query(User).filter(User.id.in_(followers)).all()
        ]
        following_users = [
            user
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


if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)