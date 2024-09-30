import logging
import os

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

from travel_bot.bot.registration import register_conv_handler
from travel_bot.bot.add_travels import new_travel_conv_handler
from travel_bot.bot.edit_travel import edit_conv_handler, leave_travel_conv_handler
from travel_bot.bot.get_travel_info import (
    travel_info_conv_handler,
    user_travels_handler,
)
from travel_bot.bot.travel_purchases import purchases_conv_handler
from travel_bot.bot.travel_notes import notes_conv_handler
from travel_bot.keyboards.common import main_page_keyboard
from travel_bot.db_manager import db_session
from travel_bot.db_models import user

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    if user.User.get_user(tg_user.id):
        reply_keyboard = main_page_keyboard
        await update.message.reply_html(
            rf"Hi {tg_user.mention_html()}! Type /new_travel to add new travel",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return

    reply_keyboard = [["/sign_up"]]
    await update.message.reply_html(
        rf"Hi, {tg_user.mention_html()}. Before we start, we need some info about you. "
        rf"Type /sign_up to get started",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handlers(
        [
            CommandHandler("start", start),
            travel_info_conv_handler,
            register_conv_handler,
            new_travel_conv_handler,
            user_travels_handler,
            edit_conv_handler,
            leave_travel_conv_handler,
            notes_conv_handler,
            purchases_conv_handler,
        ]
    )
    logger.info("Starting bot...")
    application.run_polling()


if __name__ == "__main__":
    db_session.global_init()
    main()
