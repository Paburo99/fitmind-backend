from flask import Blueprint, request, jsonify
from ..db import get_db_client
from ..auth_utils import token_required

profile_bp = Blueprint('profile_bp', __name__)
supabase = get_db_client()

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        # For .maybe_single(), the first variable in the unpacked result is the dict itself or None.
        data, count = supabase.table('profiles').select('*').eq('user_id', current_user_id).maybe_single().execute()
        
        if data: # data is the dictionary of the profile if found
            return jsonify(data), 200
        else:
            return jsonify({'message': 'Profile not found or not yet created.'}), 404
    except Exception as e:
        print(f"Error getting profile: {e}")
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/profile', methods=['POST', 'PUT'])
@token_required
def upsert_profile(current_user_id):
    profile_data = request.json
    if not profile_data:
        return jsonify({'error': 'No data provided'}), 400

    # Add user_id from token
    profile_data['user_id'] = current_user_id

    # Basic validation (add more as needed)
    required_fields = ['primary_goal', 'fitness_level'] # Adjust as per your schema
    for field in required_fields:
        if field not in profile_data or not profile_data[field]:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Using upsert to handle both creation and update
        # Ensure 'user_id' is part of your table's unique constraints or primary key for upsert to work as expected
        # Or check if exists then insert/update
        existing_profile_resp = supabase.table('profiles').select('user_id', count='exact').eq('user_id', current_user_id).maybe_single().execute()

        if existing_profile_resp.data: # .data from PostgrestAPIResponse is the dict or None for maybe_single()
            # Update existing profile
            data, count = supabase.table('profiles').update(profile_data).eq('user_id', current_user_id).execute()
        else: # Insert new profile
            data, count = supabase.table('profiles').insert(profile_data).execute()

        # After insert/update, data is a list of dictionaries
        if data and len(data) > 0:
            return jsonify(data[0]), 200 if request.method == 'PUT' else 201
        # The previous check 'if data and data[1]' was problematic.
        # data[0] from the response might contain error details if the operation failed at DB level but client didn't raise exception.
        # However, supabase-py usually raises an exception for PostgREST errors.
        # If data is empty or None, it implies failure or no data returned.
        error_details = data[0] if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) else 'No detailed response'
        return jsonify({'error': 'Failed to save profile', 'details': error_details}), 500
    except Exception as e:
        print(f"Error saving profile: {e}")
        return jsonify({'error': str(e)}), 500