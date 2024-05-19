from supabase import create_client, Client
from keys import db_password, db_url, db_api_key

url, key = db_url, db_api_key
db = create_client(url, key)