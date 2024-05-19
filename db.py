from supabase import create_client, Client
from keys import DB_PASSWORD, DB_URL, DB_API_KEY

url, key = DB_URL, DB_API_KEY
db = create_client(url, key)