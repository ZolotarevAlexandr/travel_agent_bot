from typing import Union, Type

import sqlalchemy
from sqlalchemy.orm import Session

from travel_bot.db_manager import db_session


class City(db_session.SqlAlchemyBase):
    __tablename__ = "cities"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, index=True)

    state_name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    state_code = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)

    country_name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    country_code = sqlalchemy.Column(sqlalchemy.String(2), nullable=False)
    country_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("countries.id")
    )

    latitude = sqlalchemy.Column(sqlalchemy.Float(precision=8), nullable=False)
    longitude = sqlalchemy.Column(sqlalchemy.Float(precision=8), nullable=False)

    country = sqlalchemy.orm.relationship(
        "Country", back_populates="cities", lazy="subquery"
    )

    @staticmethod
    def get_cities_by_name(city_name: str) -> Union[tuple["City"], None]:
        db_sess = db_session.create_session()
        # noinspection PyTypeChecker
        return db_sess.query(City).filter(City.name == city_name).all()

    @staticmethod
    def get_similar_cities(city_name: str) -> list[Type["City"]]:
        db_sess = db_session.create_session()
        return db_sess.query(City).filter(City.name.like(f"%{city_name}%")).all()
