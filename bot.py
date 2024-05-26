

import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MODS, ADD_MORE = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the modules they would be taking."""

    await update.message.reply_text(
        "Hi! Welcome to PlanBetterLah!, where we will help you to achieve your ideal timetable!"
        "Send /cancel to stop the conversation at any time.\n\n"
        "To start off, please let me know what modules you would be taking one at a time",
    )

    return MODS


async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's modules"""
    user = update.message.from_user
    user_modules = update.message.text.split()
    if len(user_modules) == 1:
        await update.message.reply_text("Got it! Current list of modules is: %s", user_modules)
    else:
        await update.message.reply_text(
            "We can process one module at a time. Please enter only one module name."
        )
    return ADD_MORE

async def add_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user if they want to add more modules"""
    reply_text = "Do you want to add more modules? If yes, enter the next module name. Otherwise, send /done."
    await update.message.reply_text(reply_text)
    return MODS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("TOKEN").build()

    # Add conversation handler with the states MODS, ADD_MORE
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MODS: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
            ADD_MORE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_more)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

# RETURN A URL
sample_url = "https://nusmods.com/timetable/sem-2/share?CS2030S=LAB:14F,REC:15,LEC:2&CS2040S=TUT:32,LEC:2,REC:08&ES2660=SEC:G08&IS1128=LEC:1&MA1521=TUT:16,LEC:1"
