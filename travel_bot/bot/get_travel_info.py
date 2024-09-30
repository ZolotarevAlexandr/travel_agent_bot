from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from travel_bot.api import weather, route, hotels
from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.bot.validators import sign_up_required
from travel_bot.db_models import user, travel

GET_INFO = 0


@sign_up_required
async def get_travels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    db_user = user.User.get_user_by_tg_id(tg_user.id)

    response = ""
    if db_user.travels:
        response += "Your travels: \n"
        for user_travel in db_user.travels:
            response += f"\nName: {user_travel.name}\n"
            response += f"Description: {user_travel.description}\n"
            response += f"Locations: {', '.join(map(lambda x: x.name, user_travel.locations))}\n"
            response += (
                f"Dates: from {user_travel.start_date} to {user_travel.end_date}\n"
            )

    if db_user.invited_travels:
        response += "\nYou are invited to: \n"
        for user_travel in db_user.invited_travels:
            response += f"\nName: {user_travel.name}\n"
            response += f"Description: {user_travel.description}\n"
            response += f"Locations: {', '.join(map(lambda x: x.name, user_travel.locations))}\n"
            response += (
                f"Dates: from {user_travel.start_date} to {user_travel.end_date}\n"
            )

    if not response:
        response = "You don't have any travels"

    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        response,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


@sign_up_required
async def choose_travel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = user.User.get_user_by_tg_id(update.effective_user.id)
    available_travels = db_user.travels + db_user.invited_travels

    if not available_travels:
        reply_keyboard = main_page_keyboard
        await update.message.reply_html(
            "You don't have any travels",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ConversationHandler.END

    response = "Choose travel (type travel's name): \n"
    for user_travel in available_travels:
        response += f"• {user_travel.name}\n"

    reply_keyboard = [[user_travel.name] for user_travel in available_travels]
    await update.message.reply_html(
        response,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return GET_INFO


async def get_travel_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_name = update.message.text
    tg_user = update.effective_user
    db_user = user.User.get_user_by_tg_id(tg_user.id)
    user_travel = travel.Travel.get_user_and_invited_travel(travel_name, tg_user.id)
    if user_travel is None:
        await update.message.reply_html("Sorry, travel name is invalid")
        return GET_INFO

    response = f"Travel name: {user_travel.name}\n"
    response += f"Travel description: {user_travel.description}\n"
    response += f"Travel start date: {user_travel.start_date}\n"
    response += f"Travel end date: {user_travel.end_date}\n"
    response += "Travel locations: \n"
    for location in user_travel.locations:
        response += f"\t• {location.name}\n"

    if user_travel.invited_users:
        response += "Invited users: \n"
        for invited_user in user_travel.invited_users:
            response += f"\t• {invited_user.tg_username}\n"
    await update.message.reply_html(response)

    cities = [db_user.city] + user_travel.locations
    await update.message.reply_html("Travel route (might take a moment): \n")
    img = route.get_map_png(*cities)
    await update.message.reply_photo(
        img, caption=f"{" - ".join(str(travel_city.name) for travel_city in cities)}"
    )

    notes = user_travel.notes
    if notes:
        await send_notes(update, notes)

    await send_hotels(update, user_travel)
    await send_weather(update, user_travel)
    return ConversationHandler.END


async def send_notes(update: Update, notes: list[travel.TravelNote]):
    notes_response = "Travel notes: "
    for travel_note in notes:
        if travel_note.is_public or travel_note.by_user_id == update.effective_user.id:
            notes_response += (
                f"\n• {travel_note.by_user.tg_username}: {travel_note.note}"
            )

    await update.message.reply_html(notes_response)


async def send_hotels(update: Update, user_travel: travel.Travel) -> None:
    travel_hotels = hotels.get_hotels_for_travel(user_travel)
    if travel_hotels["info"]["error_code"] != 0:
        await update.message.reply_html("Sorry, hotels data is not available")
        return
    hotels_response = "Most popular hotels: \n"
    for location in travel_hotels["hotels"]:
        hotels_response += f"\n• Hotels in {location}: \n"
        for hotel_id in travel_hotels["hotels"][location]["hotels"]:
            hotel = travel_hotels["hotels"][location]["hotels"][hotel_id]
            if hotel["stars"] is None:
                hotel["stars"] = "'no start rating'"
            hotels_response += f"\nHotel: '{hotel['name']}' with {hotel['stars']} stars and '{hotel['user_rating']}' user rating. Price of one night: {hotel['price']}. {hotel['distance']} miles away from city center\n"

    await update.message.reply_html(hotels_response)


async def send_weather(update: Update, user_travel: travel.Travel) -> None:
    reply_keyboard = main_page_keyboard

    weather_data = weather.get_short_weather(user_travel)
    weather_response = "Travel weather: \n"

    if weather_data["info"]["error_code"] != 0:
        await update.message.reply_html(
            weather_data["info"]["error"],
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return
    else:
        weather_data = weather_data["weather"]
        for loc in weather_data:
            weather_response += f"\nWeather in {loc}: \n"
            weather_response += f"• Average day temperature: {round(weather_data[loc]['avg_day_temp'])} °C\n"
            weather_response += f"• Average night temperature: {round(weather_data[loc]['avg_night_temp'])} °C\n"
            if weather_data[loc]["rainy_days"]:
                weather_response += (
                    f"• Rainy days: {', '.join(weather_data[loc]['rainy_days'])}\n"
                )

    await update.message.reply_html(
        weather_response,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


travel_info_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("travel_info", choose_travel_info),
    ],
    states={
        GET_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_travel_info)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)

user_travels_handler = CommandHandler("my_travels", get_travels)
