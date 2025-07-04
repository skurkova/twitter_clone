from typing import Any, Dict

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"User {self.name}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tweet(db.Model):
    __tablename__ = "tweets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    medias_ids = db.Column(db.ARRAY(db.Integer))
    count_likes = db.Column(db.Integer, default=0)
    author = db.relationship("User", backref="tweets", lazy=True)
    likes = db.relationship(
        "Like", backref="tweets", lazy=True, cascade="all, delete-orphan"
    )
    medias = db.relationship(
        "Media", backref="tweets", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Tweet {self.content} author {self.author}"

    def to_json(self) -> Dict[str, Any]:
        data_tweet = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        data_tweet["author"] = self.author.to_json() if self.author else None
        data_tweet["likes"] = [like.to_json() for like in self.likes]
        data_tweet["medias"] = [media.to_json() for media in self.medias]
        return data_tweet


class Media(db.Model):
    __tablename__ = "medias"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(150), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"))

    def __repr__(self) -> str:
        return f"Media {self.filename}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Like(db.Model):
    __tablename__ = "likes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey("tweets.id"), nullable=False)

    def __repr__(self) -> str:
        return f"User{self.user_id} like Tweet {self.tweet_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Follow(db.Model):
    __tablename__ = "followers"
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    def __repr__(self) -> str:
        return f"Follower {self.follower_id}"

    def to_json(self) -> Dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
