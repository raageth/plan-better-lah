import os
from dotenv import load_dotenv
load_dotenv()
MONGO_CONN_STRING = os.getenv('MONGO_CONN_STRING')
# MONGO_CONN_STRING = os.environ['MONGO_CONN_STRING']
BOT_API_KEY = os.getenv('BOT_API_KEY')
# BOT_API_KEY = os.environ['BOT_API_KEY']