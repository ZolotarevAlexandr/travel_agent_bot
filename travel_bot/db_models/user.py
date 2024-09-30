import datetime
import logging
from typing import Union

import sqlalchemy

from travel_bot.db_manager import db_session


logger = logging.getLogger(__name__)


# noinspection PyTypeChecker
class User(db_session.SqlAlchemyBase):
    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    tg_username = sqlalchemy.Column(
        sqlalchemy.String, unique=True, index=True, nullable=False
    )

    city_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("cities.id"), nullable=False
    )
    city_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    country_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("countries.id"), nullable=False
    )
    country_name = sqlalchemy.Column(sqlalchemy.String)

    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    bio = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    registered = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    city = sqlalchemy.orm.relationship("City", lazy="subquery")
    country = sqlalchemy.orm.relationship("Country", lazy="subquery")

    travels = sqlalchemy.orm.relationship(
        "Travel", back_populates="owner", lazy="subquery"
    )
    invited_travels = sqlalchemy.orm.relationship(
        "Travel",
        secondary="travel_to_user",
        back_populates="invited_users",
        lazy="subquery",
    )

    @staticmethod
    def get_user(user_id: int) -> Union["User", None]:
        db_sess = db_session.create_session()
        # noinspection PyTypeChecker
        return db_sess.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_tg_username(tg_username: str) -> Union["User", None]:
        db_sess = db_session.create_session()
        return db_sess.query(User).filter(User.tg_username == tg_username).first()

    @staticmethod
    def get_user_by_tg_id(tg_id: int) -> Union["User", None]:
        db_sess = db_session.create_session()
        return db_sess.query(User).filter(User.id == tg_id).first()

    @staticmethod
    def create_user(
        user_id: int,
        tg_username: str,
        city_id: int,
        city_name: str,
        country_id: int,
        country_name: str,
        age: int,
        bio: str | None,
    ) -> "User":
        db_sess = db_session.create_session()
        user = User(
            id=user_id,
            tg_username=tg_username,
            city_id=city_id,
            city_name=city_name,
            country_id=country_id,
            country_name=country_name,
            age=age,
            bio=bio,
        )
        db_sess.add(user)
        db_sess.commit()
        logger.info(f"User with id: {user_id} created")
        return user
