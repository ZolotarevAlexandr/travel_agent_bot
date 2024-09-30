import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.bot.validators import (
    sign_up_required,
    validate_city,
    validate_travel_dates,
    validate_travel_description,
    validate_travel_name,
)
from travel_bot.db_models import user, travel, city

NAME, DESCRIPTION, LOCATIONS, SPECIFY_LOCATION, START_DATE, END_DATE, INVITE = range(7)


@sign_up_required
async def start_travel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_html("Hi, let's add new travel")
    await update.message.reply_html(
        "First, input name of your travel. Note: name should be unique"
    )
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tg_user = update.effective_user
    travel_name = update.message.text

    if not validate_travel_name(travel_name, tg_user.id):
        await update.message.reply_html("Sorry, name is invalid")
        return NAME

    context.user_data["travel_name"] = travel_name
    await update.message.reply_html("Great, now add description of your travel.")
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_description = update.message.text

    if not validate_travel_description(travel_description):
        await update.message.reply_html("Sorry, description is invalid")
        return DESCRIPTION

    context.user_data["travel_description"] = travel_description
    await update.message.reply_html(
        "Great, now add cities of your travel. Send 'end' when you're done"
    )
    context.user_data["travel_locations"] = []
    return LOCATIONS


async def locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.text

    if location == "end" and not context.user_data["travel_locations"]:
        await update.message.reply_html("Sorry, you should add at least one location")
        return LOCATIONS

    if location == "end":
        await update.message.reply_html(
            "Great, now input start date of your travel (in format DD.MM.YYYY)"
        )
        return START_DATE

    loc_is_valid, hints = validate_city(location)

    if not loc_is_valid:
        response = "Sorry, location is invalid\n"
        if hints:
            response += "\nDid you mean one of these locations?"
        for idx, hint_city in enumerate(hints, start=1):
            response += f"\n{idx}. {hint_city.name} in {hint_city.country.name}, {hint_city.state_name}"
        await update.message.reply_html(response)
        return LOCATIONS

    found_locations = city.City.get_cities_by_name(location)
    if len(found_locations) == 1:
        context.user_data["travel_locations"].append(found_locations[0])
        await update.message.reply_html("Location added")
        return LOCATIONS

    context.user_data["found_locations"] = found_locations
    await update.message.reply_html(
        "There are multiple locations with this name. "
        "Please choose one by its number: \n"
    )
    loc_response = ""
    for idx, location in enumerate(found_locations, start=1):
        loc_response += f"{idx}. {location.name} in {location.country.name}, {location.state_name}\n"

    await update.message.reply_html(loc_response)
    return SPECIFY_LOCATION


async def specify_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    idx = update.message.text
    found_locations = context.user_data["found_locations"]

    if not (0 < int(idx) <= len(found_locations)):
        await update.message.reply_html("Sorry, index is invalid")
        return SPECIFY_LOCATION

    context.user_data["travel_locations"].append(found_locations[int(idx) - 1])
    await update.message.reply_html("Location added")
    return LOCATIONS


async def start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_start_date = update.message.text
    context.user_data["travel_start_date"] = travel_start_date
    await update.message.reply_html("Great, now input end date of your travel")
    return END_DATE


async def end_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_end_date = update.message.text

    if not validate_travel_dates(
        context.user_data["travel_start_date"], travel_end_date
    ):
        await update.message.reply_html("Sorry, dates are invalid")
        return START_DATE

    context.user_data["travel_end_date"] = travel_end_date

    new_travel = travel.Travel.create_travel(
        owner_id=update.effective_user.id,
        name=context.user_data["travel_name"],
        description=context.user_data["travel_description"],
        start_date=datetime.datetime.strptime(
            context.user_data["travel_start_date"], "%d.%m.%Y"
        ),
        end_date=datetime.datetime.strptime(
            context.user_data["travel_end_date"], "%d.%m.%Y"
        ),
    )

    for loc in context.user_data["travel_locations"]:
        travel.Travel.add_location(new_travel.id, loc.id)

    await update.message.reply_html(
        "Now you can invite other users "
        "(by their telegram username) to your travel. "
        "Note, that users have to be registered "
        "in the bot first"
    )
    await update.message.reply_html("Type 'end' to stop inviting")

    context.user_data["new_travel"] = new_travel
    return INVITE


async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    invited_user_name = update.message.text
    if invited_user_name == "end":
        reply_keyboard = main_page_keyboard
        await update.message.reply_html(
            "Travel created",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ConversationHandler.END

    invited_user = user.User.get_user_by_tg_username(invited_user_name)
    if invited_user is None:
        await update.message.reply_html(
            "Sorry user is not found. Maybe user is not registered"
        )
        return INVITE

    travel.Travel.invite_user(context.user_data["new_travel"].id, invited_user.id)
    await update.message.reply_html("User invited")
    return INVITE


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


new_travel_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("new_travel", start_travel),
    ],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        LOCATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, locations)],
        SPECIFY_LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, specify_location)
        ],
        START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_date)],
        END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, end_date)],
        INVITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, invite)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
