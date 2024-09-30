from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    MessageHandler,
)

from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.db_models import user, travel
from travel_bot.bot.validators import sign_up_required

CHOOSE_TRAVEL, CHOOSE_ACTION, CHOOSE_IS_PUBLIC, ADD_NOTE, REMOVE_NOTE = range(5)


@sign_up_required
async def edit_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    reply_keyboard = [[travel_name.name] for travel_name in available_travels]
    await update.message.reply_html(
        response,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSE_TRAVEL


async def choose_travel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    travel_name = update.message.text
    context.user_data["travel_name"] = travel_name
    tg_user = update.effective_user
    user_travel = travel.Travel.get_user_and_invited_travel(travel_name, tg_user.id)
    if user_travel is None:
        await update.message.reply_html("Sorry, travel name is invalid")
        return CHOOSE_TRAVEL

    travel_notes = user_travel.notes
    travel_notes = list(
        filter(
            lambda note: note.by_user_id == tg_user.id or note.is_public, travel_notes
        )
    )
    if not travel_notes:
        reply_keyboard = [["add"], ["end"]]
        await update.message.reply_html(
            "Travel has no notes, you can add one",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
    else:
        response = "Travel notes: \n"
        for idx, note in enumerate(travel_notes, start=1):
            response += f"{idx}. {note.by_user.tg_username}: {note.note}\n"
        await update.message.reply_html(response)

    reply_keyboard = [["add"], ["remove"], ["end"]]
    await update.message.reply_html(
        "You can add new note using 'add', remove one using 'remove' or finish editing using 'end'",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSE_ACTION


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_travel = travel.Travel.get_user_and_invited_travel(
        context.user_data["travel_name"], update.effective_user.id
    )
    travel_notes = user_travel.notes
    action = update.message.text
    match action.lower():
        case "add":
            reply_keyboard = [["public"], ["private"]]
            await update.message.reply_html(
                "Choose if note is public or not (type 'public' or 'private')",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return CHOOSE_IS_PUBLIC
        case "remove":
            if not travel_notes:
                await update.message.reply_html("Travel has no notes")
                return CHOOSE_ACTION
            if update.effective_user.id not in {
                note.by_user_id for note in travel_notes
            }:
                await update.message.reply_html(
                    "You don't have any notes in this travel"
                )
                return CHOOSE_ACTION
            await update.message.reply_html(
                "Choose note to remove by it's number. Note you can only delete your own notes"
            )
            return REMOVE_NOTE
        case "end":
            reply_keyboard = main_page_keyboard
            await update.message.reply_html(
                "Notes edited",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True
                ),
            )
            return ConversationHandler.END
        case _:
            await update.message.reply_html("Sorry, value is invalid")
            return CHOOSE_ACTION


async def choose_is_public(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text.lower()
    if user_choice.lower() == "public":
        context.user_data["is_public"] = True
    elif user_choice.lower() == "private":
        context.user_data["is_public"] = False
    else:
        await update.message.reply_html("Sorry, value is invalid")
        return CHOOSE_IS_PUBLIC
    await update.message.reply_html("Enter your note")
    return ADD_NOTE


async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_travel = travel.Travel.get_user_and_invited_travel(
        context.user_data["travel_name"], update.effective_user.id
    )
    note = update.message.text
    travel.TravelNote.add_note(
        user_travel.id, update.effective_user.id, note, context.user_data["is_public"]
    )
    reply_keyboard = [["add"], ["remove"], ["end"]]
    await update.message.reply_html(
        "Note added. You can add new one using 'add', remove one using 'remove' or finish editing using 'end'",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSE_ACTION


async def remove_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_travel = travel.Travel.get_user_and_invited_travel(
        context.user_data["travel_name"], update.effective_user.id
    )
    travel_notes = user_travel.notes
    travel_notes = list(
        filter(
            lambda note: note.by_user_id == update.effective_user.id or note.is_public,
            travel_notes,
        )
    )

    note_id = int(update.message.text)
    if not (0 < note_id <= len(travel_notes)):
        await update.message.reply_html("Sorry, index is invalid")
        return REMOVE_NOTE

    note_to_del = travel_notes[note_id - 1]
    if not note_to_del.by_user_id == update.effective_user.id:
        await update.message.reply_html(
            "Sorry, you can only delete your own notes. Choose another one or exit using /stop"
        )
        return REMOVE_NOTE

    travel.TravelNote.delete_note(note_to_del.id)
    await update.message.reply_html(
        "Note removed. You can add new one using 'add', remove one using 'remove' or finish editing using 'end'"
    )
    return CHOOSE_ACTION


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


notes_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("edit_notes", edit_notes)],
    states={
        CHOOSE_TRAVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_travel)],
        CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)],
        CHOOSE_IS_PUBLIC: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose_is_public)
        ],
        ADD_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_note)],
        REMOVE_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_note)],
    },
    fallbacks=[CommandHandler("stop", stop)],
)
