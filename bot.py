

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
from keys import BOT_API_KEY

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MODS = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the modules they would be taking."""

    await update.message.reply_text(
        "Hi! Welcome to PlanBetterLah!, where we will help you to achieve your ideal timetable!"
        "Send /cancel to stop the conversation at any time.\n\n"
        "To start off, please let me know what modules you would be taking one at a time",
    )
    context.user_data['modules'] = []

    return MODS


async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's modules"""
    user = update.message.from_user
    module = update.message.text.strip()

     # Check if the user is done
    if module.lower() == "/done":
        return await done(update, context)
        
     # Check if the user wants to cancel
    if module.lower() == "/cancel":
        return await cancel(update, context)

   # Only accept single-word module names
    if len(module.split()) == 1:
        context.user_data['modules'].append(module)
        logger.info("User %s is taking module: %s", user.first_name, module)
        await update.message.reply_text(
            f"Got it! Current list of modules is: {context.user_data['modules']}\n"
            "Do you want to add more modules? If yes, enter the next module name. Otherwise, send /done."
        )

    else:
        await update.message.reply_text("Please enter only one module name at a time.")
        return MODS

    return MODS


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ends the conversation after collecting all modules"""
    user = update.message.from_user
    logger.info("User %s has completed the module input.", user.first_name)
    await update.message.reply_text(
        f"Great! Here is the list of modules you've entered: {context.user_data['modules']}\nThank you for using PlanBetterLah!",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END
    
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
    application = Application.builder().token(BOT_API_KEY).build()

    # Add conversation handler with the states MODS, ADD_MORE
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MODS: [MessageHandler(filters.TEXT & ~filters.COMMAND, mods)],
        },
        fallbacks=[CommandHandler("done", done), CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

# RETURN A URL
#sample_url = "https://nusmods.com/timetable/sem-2/share?CS2030S=LAB:14F,REC:15,LEC:2&CS2040S=TUT:32,LEC:2,REC:08&ES2660=SEC:G08&IS1128=LEC:1&MA1521=TUT:16,LEC:1"
