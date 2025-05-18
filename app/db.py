from supabase import create_client, Client
from config import Config

try:
    supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY) # Use service role for backend
    # If you only want to operate in user context after they log in via frontend,
    # you might pass the user's JWT from frontend to backend and initialize client per request:
    # supabase_client.auth.set_session(access_token, refresh_token)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase_client = None

def get_db_client():
    """
    Returns the Supabase client instance.
    If the globally initialized client is None (due to initial failure),
    this function will attempt to re-initialize it.
    """
    global supabase_client # Declare intent to use and potentially modify the global variable

    if supabase_client is None:
        print("INFO [get_db_client]: Global Supabase client is None. Attempting to initialize/re-initialize.")
        try:
            url = Config.SUPABASE_URL
            key = Config.SUPABASE_SERVICE_ROLE_KEY # Ensure this is the service role key

            if not url or not key:
                print("ERROR [get_db_client]: Supabase URL or Key is missing in Config. Cannot initialize.")
                # supabase_client remains None, will be caught by the final check
            else:
                print(f"INFO [get_db_client]: Initializing with URL: {url}, Key Set: {'Yes' if key else 'No'}")
                # Attempt to create and assign to the global variable
                new_client_instance = create_client(url, key)
                if new_client_instance:
                    supabase_client = new_client_instance # Assign to the global variable
                    print("INFO [get_db_client]: Supabase client re-initialized successfully.")
                else:
                    # This case might not be hit if create_client always raises an error on failure
                    print("ERROR [get_db_client]: create_client returned None without an exception during re-initialization.")
                    supabase_client = None # Ensure it's None
        
        except Exception as e:
            print(f"ERROR [get_db_client]: Failed to initialize/re-initialize Supabase client: {e}")
            supabase_client = None # Ensure it's None on failure

    # Final check after any attempt to initialize or re-initialize
    if supabase_client is None:
        # This means all attempts to get a client have failed.
        raise Exception(
            "Supabase client is not initialized and attempts to initialize failed. "
            "Check application logs for errors regarding Supabase URL/Key, "
            "connectivity, or other initialization issues."
        )
    
    return supabase_client