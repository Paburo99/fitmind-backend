from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.profile_routes import profile_bp
from routes.log_routes import log_bp
from routes.dashboard_routes import dashboard_bp
from routes.recommend_routes import recommend_bp
from routes.progress_routes import progress_bp
from routes.chat_routes import chat_bp
from db import get_db_client # To ensure it's initialized on startup

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.FLASK_SECRET_KEY # Important for session management if you use Flask sessions

# Initialize Supabase client (optional here if all calls are within routes that call get_db_client)
try:
    get_db_client()
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Failed to initialize Supabase client on startup: {e}")


# CORS Configuration
CORS(app, resources={r"/api/*": {"origins": Config.CLIENT_ORIGIN_URL}}, supports_credentials=True)

# Register Blueprints
app.register_blueprint(profile_bp, url_prefix='/api')
app.register_blueprint(log_bp, url_prefix='/api') # /api/log/workout etc.
app.register_blueprint(dashboard_bp, url_prefix='/api') # /api/dashboard/summary
app.register_blueprint(recommend_bp, url_prefix='/api') # /api/recommend/workout
app.register_blueprint(progress_bp, url_prefix='/api') # /api/progress/weight
app.register_blueprint(chat_bp, url_prefix='/api') # /api/chat/context-aware

@app.route('/')
def home():
    return "FitTrack AI Flask Backend is running!"

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "API is up and running"}), 200

if __name__ == '__main__':
    # This is for local development only. Gunicorn is used in Docker for production.
    app.run(host='0.0.0.0', port=10000, debug=True)