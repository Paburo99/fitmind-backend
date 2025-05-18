import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file if present (for local dev)

class Config:
    SUPABASE_URL = os.environ.get("https://tchcbhzbnrqwsutslirr.supabase.co")
    SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRjaGNiaHpibnJxd3N1dHNsaXJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1MTYxNzcsImV4cCI6MjA2MzA5MjE3N30.e5FaC_mXBQCGpYAO3_dyQQKee2D1sGNfLfeNnkRJt3I") # This should be the SERVICE_ROLE_KEY for admin actions, or ANON_KEY if backend acts as user
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRjaGNiaHpibnJxd3N1dHNsaXJyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzUxNjE3NywiZXhwIjoyMDYzMDkyMTc3fQ.KhKM4krKRuyhKcfpf_c0sgYld34pHmY2O-Q2bufwNFk") # More secure for backend operations
    GEMINI_API_KEY = os.environ.get("AIzaSyB1PSPkO0fCJvkVpCd83JJ7Mjj4krNCuPU")
    FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "your_default_secret_key") # Change this!
    CLIENT_ORIGIN_URL = os.environ.get("fitmindproject.netlify.app", "http://localhost:5500") # Your Netlify URL in prod