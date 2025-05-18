import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file if present (for local dev)

print(f"DEBUG: SUPABASE_URL from env: {os.environ.get('SUPABASE_URL')}")
print(f"DEBUG: SUPABASE_KEY from env (is set): {os.environ.get('SUPABASE_KEY') is not None}")

class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # This should be the SERVICE_ROLE_KEY for admin actions, or ANON_KEY if backend acts as user
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # More secure for backend operations
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key") # Change this!
    CLIENT_ORIGIN_URL = os.environ.get("CLIENT_ORIGIN_URL", "http://localhost:5500") # Your Netlify URL in prod