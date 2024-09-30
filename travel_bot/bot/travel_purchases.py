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
from travel_bot.db_models import user, travel
from travel_bot.bot.validators import sign_up_required, validate_purchase


CHOOSE_TRAVEL, CHOOSE_ACTION, PURCHASE_SUM, ADD_PURCHASE, SEE_PURCHASES = range(5)


@sign_up_required
async def edit_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    reply_keyboard = [["add"], ["see"], ["end"]]
    await update.message.reply_html(
        "Choose action (type action's name): see purchases or add new purchase \n",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return CHOOSE_ACTION


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_action = update.message.text
    match user_action.lower():
        case "add":
            await update.message.reply_html("Enter purchase summary")
            return PURCHASE_SUM
        case "see":
            await see_purchases(update, context)
        case "end":
            return ConversationHandler.END
        case _:
            await update.message.reply_html("Sorry, action is invalid")
            return CHOOSE_ACTION


async def get_purchase_sum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    purchase = update.message.text
    if not validate_purchase(purchase):
        await update.message.reply_html("Sorry, purchase is invalid")
        return PURCHASE_SUM
    await update.message.reply_html("Now add note")
    context.user_data["purchase"] = purchase
    return ADD_PURCHASE


async def add_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_travel = travel.Travel.get_user_and_invited_travel(
        context.user_data["travel_name"], update.effective_user.id
    )
    purchase = context.user_data["purchase"]
    note = update.message.text
    travel.TravelPurchase.add_purchase(
        user_travel.id, update.effective_user.id, purchase, note
    )
    reply_keyboard = [["add"], ["see"], ["end"]]
    await update.message.reply_html("Purchase added", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE_ACTION


async def see_purchases(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_travel = travel.Travel.get_user_and_invited_travel(
        context.user_data["travel_name"], update.effective_user.id
    )
    if not user_travel.purchases:
        reply_keyboard = [["add"], ["see"], ["end"]]
        await update.message.reply_html("Travel has no purchases, you can add one", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return CHOOSE_TRAVEL

    response = "Travel purchases: \n"
    for person in [user_travel.owner] + user_travel.invited_users:
        person_purchases = travel.TravelPurchase.get_user_purchases(person.id)
        if not person_purchases:
            continue
        response += f"\n{person.tg_username} purchases: \n"
        for idx, purchase in enumerate(person_purchases, start=1):
            response += f"{idx}. {purchase.price} ({purchase.note}) on {datetime.date.strftime(purchase.on_date, '%d-%m-%Y')}\n"
        response += f"{person.tg_username} total: {travel.TravelPurchase.get_user_total_price(person.id)} \n"

    reply_keyboard = [["add"], ["see"], ["end"]]
    await update.message.reply_html(response, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE_ACTION


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = main_page_keyboard
    await update.message.reply_html(
        "Hope you'll come back later!",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ConversationHandler.END


purchases_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("travel_purchases", edit_purchases)],
    states={
        CHOOSE_TRAVEL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose_travel)
        ],
        CHOOSE_ACTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose_action)
        ],
        PURCHASE_SUM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_purchase_sum)
        ],
        ADD_PURCHASE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, add_purchase)
        ],
        SEE_PURCHASES: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, see_purchases)
        ]
    },
    fallbacks=[CommandHandler("stop", stop)],
)
