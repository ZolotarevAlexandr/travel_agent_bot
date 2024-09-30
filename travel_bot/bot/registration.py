from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.bot.validators import validate_age, validate_city, validate_country
from travel_bot.db_models import country, user, city

CITY, SPECIFY_CITY, COUNTRY, AGE, BIO, CREATE_USER = range(6)


async def sign_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.effective_user
    if user.User.get_user(tg_user.id):
        reply_keyboard = main_page_keyboard
        await update.message.reply_html(
            rf"Hi {tg_user.mention_html()}! You are already registered!",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ConversationHandler.END

    await update.message.reply_html(
        r"Input your city (It will be used as start point for your new adventures)"
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_city = update.message.text
    is_valid, hints = validate_city(user_city)

    if not is_valid:
        response = "Sorry, location is invalid\n"
        if hints:
            response += "\nDid you mean one of these locations?"
        for idx, hint_city in enumerate(hints, start=1):
            response += f"\n{idx}. {hint_city.name} in {hint_city.country.name}, {hint_city.state_name}"
        await update.message.reply_html(response)
        return CITY

    found_locations = city.City.get_cities_by_name(user_city)
    if len(found_locations) == 1:
        context.user_data["city_name"] = found_locations[0].name
        context.user_data["city_id"] = found_locations[0].id
        await update.message.reply_html(rf"Got your city: {found_locations[0].name}")
        await update.message.reply_html(r"Now, please, input your country")
        return COUNTRY

    context.user_data["found_locations"] = found_locations
    await update.message.reply_html(
        "There are multiple locations with this name. "
        "Please choose one by its number: \n"
    )
    loc_response = ""
    for idx, location in enumerate(found_locations, start=1):
        loc_response += f"{idx}. {location.name} in {location.country.name}, {location.state_name}\n"
    await update.message.reply_html(loc_response)

    return SPECIFY_CITY


async def specify_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    idx = update.message.text
    found_locations = context.user_data["found_locations"]

    if not (0 < int(idx) <= len(found_locations)):
        await update.message.reply_html("Sorry, index is invalid")
        return SPECIFY_CITY

    context.user_data["city_name"] = found_locations[int(idx) - 1].name
    context.user_data["city_id"] = found_locations[int(idx) - 1].id
    await update.message.reply_html(r"Now, please, input your country")
    return COUNTRY


async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_country = update.message.text
    if not validate_country(user_country):
        await update.message.reply_html("Sorry, country is invalid")
        return COUNTRY

    user_country = country.Country.get_country_by_name(user_country)
    context.user_data["country_id"] = user_country.id
    context.user_data["country_name"] = user_country.name
    await update.message.reply_html(rf"Got your city: {user_country.name}")
    await update.message.reply_html(r"Now, please, input your age")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    age = update.message.text
    if not validate_age(age):
        await update.message.reply_html("Sorry, age is invalid")
        return AGE

    context.user_data["age"] = int(age)
    await update.message.reply_html(rf"Got your age: {age}")
    await update.message.reply_html(
        r"Now, you can add some bio or skip it (with /skip command)"
    )
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bio = update.message.text
    context.user_data["bio"] = bio
    await update.message.reply_html(rf"Got your bio: {bio}")
    await create_user(update, context)
    return ConversationHandler.END


async def skip_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await create_user(update, context)
    return ConversationHandler.END


async def create_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    user.User.create_user(
        tg_user.id,
        tg_user.username,
        context.user_data["city_id"],
        context.user_data["city_name"],
        context.user_data["country_id"],
        context.user_data["country_name"],
        context.user_data["age"],
        context.user_data.get("bio", None),
    )
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        r"Thanks for all info. You can now add your "
        r"first travel using /new_travel!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        r"Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


register_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("sign_up", sign_up)],
    states={
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        SPECIFY_CITY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, specify_location)
        ],
        COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
        BIO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio),
            CommandHandler("skip", skip_bio),
        ],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
