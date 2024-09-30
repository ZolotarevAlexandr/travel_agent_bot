import datetime

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.bot.validators import (
    must_have_travels,
    validate_city,
    validate_travel_dates,
    validate_travel_description,
    validate_travel_name,
    sign_up_required,
)
from travel_bot.db_models import user, travel, city

(
    CHOOSE_COLUMN,
    EDIT_COLUMN,
    NAME,
    DESCRIPTION,
    LOCATIONS,
    SPECIFY_LOCATION,
    START_DATE,
    END_DATE,
    INVITE,
    DELETE,
    CONFIRM_DELETE,
) = range(11)
LEAVE_TRAVEL = 11


@must_have_travels
async def choose_travel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = user.User.get_user_by_tg_id(update.effective_user.id)
    available_travels = db_user.travels

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
    return CHOOSE_COLUMN


async def choose_column(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_name = update.message.text
    edited_travel = travel.Travel.get_user_travel(travel_name, update.effective_user.id)
    if edited_travel is None:
        await update.message.reply_html("Sorry, travel name is invalid")
        return CHOOSE_COLUMN
    context.user_data["edited_travel_name"] = edited_travel.name

    reply_keyboard = [
        [option]
        for option in (
            "name",
            "description",
            "locations",
            "dates",
            "invited users",
            "delete",
            "end",
        )
    ]
    await update.message.reply_html(
        "Choose value to edit: name, description, locations, dates, invited users. You can also type 'delete' to delete travel, 'edit_notes' to manage travel's notes or 'end' to finish editing",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDIT_COLUMN


async def edit_column(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    match update.message.text.lower():
        case "name":
            await update.message.reply_html(
                f"Current name: {edited_travel.name}. Enter new name",
                reply_markup=ReplyKeyboardRemove(),
            )
            return NAME
        case "description":
            await update.message.reply_html(
                f"Current description: {edited_travel.description}. Enter new description",
                reply_markup=ReplyKeyboardRemove(),
            )
            return DESCRIPTION
        case "locations":
            travel.Travel.remove_locations(edited_travel.id)
            await update.message.reply_html(
                f"Current locations ({', '.join([loc.name for loc in edited_travel.locations])}) deleted. Enter new locations. Send 'end' when you're done",
                reply_markup=ReplyKeyboardRemove(),
            )
            return LOCATIONS
        case "dates":
            await update.message.reply_html(
                f"Current dates: {edited_travel.start_date} - {edited_travel.end_date}. Enter new dates",
                reply_markup=ReplyKeyboardRemove(),
            )
            return START_DATE
        case "invited users":
            travel.Travel.remove_users(edited_travel.id)
            await update.message.reply_html(
                f"Current invited users ({', '.join([user.username for user in edited_travel.invited_users])}) deleted. Invite new users. Send 'end' when you're done",
                reply_markup=ReplyKeyboardRemove(),
            )
            return INVITE
        case "delete":
            await update.message.reply_html(
                f"Are you sure you want to delete travel {context.user_data['edited_travel_name']}? Type 'yes' to confirm or 'no' to cancel",
                reply_markup=ReplyKeyboardRemove(),
            )
            return DELETE
        case "end":
            reply_keyboard = main_page_keyboard
            await update.message.reply_html(
                "Travel editing finished",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return ConversationHandler.END

    reply_keyboard = [
        [option]
        for option in (
            "name",
            "description",
            "locations",
            "dates",
            "invited users",
            "delete",
            "end",
        )
    ]
    await update.message.reply_html(
        "Sorry, value is invalid",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDIT_COLUMN


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    new_name = update.message.text
    if (
        not validate_travel_name(new_name, update.effective_user.id)
        and new_name != edited_travel.name
    ):
        await update.message.reply_html("Sorry, name is invalid")
        return NAME

    travel.Travel.edit_value(edited_travel.id, "name", new_name)

    reply_keyboard = [
        [option]
        for option in (
            "name",
            "description",
            "locations",
            "dates",
            "invited users",
            "delete",
            "end",
        )
    ]
    await update.message.reply_html(
        "Travel name changed. Choose new value to edit or type 'end' to finish editing",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDIT_COLUMN


async def edit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    new_description = update.message.text
    if not validate_travel_description(new_description):
        await update.message.reply_html("Sorry, description is invalid")
        return DESCRIPTION

    travel.Travel.edit_value(edited_travel.id, "description", new_description)

    reply_keyboard = [
        [option]
        for option in (
            "name",
            "description",
            "locations",
            "dates",
            "invited users",
            "delete",
            "end",
        )
    ]
    await update.message.reply_html(
        "Travel description changed. Choose new value to edit or type 'end' to finish editing",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDIT_COLUMN


async def edit_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    location = update.message.text

    if location == "end" and not edited_travel.locations:
        await update.message.reply_html("Sorry, you should add at least one location")
        return LOCATIONS

    if location == "end":
        reply_keyboard = [
            [option]
            for option in (
                "name",
                "description",
                "locations",
                "dates",
                "invited users",
                "delete",
                "end",
            )
        ]
        await update.message.reply_html(
            "Locations changed. Choose new value to edit or type 'end' to finish editing",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return EDIT_COLUMN

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
        travel.Travel.add_location(edited_travel.id, found_locations[0].id)
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
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    idx = update.message.text
    found_locations = context.user_data["found_locations"]

    if not (0 < int(idx) <= len(found_locations)):
        await update.message.reply_html("Sorry, index is invalid")
        return SPECIFY_LOCATION

    travel.Travel.add_location(edited_travel.id, found_locations[int(idx) - 1].id)
    await update.message.reply_html("Location added")
    return LOCATIONS


async def edit_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_start_date = update.message.text
    context.user_data["travel_start_date"] = travel_start_date
    await update.message.reply_html("Great, now input new end date of your travel")
    return END_DATE


async def edit_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    travel_end_date = update.message.text

    if not validate_travel_dates(
        context.user_data["travel_start_date"], travel_end_date
    ):
        await update.message.reply_html("Sorry, dates are invalid")
        return START_DATE

    start_date = datetime.datetime.strptime(
        context.user_data["travel_start_date"], "%d.%m.%Y"
    )
    end_date = datetime.datetime.strptime(travel_end_date, "%d.%m.%Y")
    travel.Travel.edit_value(edited_travel.id, "start_date", start_date)
    travel.Travel.edit_value(edited_travel.id, "end_date", end_date)

    reply_keyboard = [
        [option]
        for option in (
            "name",
            "description",
            "locations",
            "dates",
            "invited users",
            "delete",
            "end",
        )
    ]
    await update.message.reply_html(
        "Travel dates changed. Choose new value to edit or type 'end' to finish editing",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return EDIT_COLUMN


async def invited(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    edited_travel = travel.Travel.get_user_travel(
        context.user_data["edited_travel_name"], update.effective_user.id
    )
    invited_user_name = update.message.text
    if invited_user_name == "end":
        reply_keyboard = [
            [option]
            for option in (
                "name",
                "description",
                "locations",
                "dates",
                "invited users",
                "delete",
                "end",
            )
        ]
        await update.message.reply_html(
            "Users are invited. Choose new value to edit or type 'end' to finish editing",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return EDIT_COLUMN

    invited_user = user.User.get_user_by_tg_username(invited_user_name)
    if invited_user is None:
        await update.message.reply_html(
            "Sorry user is not found. Maybe user is not registered"
        )
        return INVITE

    travel.Travel.invite_user(edited_travel.id, invited_user.id)
    await update.message.reply_html("User invited")
    return INVITE


async def delete_chosen_travel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_input = update.message.text
    match user_input.lower():
        case "yes":
            travel_name = context.user_data["edited_travel_name"]
            travel.Travel.delete_travel(travel_name, update.effective_user.id)
            reply_keyboard = main_page_keyboard
            await update.message.reply_html(
                "Travel deleted",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return ConversationHandler.END
        case "no":
            reply_keyboard = [
                [option]
                for option in (
                    "name",
                    "description",
                    "locations",
                    "dates",
                    "invited users",
                    "delete",
                    "end",
                )
            ]
            await update.message.reply_html(
                "Travel **not** deleted. Choose new value to edit or type 'end' to finish editing",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return EDIT_COLUMN
        case _:
            await update.message.reply_html("Sorry, value is invalid")
            return DELETE


@sign_up_required
async def leave_travel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    db_user = user.User.get_user_by_tg_id(update.effective_user.id)
    invited_to = db_user.invited_travels
    if not invited_to:
        reply_keyboard = main_page_keyboard
        await update.message.reply_html(
            "You don't have any invites",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return ConversationHandler.END
    response = "Which travel you want to leave (type travel's name): \n"
    for user_invited_travel in invited_to:
        response += f"• {user_invited_travel.name}\n"

    reply_keyboard = [[user_invited_travel.name] for user_invited_travel in invited_to]
    await update.message.reply_html(
        response,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return LEAVE_TRAVEL


async def leave_chosen_travel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_input = update.message.text
    travel_name = user_input
    user_travel = travel.Travel.get_user_and_invited_travel(
        travel_name, update.effective_user.id
    )
    travel.Travel.remove_user(user_travel.id, update.effective_user.id)
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Travel left",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


edit_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_travel", choose_travel_edit)],
    states={
        CHOOSE_COLUMN: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_column)],
        EDIT_COLUMN: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_column)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_name)],
        DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, edit_description)
        ],
        LOCATIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_locations)],
        SPECIFY_LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, specify_location)
        ],
        START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_start_date)],
        END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_end_date)],
        INVITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, invited)],
        DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_chosen_travel)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)

leave_travel_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("leave_travel", leave_travel)],
    states={
        LEAVE_TRAVEL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, leave_chosen_travel)
        ],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
