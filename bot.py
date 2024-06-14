

import logging
import re

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils.keys import BOT_API_KEY
from db import DBClient
from module_allocator import ModuleAllocator
from utils.helpers import user_days_to_array

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

db = DBClient()

SEMESTER, MODS, DELETE, BLOCK_DAYS, FINISH = range(5)

MAX_NO_OF_MODULES = 8

# RETURN A URL
sample_url = "https://nusmods.com/timetable/sem-2/share?CS2030S=LAB:14F,REC:15,LEC:2&CS2040S=TUT:32,LEC:2,REC:08&ES2660=SEC:G08&IS1128=LEC:1&MA1521=TUT:16,LEC:1"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the modules they would be taking."""

    await update.message.reply_text(
        "Hi! Welcome to PlanBetterLah!, where we will help you to achieve your ideal timetable!\n\n"
        "Send /cancel to stop the conversation at any time.\n\n"
        "To start off, please let me know which semester you are planning for.", reply_markup=ReplyKeyboardMarkup([["1","2"]], one_time_keyboard=True, resize_keyboard=True)
    )

    return SEMESTER

async def sem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores which semester the user is querying for and asks about the modules they would be taking"""
    user = update.message.from_user
    semester = update.message.text.strip()

    if semester not in ["1", "2"]:
        await update.message.reply_text(
            "Invalid semester. Please enter 1 or 2."
        )
        return SEMESTER

    context.user_data['semester'] = semester
    context.user_data['modules'] = []

    await update.message.reply_text(
        f"Great! You're planning for semester {semester}.\n\n"
        "Now, please let me know what modules you would be taking one at a time. Eg. CS1101S.",
    )
    return MODS

async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the user's modules"""
    user = update.message.from_user
    module = update.message.text.strip()

     # Check if the user is done
    if module.lower() == "/done":
        return await done(update, context)
    
    # Check if the user wants to delete
    if module.lower() == "/delete":
        return await delete(update, context)
        
     # Check if the user wants to cancel
    if module.lower() == "/cancel":
        return await cancel(update, context)

    #Check for punctuation
    if re.search(r'[^\w\s]', module):
        await update.message.reply_text(
            "Module names should not contain any punctuation. Please enter a valid module name. Eg. CS1101S"
        )
        return MODS
    
    modules = context.user_data['modules']
   # Only accept single-word module names
    if len(module.split()) == 1:
        module = module.upper()
        #Check for duplicates
        if module in modules:
            await update.message.reply_text(
                f"The module '{module}' is already in your list. Please enter a different module."
            )
        else:
            #check for valid mod
            semester = context.user_data["semester"]
            if db.check_valid_mod(module, semester):
                if len(modules) >= MAX_NO_OF_MODULES:
                    await update.message.reply_text(
                        "Maximum number of modules allowed per semester reached. Please send /delete and delete a module before adding more."
                    )
                    return MODS
                
                modules.append(module)
                logger.info("User %s is taking module: %s", user.first_name, module)
                if len(modules) == MAX_NO_OF_MODULES:
                    await update.message.reply_text(
                        f"Got it! Current list of modules is: {modules}\n\n"
                        "Maximum number of modules allowed per semester reached. Please send /done to manage your current selection of modules.\n\n"
                        "If you wish to delete any modules, please send /delete and choose the module you wish to delete.\n\n"
                    )
                else:
                    await update.message.reply_text(
                        f"Got it! Current list of modules is: {modules}\n\n"
                        "Do you want to add more modules? If yes, please enter the next module name. Otherwise, send /done to manage your current selection of modules."
                    )
            else:
                await update.message.reply_text(
                    f"Invalid module name or {module} is not offered in sem {semester}. Please ensure that you enter the module name correctly. Eg. CS1101S."
                )
    else:
        await update.message.reply_text("Please enter only one module name at a time.")
        return MODS

    return MODS


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Collects all the modules to generate URL"""
    user = update.message.from_user
    logger.info("User %s has completed the module input.", user.first_name)
    modules = context.user_data['modules']
    if len(modules) == MAX_NO_OF_MODULES:
            await update.message.reply_text(
        f"Great! Here is the list of modules you've entered: {modules}\n\n"
        "If it is correct, please send /generate to get your timetable URL.\n\n"
        "If you wish to delete any modules, please send /delete and choose the module you wish to delete."
        )
    else:
        await update.message.reply_text(
            f"Great! Here is the list of modules you've entered: {modules}\n\n"
            "If it is correct, please send /generate to get your timetable URL.\n\n"
            "If you wish to delete any modules, please send /delete and choose the module you wish to delete.\n\n"
            "If you wish to add more modules, please send the module name directly instead."
        )

    return MODS

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks the user to select a module to delete"""
    modules = context.user_data.get('modules', [])

    if not modules:
        await update.message.reply_text(
            "No modules to delete. Please add some modules first."
        )
        return MODS

    keyboard = [[module] for module in modules]
    keyboard.append(["Cancel"])

    await update.message.reply_text(
        "Please choose the module you want to delete:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

    return DELETE
    
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms the deletion of the selected module"""
    user = update.message.from_user
    selected_module = update.message.text
    modules = context.user_data.get('modules', [])
    
    logger.info("User %s is trying to delete module: %s", user.first_name, selected_module)
    logger.info("Current list of modules: %s", modules)

    if selected_module == "Cancel":
        if selected_module in modules:
            modules.remove(selected_module)
        await update.message.reply_text(
                f"Current list of modules is: {context.user_data['modules']}\n\n"
                "Please continue adding more modules or send /done to manage your current selection of modules."
            )
        return MODS

    if selected_module in modules:
        modules.remove(selected_module)
        await update.message.reply_text(
            f"Module '{selected_module}' has been deleted. Current list of modules is: {context.user_data['modules']}\n\n"
            "Please continue adding more modules or send /done to manage your current selection of modules."
        )
    else:
        await update.message.reply_text(
            "Invalid module selection. Please choose a module from the list."
        )
        return DELETE  # Return to the DELETE state to prompt for a valid selection

    return MODS

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generates the URL for the timetable and ends the conversation"""
    user = update.message.from_user
    modules = context.user_data.get('modules', [])

    if not modules:
        await update.message.reply_text(
            "No modules have been added. Please add some modules first."
        )
        return MODS
    
    await update.message.reply_text(
        "Please indicate the specific days you wish to exclude from your timetable planning. Use numbers to denote each day, starting with Monday as 1 (eg. '1, 2, 3') \n\n"
        "If you do not have any particular preferences, please send 'skip'"
    )
    return BLOCK_DAYS

async def block_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    modules = context.user_data.get('modules', [])
    message = update.message.text.strip()
    blocked_out_days = []
    if message.lower() == "skip":
        logger.info("User %s has opted to skip blocking days step", user.first_name)    

    else: 
        avail_days = ['1', '2', '3', '4', '5']
        blocked_out_days = user_days_to_array(message) # Add user input for blocked out days
        for day in blocked_out_days:
            if re.search(r'[^\w\s]', day):
                await update.message.reply_text(
                    "Please do not include any other types of punctuation. Use numbers to denote each day, starting with Monday as 1 (eg. '1, 2, 3') "
                )

                return BLOCK_DAYS
            
            elif day in ['6', '7']:
                await update.message.reply_text(
                    "No lessons are conducted on the weekends. Please only input numbers from 1 to 5, where Monday is represented by 1, in the following format: '1, 2, 3' "
                )

                return BLOCK_DAYS
            
            elif day in avail_days:
                continue

            else:
                await update.message.reply_text(
                    "Invalid input received. Please ensure that you only input numbers from 1 to 5, where Monday is represented by 1, in the following format: '1, 2, 3' "
                )

                return BLOCK_DAYS
        
        blocked_out_days = [int(x) for x in blocked_out_days]
        logger.info("User %s has indicated the following blocked_out_days: %s", user.first_name, blocked_out_days)    
    allocator = ModuleAllocator(modules, blocked_out_days)
    db.draw_module_info(modules, context.user_data["semester"])
    return await finish(update, context)

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s has received URL", user.first_name)
    await update.message.reply_text(
        f"Great! Please refer to the following URL for your timetable. {sample_url}\n\nThank you for using PlanBetterLah!",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! Thank you for using PlanBetterLah!", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_API_KEY).build()

    # Add conversation handler with the states MODS
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SEMESTER:[MessageHandler(filters.TEXT & ~filters.COMMAND, sem)],
            MODS: [MessageHandler(filters.TEXT & ~filters.COMMAND, mods)],
            DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete)],
            BLOCK_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, block_days)],
            FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)]
        },
        fallbacks=[CommandHandler("done", done), CommandHandler("delete", delete), CommandHandler("generate", generate), CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

