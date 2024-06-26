import os
from dotenv import load_dotenv

load_dotenv()
MONGO_CONN_STRING = os.getenv('MONGO_CONN_STRING')
BOT_API_KEY = os.getenv('BOT_API_KEY')