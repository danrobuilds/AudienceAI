import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load .env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_API_KEY") 

supabase: Client = create_client(url, key)