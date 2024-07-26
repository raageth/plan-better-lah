import logging
import re

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from utils.keys import BOT_API_KEY
from algo.db import DBClient
from algo.mod_planner import ModPlanner
from utils.helpers import user_days_to_array, int_to_days, blockout_timings_cleaner, blocktimings_printer, blocked_time_merge

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

db = DBClient()

#Milestone 3
SEMESTER, MODS, DELETE, BLOCK_DAYS, CONFIRM_BLOCKDAYS, BLOCKOUT_TIMINGS, LIMIT_HOURS, FINISH = range(8)

MAX_NO_OF_MODULES = 10

# RETURN A URL
sample_url = "https://nusmods.com/timetable/sem-2/share?CS2030S=LAB:14F,REC:15,LEC:2&CS2040S=TUT:32,LEC:2,REC:08&ES2660=SEC:G08&IS1128=LEC:1&MA1521=TUT:16,LEC:1"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user about the modules they would be taking."""

    context.user_data.clear()

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
                        "Maximum number of modules allowed per semester reached. \n"
                        "Please send /delete and delete a module before adding more."
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
        "If you do not have any particular preferences, please click 'Skip'.\n\n"
        "If you only wish to exclude certain timings instead of the entire day, please click 'skip' and indicate your preference at the next step instead.",
        reply_markup=ReplyKeyboardMarkup([["Skip"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return BLOCK_DAYS

async def block_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks user for days to exclude from timetable planning"""
    user = update.message.from_user
    message = update.message.text.strip()
    if message.lower() == "skip":
        context.user_data['blocked_days'] = []
        logger.info("User %s has opted to skip blockout days", user.first_name) 
        await update.message.reply_text(
            "All days would be included in your timetable planning.\n\n"
            "Please click 'Continue' to confirm your selection.\n\n"
            "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
            reply_markup=ReplyKeyboardMarkup([["Continue", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return CONFIRM_BLOCKDAYS
    
    #User indicating blockout days
    avail_days = ['1', '2', '3', '4', '5', '6']
    blocked_out_days = user_days_to_array(message) # Add user input for blocked out days
    for day in blocked_out_days:
        if re.search(r'[^\w\s]', day):
            await update.message.reply_text(
                "Please do not include any other types of punctuation. Use numbers to denote each day, starting with Monday as 1 (eg. '1, 2, 3') "
            )

            return BLOCK_DAYS
        
        elif day == '7':
            await update.message.reply_text(
                "No lessons are conducted on Sunday. Please only input numbers from 1 to 6, where Monday is represented by 1, in the following format: '1, 2, 3' "
            )

            return BLOCK_DAYS
        
        elif day in avail_days:
            continue

        else:
            await update.message.reply_text(
                "Invalid input received. Please ensure that you only input numbers from 1 to 6, where Monday is represented by 1, in the following format: '1, 2, 3' "
            )

            return BLOCK_DAYS
    
    blocked_out_days = [int(x) for x in blocked_out_days] 
    string_blocked_out_days = [int_to_days(y) for y in blocked_out_days]
    context.user_data['blocked_days'] = blocked_out_days

    logger.info("User %s has opted to skip %s", user.first_name, string_blocked_out_days)  
    await update.message.reply_text(
        f"The following days will be excluded from your timetable planning: \n{string_blocked_out_days} \n\n"
        "Please click 'Continue' to confirm your selection.\n\n"
        "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
        reply_markup=ReplyKeyboardMarkup([["Continue", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_BLOCKDAYS

async def confirm_blockdays(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    message = update.message.text.strip()
    if message.lower() not in ['continue', 'edit']:
        await update.message.reply_text(
            "Invalid input received. Please ensure that you only click either 'Continue' or 'Edit'."
        )
        return CONFIRM_BLOCKDAYS
    
    if message.lower() == 'edit':
        await update.message.reply_text(
            "Please indicate the specific days you wish to exclude from your timetable planning. Use numbers to denote each day, starting with Monday as 1 (eg. '1, 2, 3') \n\n"
            "If you do not have any particular preferences, please click 'Skip'.\n\n"
            "If you only wish to exclude certain timings instead of the entire day, please click 'Skip' and indicate your preference at the next step instead.",
            reply_markup=ReplyKeyboardMarkup([["Skip"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return BLOCK_DAYS
    
    selected_slots = context.user_data.get('selected_slots', set())
    keyboards = create_timetable_keyboard(selected_slots)
    await update.message.reply_text(
        "Please select your unavailable timeslots and click 'Confirm' once you are done.\n\n"
        "If you do not have any particular preferences, please click 'Confirm' without selecting any timeslots.",
        reply_markup=keyboards
    )

    return BLOCKOUT_TIMINGS

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

def create_timetable_keyboard(selected_slots):
    # Define 1-hour timeslots
    timeslots = [
        "0800-0900", "0900-1000", "1000-1100", "1100-1200",
        "1200-1300", "1300-1400", "1400-1500", "1500-1600",
        "1600-1700", "1700-1800", "1800-1900", "1900-2000",
        "2000-2100"
    ]

    keyboard = []

    # Add the header row with days
    header_row = [InlineKeyboardButton("Timeslots                   ", callback_data="ignore")]
    header_row.extend([InlineKeyboardButton(day, callback_data="ignore") for day in DAYS])
    keyboard.append(header_row)

    # Add rows for each timeslot with the corresponding days
    for timeslot in timeslots:
        row = [InlineKeyboardButton(timeslot + "       ", callback_data="ignore")]
        for day in DAYS:
            if (day, timeslot) in selected_slots:
                text = "✅"
            else:
                text = "⬜"
            row.append(InlineKeyboardButton(text, callback_data=f"{day}:{timeslot}"))
        keyboard.append(row)

    # Add confirm button at the end
    confirm_row = [InlineKeyboardButton("Confirm                   ", callback_data="confirm")]
    keyboard.append(confirm_row)
    
    return InlineKeyboardMarkup(keyboard)

async def blockout_timings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    selected_slots = context.user_data.get('selected_slots', set())
    if query.data == "ignore":
        return BLOCKOUT_TIMINGS

    if query.data == "confirm":
        blocked_slots = blockout_timings_cleaner(selected_slots)
        context.user_data['blocked_slots'] = blocked_slots
        logger.info("Blocked out timings selected: %s", blocked_slots)
        if not selected_slots:
            await query.message.reply_text(
                "No timings have been selected.\n\n"
                "Please indicate the total number of hours you wish to limit your lessons to each day. (an integer between 2 - 24 inclusive)\n\n"
                "If you do not have any particular preferences, please click 'Skip'.\n\n"
                "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
                reply_markup=ReplyKeyboardMarkup([["Skip", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
            )
            return LIMIT_HOURS
        await query.message.reply_text(
            f"The following selected timings will be excluded from the planning:\n{blocktimings_printer(blocked_slots)}\n"
            "Please indicate the total number of hours you wish to limit your lessons to each day. (an integer between 2 - 24 inclusive)\n\n"
            "If you do not have any particular preferences, please click 'Skip'.\n\n"
            "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
            reply_markup=ReplyKeyboardMarkup([["Skip", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return LIMIT_HOURS

    day, timeslot = query.data.split(":")
    if (day, timeslot) in selected_slots:
        selected_slots.remove((day, timeslot))
    else:
        selected_slots.add((day, timeslot))

    context.user_data['selected_slots'] = selected_slots

    # Update the message with the new keyboard
    await query.edit_message_reply_markup(reply_markup=create_timetable_keyboard(selected_slots))
    return BLOCKOUT_TIMINGS

async def limit_hours(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    message = update.message.text.strip()
    
    if message.lower() == 'edit':
        selected_slots = context.user_data.get('selected_slots', set())
        keyboards = create_timetable_keyboard(selected_slots)
        await update.message.reply_text(
            "Please select your unavailable timeslots and click 'Confirm' once you are done.\n\n"
            "If you do not have any particular preferences, please click 'Confirm' without selecting any timeslots.",
            reply_markup=keyboards
        )

        return BLOCKOUT_TIMINGS
    
    if message.lower() == 'skip':
        logger.info("User %s has opted to skip attention span limiter", user.first_name)
        await update.message.reply_text(
            "No attention span limiter has been set.\n\n"
            "Please click 'Continue' to confirm your selection and generate your timetable.\n\n"
            "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
            reply_markup=ReplyKeyboardMarkup([["Continue", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return FINISH
    
    if message.isdigit():
        hours = int(message)
        if 2 <= hours <= 24:
            context.user_data["limit_hours"] = hours
            logger.info("Attention span limiter of %d hours set.", hours)
            await update.message.reply_text(
                f"Total number of lesson hours per day will be limited to {hours}.\n\n"
                "Please click 'Continue' to confirm your selection and generate your timetable.\n\n"
                "If you have made a mistake and would like to re-indicate your preference, please click 'Edit'.",
                reply_markup=ReplyKeyboardMarkup([["Continue", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
            )
            return FINISH
        else:
            await update.message.reply_text("Please ensure that the number entered is between 2 and 24 inclusive.")
            return LIMIT_HOURS
    else:
        await update.message.reply_text("Invalid input received. Please ensure that the number entered is between 2 and 24 inclusive without any extra symbols or letters.")
        return LIMIT_HOURS

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    message = update.message.text.strip()
    if message.lower() not in ['continue', 'edit']:
        await update.message.reply_text(
            "Invalid input received. Please ensure that you only click either 'Continue' or 'Edit'."
        )
        return FINISH
    
    if message.lower() == 'edit':
        await update.message.reply_text(
            "Please enter the total number of hours you wish to limit your lessons to each day\n\n"
            "If you do not have any particular preferences, please click 'Skip'.\n\n"
            "If you have made a mistake previously and would like to re-indicate your preference for your blockout timings, please click 'Edit'.",
            reply_markup=ReplyKeyboardMarkup([["Skip", "Edit"]], one_time_keyboard=True, resize_keyboard=True)
        )

        return LIMIT_HOURS
    
    modules = context.user_data.get('modules', [])
    semester = context.user_data["semester"]
    blocked_out_days = context.user_data.get('blocked_days', [])
    if not blocked_out_days:
        string_blocked_out_days = "All days are included in timetable planning."
    else:
        string_blocked_out_days = f"Days excluded from timetable planning: {[int_to_days(y) for y in blocked_out_days]}"

    blocked_out_timings = context.user_data.get('blocked_slots', list())
    string_timings = blocktimings_printer(blocked_out_timings)
    if string_timings == "":
        string_blocked_timings = "No blockout timings restrictions included in timetable planning.\n"
    else:
        string_blocked_timings = f"Blockout timings excluded from timetable planning:\n{string_timings}"

    max_hours = context.user_data.get('limit_hours', 24)
    if max_hours == 24:
        string_max_hours = "No attention span limiter has been set for total number of lesson hours per day."
    else: 
        string_max_hours = f"Limit on total number of lesson hours per day: {max_hours}"
    
    blocked_out_time = blocked_time_merge(blocked_out_days, blocked_out_timings)
    filtered_module_info = db.draw_filtered_module_info(modules, semester, blocked_out_days, blocked_out_timings)
    module_info = db.draw_distinct_info(modules, semester)
    logger.info("Finding timetable with the following information:")
    logger.info(f"modules: {modules}")
    logger.info(f"semester: {semester}")
    logger.info(f"max_hours: {max_hours}")
    logger.info(f"blocked_out_time: {blocked_out_time}")
    planner = ModPlanner(modules, module_info, semester, max_hours, blocked_out_time, filtered_module_info)
    solution = planner.solve()
    url = solution[0]
    violation_info = solution[1]
    error_message = solution[2]
    if not url:
        #Unable to find clashes
        if not error_message:
            logger.info("Unable to find optimal timetable even with relaxed constraints and no known clashes found.")
            await update.message.reply_text(
                "Sorry, we did not manage to find a timetable that meets all of the given constraints. Kindly check if there are clashes between the selected modules which cannot be resolved by timetable planning.\n\n"
                "Recap of list of conditions provided:\n"
                f"Semester: {semester}\n"
                f"Modules: {modules}\n"
                f"{string_blocked_out_days}\n"
                f"{string_blocked_timings}"
                f"{string_max_hours}\n\n"
                "Thank you for using PlanBetterLah!",
                reply_markup=ReplyKeyboardRemove(),
            )
            logger.info("Conversation with User %s has ended.", user.first_name)
            return ConversationHandler.END
        
        logger.info("No timetable found due to irreconcilable clashes between modules.")
        await update.message.reply_text(
            "Sorry, we did not manage to find a timetable that meets all of the given constraints. Kindly check if the selection of modules is valid.\n"
            f"{error_message}"
            "Recap of list of conditions provided:\n"
            f"Semester: {semester}\n"
            f"Modules: {modules}\n"
            f"{string_blocked_out_days}\n"
            f"{string_blocked_timings}"
            f"{string_max_hours}\n\n"
            "Thank you for using PlanBetterLah!",
            reply_markup=ReplyKeyboardRemove(),
        )
        logger.info("Conversation with User %s has ended.", user.first_name)
        return ConversationHandler.END

    elif violation_info:
        logger.info("Unable to find optimal timetable, found good approximation of timetable.")
        await update.message.reply_text(
            "Sorry, we did not manage to find a timetable that meets all of the given constraints. "
            f"Please refer to the following URL for a possible timetable with minimised relaxed constraints instead. \n{url}\n\n"
            f"Summary of constraints breached:\n {violation_info}\n"
            "Recap of list of conditions provided:\n"
            f"Semester: {semester}\n"
            f"Modules: {modules}\n"
            f"{string_blocked_out_days}\n"
            f"{string_blocked_timings}"
            f"{string_max_hours}\n\n"
            "Thank you for using PlanBetterLah!",
            reply_markup=ReplyKeyboardRemove(),
        )
        logger.info("Conversation with User %s has ended.", user.first_name)
        return ConversationHandler.END
    
    logger.info("User %s has received URL", user.first_name)
    await update.message.reply_text(
        f"Great! Please refer to the following URL for your timetable. {url}\n\n"
        "Please refer below for the list of conditions provided:\n"
        f"Semester: {semester}\n"
        f"Modules: {modules}\n"
        f"{string_blocked_out_days}\n"
        f"{string_blocked_timings}"
        f"{string_max_hours}\n\n"
        "Thank you for using PlanBetterLah!",
        reply_markup=ReplyKeyboardRemove(),
    )
    logger.info("Conversation with User %s has ended.", user.first_name)
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
            CONFIRM_BLOCKDAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_blockdays)],
            BLOCKOUT_TIMINGS: [CallbackQueryHandler(blockout_timings)], 
            LIMIT_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, limit_hours)],
            FINISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)]
        },
        fallbacks=[CommandHandler("done", done), CommandHandler("delete", delete), CommandHandler("generate", generate), CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

