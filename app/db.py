from supabase import create_client, Client
from .config import Config

try:
    supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY) # Use service role for backend
    # If you only want to operate in user context after they log in via frontend,
    # you might pass the user's JWT from frontend to backend and initialize client per request:
    # supabase_client.auth.set_session(access_token, refresh_token)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase_client = None

def get_db_client():
    if not supabase_client:
        raise Exception("Supabase client not initialized. Check credentials and connection.")
    return supabase_client
