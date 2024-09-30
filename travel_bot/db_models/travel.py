import datetime
import logging
from typing import Union

import sqlalchemy

from travel_bot.db_manager import db_session
from travel_bot.db_models.city import City
from travel_bot.db_models.user import User


logger = logging.getLogger(__name__)


# noinspection PyTypeChecker
class Travel(db_session.SqlAlchemyBase):
    __tablename__ = "travels"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, index=True)

    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    start_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)
    end_date = sqlalchemy.Column(sqlalchemy.Date, nullable=False)

    owner = sqlalchemy.orm.relationship("User", lazy="subquery")
    notes = sqlalchemy.orm.relationship(
        "TravelNote", back_populates="travel", lazy="subquery", cascade="all, delete"
    )
    purchases = sqlalchemy.orm.relationship(
        "TravelPurchase", back_populates="travel", lazy="subquery", cascade="all, delete"
    )
    locations = sqlalchemy.orm.relationship(
        "City", secondary="travel_to_city", lazy="subquery", backref="travels"
    )
    invited_users = sqlalchemy.orm.relationship(
        "User",
        secondary="travel_to_user",
        lazy="subquery",
        back_populates="invited_travels",
    )

    @staticmethod
    def create_travel(
        owner_id: int,
        name: str,
        description: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> "Travel":
        db_sess = db_session.create_session()
        travel = Travel(
            owner_id=owner_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
        )
        db_sess.add(travel)
        db_sess.commit()
        logger.info(f"Travel with id: {travel.id} created")
        return travel

    @staticmethod
    def get_user_travel(travel_name: str, user_id: int) -> Union["Travel", None]:
        db_sess = db_session.create_session()
        travel = (
            db_sess.query(Travel)
            .filter(Travel.name == travel_name, Travel.owner_id == user_id)
            .first()
        )
        return travel

    @staticmethod
    def get_user_and_invited_travel(
        travel_name: str, user_id: int
    ) -> Union["Travel", None]:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        travel = db_sess.query(Travel).filter(Travel.name == travel_name).first()
        if travel is None:
            return None
        if travel.owner == user or user in travel.invited_users:
            return travel
        return None

    @staticmethod
    def get_user_travels(user_id: int) -> list["Travel"]:
        db_sess = db_session.create_session()
        travels = db_sess.query(Travel).filter(Travel.owner_id == user_id).all()
        return travels

    @staticmethod
    def delete_travel(travel_name: str, user_id: int) -> None:
        db_sess = db_session.create_session()
        travel_to_del = (
            db_sess.query(Travel)
            .filter(Travel.name == travel_name, Travel.owner_id == user_id)
            .first()
        )
        db_sess.delete(travel_to_del)
        db_sess.commit()
        logger.info(f"Travel with id: {travel_to_del.id} deleted")

    @staticmethod
    def invite_user(travel_id: int, user_id: int) -> None:
        db_sess = db_session.create_session()

        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        user = db_sess.query(User).filter(User.id == user_id).first()
        travel.invited_users.append(user)

        db_sess.commit()
        logger.info(f"User with id: {user_id} invited to travel with id: {travel_id}")

    @staticmethod
    def remove_user(travel_id: int, user_id: int) -> None:
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        user = db_sess.query(User).filter(User.id == user_id).first()
        travel.invited_users.remove(user)
        db_sess.commit()
        logger.info(f"User with id: {user_id} removed from travel with id: {travel_id}")

    @staticmethod
    def remove_users(travel_id: int) -> None:
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        travel.invited_users.clear()
        db_sess.commit()
        logger.info(f"Users removed from travel with id: {travel_id}")

    @staticmethod
    def remove_locations(travel_id: int) -> None:
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        travel.locations.clear()
        db_sess.commit()
        logger.info(f"Locations removed from travel with id: {travel_id}")

    @staticmethod
    def add_location(travel_id: int, city_id: int) -> None:
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        city = db_sess.query(City).filter(City.id == city_id).first()
        travel.locations.append(city)
        db_sess.commit()
        logger.info(f"City with id: {city_id} added to travel with id: {travel_id}")

    @staticmethod
    def edit_value(
        travel_id: int, column_name: str, value: str | int | datetime.datetime
    ) -> None:
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        match column_name:
            case "name":
                travel.name = value
            case "description":
                travel.description = value
            case "start_date":
                travel.start_date = value
            case "end_date":
                travel.end_date = value
        db_sess.commit()
        logger.info(f"Value {column_name} changed in travel with id: {travel_id}")


# noinspection PyTypeChecker
class TravelNote(db_session.SqlAlchemyBase):
    __tablename__ = "travel_notes"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    travel_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("travels.id"), nullable=False
    )
    by_user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False
    )

    is_public = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    note = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    travel = sqlalchemy.orm.relationship("Travel")
    by_user = sqlalchemy.orm.relationship("User")

    @staticmethod
    def add_note(
        travel_id: int, user_id: int, note: str, is_public: bool
    ) -> "TravelNote":
        db_sess = db_session.create_session()
        travel = db_sess.query(Travel).filter(Travel.id == travel_id).first()
        travel_notes = TravelNote(
            travel=travel, by_user_id=user_id, note=note, is_public=is_public
        )
        db_sess.add(travel_notes)
        db_sess.commit()
        logger.info(f"Note added to travel with id: {travel_id}")
        return travel_notes

    @staticmethod
    def get_travel_notes(travel_id: int) -> list["TravelNote"]:
        db_sess = db_session.create_session()
        travel_notes = (
            db_sess.query(TravelNote).filter(TravelNote.travel_id == travel_id).all()
        )
        return travel_notes

    @staticmethod
    def delete_note(note_id: int) -> None:
        db_sess = db_session.create_session()
        travel_notes = (
            db_sess.query(TravelNote).filter(TravelNote.id == note_id).first()
        )
        db_sess.delete(travel_notes)
        db_sess.commit()
        logger.info(f"Note with id: {note_id} deleted")


class TravelPurchase(db_session.SqlAlchemyBase):
    __tablename__ = "purchases"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    travel_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("travels.id"), nullable=False
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False
    )
    on_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=datetime.datetime.now)

    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    note = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    travel = sqlalchemy.orm.relationship("Travel")
    by_user = sqlalchemy.orm.relationship("User")

    @staticmethod
    def add_purchase(travel_id: int, user_id: int, price: int, note: str):
        db_sess = db_session.create_session()
        purchase = TravelPurchase(
            travel_id=travel_id, user_id=user_id, price=price, note=note
        )
        db_sess.add(purchase)
        db_sess.commit()
        logger.info(f"Purchase added to travel with id: {travel_id}")

    @staticmethod
    def get_travel_purchases(travel_id: int) -> list["TravelPurchase"]:
        db_sess = db_session.create_session()
        travel_purchases = (
            db_sess.query(TravelPurchase).filter(TravelPurchase.travel_id == travel_id).all()
        )
        return travel_purchases

    @staticmethod
    def get_user_purchases(user_id: int) -> list["TravelPurchase"]:
        db_sess = db_session.create_session()
        travel_purchases = (
            db_sess.query(TravelPurchase).filter(TravelPurchase.user_id == user_id).all()
        )
        return travel_purchases

    @staticmethod
    def get_user_total_price(user_id: int) -> int:
        db_sess = db_session.create_session()
        total_price = 0
        travel_purchases = db_sess.query(TravelPurchase).filter(TravelPurchase.user_id == user_id).all()
        for purchase in travel_purchases:
            total_price += purchase.price
        return total_price


travel_to_user = sqlalchemy.Table(
    "travel_to_user",
    db_session.SqlAlchemyBase.metadata,
    sqlalchemy.Column(
        "travel_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("travels.id")
    ),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
)

travel_to_city = sqlalchemy.Table(
    "travel_to_city",
    db_session.SqlAlchemyBase.metadata,
    sqlalchemy.Column(
        "travel_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("travels.id")
    ),
    sqlalchemy.Column(
        "city_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("cities.id")
    ),
)
