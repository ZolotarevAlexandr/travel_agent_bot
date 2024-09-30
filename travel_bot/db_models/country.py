from typing import Union

import sqlalchemy

from travel_bot.db_manager import db_session


class Country(db_session.SqlAlchemyBase):
    __tablename__ = "countries"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False, index=True)

    iso3 = sqlalchemy.Column(sqlalchemy.String(3))
    iso2 = sqlalchemy.Column(sqlalchemy.String(2))
    numeric_code = sqlalchemy.Column(sqlalchemy.String(3))
    phone_code = sqlalchemy.Column(sqlalchemy.String(255))

    capital = sqlalchemy.Column(sqlalchemy.String(255))
    currency = sqlalchemy.Column(sqlalchemy.String(255))
    currency_name = sqlalchemy.Column(sqlalchemy.String(255))
    currency_symbol = sqlalchemy.Column(sqlalchemy.String(255))
    tld = sqlalchemy.Column(sqlalchemy.String(255))

    region = sqlalchemy.Column(sqlalchemy.String(255))
    subregion = sqlalchemy.Column(sqlalchemy.String(255))

    native = sqlalchemy.Column(sqlalchemy.String(255))
    nationality = sqlalchemy.Column(sqlalchemy.String(255))

    latitude = sqlalchemy.Column(sqlalchemy.Float(precision=8))
    longitude = sqlalchemy.Column(sqlalchemy.Float(precision=8))

    emoji = sqlalchemy.Column(sqlalchemy.String(191))
    emojiU = sqlalchemy.Column(sqlalchemy.String(191))  # noqa: N815

    cities = sqlalchemy.orm.relationship(
        "City", back_populates="country", lazy="subquery"
    )

    @staticmethod
    def get_country_by_name(country_name: str) -> Union["Country", None]:
        db_sess = db_session.create_session()
        # noinspection PyTypeChecker
        return db_sess.query(Country).filter(Country.name == country_name).first()
