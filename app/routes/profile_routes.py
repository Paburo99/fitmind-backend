from flask import Blueprint, request, jsonify
from db import get_db_client
from auth_utils import token_required

profile_bp = Blueprint('profile_bp', __name__)
supabase = get_db_client()

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user_id):
    try:
        response = supabase.table('profiles').select('*').eq('user_id', current_user_id).execute()
        
        if response is None: 
            print(f"Error getting profile: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (response was None)'}), 500

        if not hasattr(response, 'data'):
            print(f"Error getting profile: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching profile data', 'details': 'Malformed database response'}), 500

        # response.data will be a list.
        # Empty list means not found.
        # List with one item is a successful find.
        # List with more than one item (if user_id should be unique) is an issue.

        if len(response.data) == 1:
            return jsonify(response.data[0]), 200
        elif not response.data: # Empty list
            return jsonify({'message': 'Profile not found or not yet created.'}), 404
        else:
            # This case should ideally not happen if user_id is a unique constraint.
            # But it's good to handle defensively.
            print(f"Warning: Multiple profiles found for user_id {current_user_id} when expecting one or none.")
            # You might return the first, or an error, depending on desired logic
            return jsonify({'error': 'Inconsistent data: Multiple profiles found'}), 500
            
    except Exception as e:
        print(f"Error getting profile: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching profile data', 'details': details}), 500

@profile_bp.route('/profile', methods=['POST', 'PUT'])
@token_required
def upsert_profile(current_user_id):
    profile_data_req = request.json
    if not profile_data_req:
        return jsonify({'error': 'No data provided'}), 400    # Add user_id from token
    profile_data_req['user_id'] = current_user_id

    required_fields = ['primary_goal', 'fitness_level', 'date_of_birth', 'gender', 'height_cm', 'initial_weight_kg', 'activity_level']
    optional_fields = ['weekly_workout_goal', 'daily_activity_goal']
    
    for field in required_fields:
        if field not in profile_data_req or profile_data_req[field] is None or str(profile_data_req[field]).strip() == '':
            return jsonify({'error': f'Missing or empty required field: {field}'}), 400
    
    # Set default values for optional goal fields if not provided
    if 'weekly_workout_goal' not in profile_data_req or profile_data_req['weekly_workout_goal'] is None:
        profile_data_req['weekly_workout_goal'] = 5
    if 'daily_activity_goal' not in profile_data_req or profile_data_req['daily_activity_goal'] is None:
        profile_data_req['daily_activity_goal'] = 3
    
    try:
        # Check existence
        check_response = supabase.table('profiles').select('user_id').eq('user_id', current_user_id).execute()

        if check_response is None:
            print(f"Error upserting profile: Supabase client returned None during existence check. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (existence check response was None)'}), 500
        
        if not hasattr(check_response, 'data'):
             print(f"Error upserting profile: Supabase response object malformed during existence check (missing 'data'). User: {current_user_id}")
             return jsonify({'error': 'Failed to check existing profile', 'details': 'Malformed database response'}), 500


        db_operation_response = None
        status_code = 0

        if check_response.data: # Profile exists, so update
            db_operation_response = supabase.table('profiles').update(profile_data_req).eq('user_id', current_user_id).execute()
            status_code = 200
        else: # Profile does not exist, so insert
            db_operation_response = supabase.table('profiles').insert(profile_data_req).execute()
            status_code = 201

        if db_operation_response is None:
            print(f"Error upserting profile: Supabase client returned None during insert/update. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (insert/update response was None)'}), 500

        if not hasattr(db_operation_response, 'data'):
            print(f"Error upserting profile: Supabase response object malformed during insert/update (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Failed to save profile', 'details': 'Malformed database response after insert/update'}), 500

        if not db_operation_response.data: # Insert/Update should return data
            print(f"Error upserting profile: No data returned after insert/update and no exception. User: {current_user_id}")
            return jsonify({'error': 'Failed to save profile', 'details': 'No data returned after database operation'}), 500
        
        return jsonify(db_operation_response.data[0]), status_code
        
    except Exception as e:
        print(f"Error saving profile: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Failed to save profile', 'details': details}), 500