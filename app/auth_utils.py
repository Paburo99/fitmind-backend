from functools import wraps
from flask import request, jsonify
from supabase import Client
from .db import get_db_client # Or initialize a client here per request

# This is a simplified version. Supabase client library handles JWT verification
# when you set the session or use its methods with a user's token.
# If you are passing the JWT in Authorization header from frontend:
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Bearer token malformed'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Use the existing service client from db.py to verify the token
            service_client = get_db_client()
            user_response = service_client.auth.get_user(token)
            current_user = user_response.user
            if not current_user:
                return jsonify({'message': 'Token is invalid or expired'}), 401
        except Exception as e:
            print(f"Token validation error: {e}")
            return jsonify({'message': 'Token is invalid or an error occurred'}), 401
        
        # Make user info available to the route
        # Be careful what you pass through; user.id is usually sufficient.
        kwargs['current_user_id'] = current_user.id
        return f(*args, **kwargs)
    return decorated_function