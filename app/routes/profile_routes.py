from flask import Blueprint, request, jsonify
from db import get_db_client
from auth_utils import token_required

profile_bp = Blueprint('profile_bp', __name__)
supabase = get_db_client()

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        # For .maybe_single(), the first variable in the unpacked result is the dict itself or None.
        response = supabase.table('profiles').select('*').eq('user_id', current_user_id).maybe_single().execute()
        
        if response.error:
            # Handle potential errors during the query execution itself
            error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
            print(f"Error getting profile (query execution): {error_message}")
            return jsonify({'error': 'Error fetching profile data', 'details': error_message}), 500

        profile_data = response.data # profile_data will be the dict or None
        
        if profile_data: # profile_data is the dictionary of the profile if found
            return jsonify(profile_data), 200
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
    required_fields = ['primary_goal', 'fitness_level', 'date_of_birth', 'gender', 'height_cm', 'initial_weight_kg', 'activity_level'] # Ensure these match frontend required fields
    for field in required_fields:
        if field not in profile_data or profile_data[field] is None or profile_data[field] == '': # Check for empty strings too
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Using upsert to handle both creation and update
        # Ensure 'user_id' is part of your table's unique constraints or primary key for upsert to work as expected
        # The default behavior of upsert is to match on the primary key. If user_id is PK, it's fine.
        # If user_id is unique but not PK, specify on_conflict:
        # response = supabase.table('profiles').upsert(profile_data, on_conflict='user_id').execute()
        
        # Simpler: Check existence then insert or update
        check_response = supabase.table('profiles').select('user_id').eq('user_id', current_user_id).maybe_single().execute()

        if check_response.error:
            error_message = check_response.error.message if hasattr(check_response.error, 'message') else str(check_response.error)
            return jsonify({'error': 'Failed to check existing profile', 'details': error_message}), 500

        if check_response.data: # Profile exists, so update
            response = supabase.table('profiles').update(profile_data).eq('user_id', current_user_id).execute()
            status_code = 200
        else: # Profile does not exist, so insert
            response = supabase.table('profiles').insert(profile_data).execute()
            status_code = 201

        if response.error:
            error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
            return jsonify({'error': 'Failed to save profile', 'details': error_message}), 500
        
        if response.data and len(response.data) > 0:
            return jsonify(response.data[0]), status_code
        
        return jsonify({'error': 'Failed to save profile', 'details': 'No data returned after operation'}), 500
    except Exception as e:
        print(f"Error saving profile: {e}")
        return jsonify({'error': str(e)}), 500