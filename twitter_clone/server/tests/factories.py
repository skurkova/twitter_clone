import secrets
import string

import factory
from db.models import User, db  # type: ignore


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    name = factory.Faker("name")
    api_key = factory.LazyAttribute(
        lambda x: "".join(
            secrets.choice(string.ascii_letters + string.digits) for _ in range(20)
        )
    )
