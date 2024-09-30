import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.db_models import country, user, travel, city


def sign_up_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        tg_user = update.message.from_user
        if user.User.get_user(tg_user.id):
            return await func(update, context)
        else:
            await update.message.reply_html("Please /sign_up first")
            return ConversationHandler.END

    return wrapper


def must_have_travels(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        tg_user = update.effective_user
        if travel.Travel.get_user_travels(tg_user.id):
            return await func(update, context)
        else:
            reply_keyboard = main_page_keyboard
            await update.message.reply_html("You don't have any travels")
            await update.message.reply_html(
                "Let's fix it! Type /new_travel to add new travel",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return ConversationHandler.END

    return wrapper


def validate_city(city_name: str) -> (bool, list[city.City]):
    found_cities = city.City.get_cities_by_name(city_name)
    if len(found_cities) != 0:
        return True, []

    hints = city.City.get_similar_cities(city_name)[:20]
    return False, hints


def validate_country(country_name: str) -> bool:
    return country.Country.get_country_by_name(country_name) is not None


def validate_age(age: str) -> bool:
    if not age.isdigit():
        return False
    if not (0 < int(age) < 100):
        return False
    return True


def validate_travel_name(name: str, user_id: int) -> bool:
    travels = travel.Travel.get_user_travel(name, user_id)
    return travels is None


def validate_travel_description(description: str) -> bool:
    return bool(description.strip())


def validate_travel_locations(locations: list[str]) -> bool:
    return all([validate_city(location) for location in locations])


def validate_travel_dates(start_date: str, end_date: str) -> bool:
    try:
        start = datetime.datetime.strptime(start_date, "%d.%m.%Y")
        end = datetime.datetime.strptime(end_date, "%d.%m.%Y")
    except ValueError:
        return False
    if start > end or start < datetime.datetime.now():
        return False
    return True


def validate_username(username: str) -> bool:
    return user.User.get_user_by_tg_username(username) is not None


def validate_purchase(price: str) -> bool:
    return price.isdigit()
