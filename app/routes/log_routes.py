from flask import Blueprint, request, jsonify
from db import get_db_client
from auth_utils import token_required
from datetime import date

log_bp = Blueprint('log_bp', __name__)
supabase = get_db_client()

@log_bp.route('/log/workout', methods=['POST'])
@token_required
def log_workout(current_user_id):
    data = request.json
    if not data or not data.get('type') or not data.get('duration_minutes'):
        return jsonify({'error': 'Missing workout type or duration'}), 400

    workout_log_payload = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'type': data.get('type'),
        'duration_minutes': data.get('duration_minutes'),
        'calories_burned': data.get('calories_burned'),
        'notes': data.get('notes')
    }
    exercises_payload = data.get('exercises', []) # List of dictionaries for exercises
    workout_log_id = None

    try:
        # Insert workout_log
        response = supabase.table('workout_logs').insert(workout_log_payload).execute()

        if response is None:
            print(f"Error logging workout: Supabase client returned None for workout_logs. User: {current_user_id}")
            return jsonify({'error': 'Failed to save workout log', 'details': 'Database client communication error'}), 500

        if not response.data: # An insert should return data
            print(f"Error logging workout: No data returned for workout_logs insert and no exception raised. User: {current_user_id}")
            return jsonify({'error': 'Failed to save workout log', 'details': 'No data returned from database operation'}), 500
        
        workout_log_id = response.data[0]['id']

        # Insert exercise_details if any
        if exercises_payload:
            for ex in exercises_payload:
                ex['workout_log_id'] = workout_log_id
                ex['user_id'] = current_user_id 

            try:
                ex_response = supabase.table('exercise_details').insert(exercises_payload).execute()

                if ex_response is None:
                    print(f"Warning: Workout log (ID: {workout_log_id}) saved, but Supabase client returned None for exercises.")
                elif not ex_response.data: # An insert should return data
                    print(f"Warning: Workout log (ID: {workout_log_id}) saved, but no data returned for exercises insert and no exception raised.")
                # If execution reached here without an exception, and data is present, it's considered successful for exercises.
            
            except Exception as ex_e: # Catch exception specifically for exercise insertion
                print(f"Warning: Workout log (ID: {workout_log_id}) saved, but failed to save some/all exercises. Error: {ex_e}")
                # Continue to return 201 for the main log, but with a warning logged.

        return jsonify({'message': 'Workout logged successfully', 'log_id': workout_log_id}), 201

    except Exception as e: 
        print(f"Error logging workout: {e}")
        details = str(e)
        # Check if it's a PostgrestError and try to get a more specific message
        if hasattr(e, 'message') and e.message: # supabase.lib.client_errors.SupabaseAPIError might have this
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)


        return jsonify({'error': 'Failed to save workout log', 'details': details}), 500

@log_bp.route('/log/nutrition', methods=['POST'])
@token_required
def log_nutrition(current_user_id):
    data = request.json
    if not data or not data.get('meal_type') or not data.get('food_item_description') or not data.get('calories'):
        return jsonify({'error': 'Missing meal type, food item description or calories'}), 400

    nutrition_log_payload = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'meal_type': data.get('meal_type'),
        'food_item_description': data.get('food_item_description'),
        'calories': data.get('calories'),
        'protein_g': data.get('protein_g'),
        'carbs_g': data.get('carbs_g'),
        'fat_g': data.get('fat_g')
    }
    try:
        response = supabase.table('nutrition_logs').insert(nutrition_log_payload).execute()

        if response is None:
            print(f"Error logging nutrition: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Failed to log nutrition', 'details': 'Database client communication error'}), 500
        if not response.data:
            print(f"Error logging nutrition: No data returned and no exception raised. User: {current_user_id}")
            return jsonify({'error': 'Failed to log nutrition', 'details': 'No data returned from database operation'}), 500
            
        return jsonify({'message': 'Nutrition logged successfully', 'log_id': response.data[0]['id']}), 201
    except Exception as e:
        print(f"Error logging nutrition: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Failed to log nutrition', 'details': details}), 500

@log_bp.route('/log/weight', methods=['POST'])
@token_required
def log_weight(current_user_id):
    data = request.json
    if not data or not data.get('weight_kg'):
        return jsonify({'error': 'Missing weight_kg'}), 400

    weight_log_payload = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'weight_kg': data.get('weight_kg'),
    }
    try:
        response = supabase.table('weight_tracker').insert(weight_log_payload).execute()
        
        if response is None:
            print(f"Error logging weight: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Failed to log weight', 'details': 'Database client communication error'}), 500
        if not response.data:
            print(f"Error logging weight: No data returned and no exception raised. User: {current_user_id}")
            return jsonify({'error': 'Failed to log weight', 'details': 'No data returned from database operation'}), 500
            
        return jsonify({'message': 'Weight logged successfully', 'log_id': response.data[0]['id']}), 201
    except Exception as e:
        print(f"Error logging weight: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Failed to log weight', 'details': details}), 500

@log_bp.route('/log/water', methods=['POST'])
@token_required
def log_water(current_user_id):
    data = request.json
    if not data or not data.get('amount_ml'):
        return jsonify({'error': 'Missing amount_ml'}), 400

    water_log_payload = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'amount_ml': data.get('amount_ml')
    }
    try:
        response = supabase.table('water_intake_logs').insert(water_log_payload).execute()

        if response is None:
            print(f"Error logging water: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Failed to log water intake', 'details': 'Database client communication error'}), 500
        if not response.data:
            print(f"Error logging water: No data returned and no exception raised. User: {current_user_id}")
            return jsonify({'error': 'Failed to log water intake', 'details': 'No data returned from database operation'}), 500
            
        return jsonify({'message': 'Water intake logged successfully', 'log_id': response.data[0]['id']}), 201
    except Exception as e:
        print(f"Error logging water: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Failed to log water intake', 'details': details}), 500

# GET routes to fetch logs
@log_bp.route('/logs/workout', methods=['GET'])
@token_required
def get_workout_logs(current_user_id):
    log_date_str = request.args.get('date') 
    try:
        query = supabase.table('workout_logs').select('*, exercise_details(*)').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()

        if response is None:
            print(f"Error fetching workout logs: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Error fetching workout logs', 'details': 'Database client communication error'}), 500
        
        if not hasattr(response, 'data'): 
            print(f"Error fetching workout logs: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching workout logs', 'details': 'Malformed database response'}), 500

        return jsonify(response.data), 200 
    except Exception as e:
        print(f"Error fetching workout logs: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching workout logs', 'details': details}), 500

@log_bp.route('/logs/nutrition', methods=['GET'])
@token_required
def get_nutrition_logs(current_user_id):
    log_date_str = request.args.get('date')
    try:
        query = supabase.table('nutrition_logs').select('*').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True).order('created_at', desc=True)
        
        response = query.execute()

        if response is None:
            print(f"Error fetching nutrition logs: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Error fetching nutrition logs', 'details': 'Database client communication error'}), 500
        if not hasattr(response, 'data'):
            print(f"Error fetching nutrition logs: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching nutrition logs', 'details': 'Malformed database response'}), 500
            
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching nutrition logs: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching nutrition logs', 'details': details}), 500

@log_bp.route('/logs/weight', methods=['GET'])
@token_required
def get_weight_logs(current_user_id):
    log_date_str = request.args.get('date')
    try:
        query = supabase.table('weight_tracker').select('*').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()

        if response is None:
            print(f"Error fetching weight logs: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Error fetching weight logs', 'details': 'Database client communication error'}), 500
        if not hasattr(response, 'data'):
            print(f"Error fetching weight logs: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching weight logs', 'details': 'Malformed database response'}), 500
            
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching weight logs: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching weight logs', 'details': details}), 500

@log_bp.route('/logs/water', methods=['GET'])
@token_required
def get_water_logs(current_user_id):
    log_date_str = request.args.get('date')
    try:
        query = supabase.table('water_intake_logs').select('*').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()

        if response is None:
            print(f"Error fetching water logs: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Error fetching water logs', 'details': 'Database client communication error'}), 500
        if not hasattr(response, 'data'):
            print(f"Error fetching water logs: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching water logs', 'details': 'Malformed database response'}), 500
            
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching water logs: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching water logs', 'details': details}), 500