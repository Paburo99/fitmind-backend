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

    workout_log = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'type': data.get('type'),
        'duration_minutes': data.get('duration_minutes'),
        'calories_burned': data.get('calories_burned'),
        'notes': data.get('notes')
    }
    exercises = data.get('exercises', []) # List of exercise dicts

    try:
        # Insert workout_log
        response = supabase.table('workout_logs').insert(workout_log).execute()
        
        if response.error or not response.data:
            error_detail = response.error.message if response.error else 'No data returned'
            return jsonify({'error': 'Failed to save workout log', 'details': error_detail}), 500
        
        workout_log_id = response.data[0]['id']

        # Insert exercise_details if any
        if exercises:
            for ex in exercises:
                ex['workout_log_id'] = workout_log_id
            # Batch insert exercises
            ex_response = supabase.table('exercise_details').insert(exercises).execute()
            if ex_response.error or not ex_response.data:
                # Log this error, but maybe don't fail the whole request if main log saved
                error_detail = ex_response.error.message if ex_response.error else 'No data returned for exercises'
                print(f"Warning: Workout log saved (ID: {workout_log_id}), but failed to save some/all exercises. Error: {error_detail}")

        return jsonify({'message': 'Workout logged successfully', 'log_id': workout_log_id}), 201

    except Exception as e:
        print(f"Error logging workout: {e}")
        return jsonify({'error': str(e)}), 500

# --- Add similar routes for /log/nutrition, /log/weight, /log/water ---
# Example for nutrition:
@log_bp.route('/log/nutrition', methods=['POST'])
@token_required
def log_nutrition(current_user_id):
    data = request.json
    if not data or not data.get('meal_type') or not data.get('food_item_description') or not data.get('calories'):
        return jsonify({'error': 'Missing meal type, food item description or calories'}), 400

    nutrition_log = {
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
        response = supabase.table('nutrition_logs').insert(nutrition_log).execute()
        if response.data and not response.error:
            return jsonify({'message': 'Nutrition logged successfully', 'log_id': response.data[0]['id']}), 201
        error_detail = response.error.message if response.error else 'No data returned'
        return jsonify({'error': 'Failed to log nutrition', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error logging nutrition: {e}")
        return jsonify({'error': str(e)}), 500

@log_bp.route('/log/weight', methods=['POST'])
@token_required
def log_weight(current_user_id):
    data = request.json
    if not data or not data.get('weight_kg'):
        return jsonify({'error': 'Missing weight_kg'}), 400

    weight_log = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'weight_kg': data.get('weight_kg'),
    }
    try:
        response = supabase.table('weight_tracker').insert(weight_log).execute()
        if response.data and not response.error:
            return jsonify({'message': 'Weight logged successfully', 'log_id': response.data[0]['id']}), 201
        error_detail = response.error.message if response.error else 'No data returned'
        return jsonify({'error': 'Failed to log weight', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error logging weight: {e}")
        return jsonify({'error': str(e)}), 500

@log_bp.route('/log/water', methods=['POST'])
@token_required
def log_water(current_user_id):
    data = request.json
    if not data or not data.get('amount_ml'):
        return jsonify({'error': 'Missing amount_ml'}), 400

    water_log = {
        'user_id': current_user_id,
        'date': data.get('date', date.today().isoformat()),
        'amount_ml': data.get('amount_ml')
    }
    try:
        response = supabase.table('water_intake_logs').insert(water_log).execute()
        if response.data and not response.error:
            return jsonify({'message': 'Water intake logged successfully', 'log_id': response.data[0]['id']}), 201
        error_detail = response.error.message if response.error else 'No data returned'
        return jsonify({'error': 'Failed to log water intake', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error logging water: {e}")
        return jsonify({'error': str(e)}), 500

# GET routes to fetch logs (e.g., for a specific date or range)
@log_bp.route('/logs/workout', methods=['GET'])
@token_required
def get_workout_logs(current_user_id):
    log_date_str = request.args.get('date') # expects YYYY-MM-DD
    try:
        query = supabase.table('workout_logs').select('*, exercise_details(*)').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()
        if response.data is not None and not response.error: # response.data can be an empty list
            return jsonify(response.data), 200
        error_detail = response.error.message if response.error else 'No data/error fetching workout logs'
        return jsonify({'error': 'Error fetching workout logs or no logs found', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error fetching workout logs: {e}")
        return jsonify({'error': str(e)}), 500

@log_bp.route('/logs/nutrition', methods=['GET'])
@token_required
def get_nutrition_logs(current_user_id):
    log_date_str = request.args.get('date') # expects YYYY-MM-DD
    try:
        query = supabase.table('nutrition_logs').select('*').eq('user_id', current_user_id)
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True).order('created_at', desc=True) # Order by date then by time
        
        response = query.execute()
        if response.data is not None and not response.error:
            return jsonify(response.data), 200
        error_detail = response.error.message if response.error else 'No data/error fetching nutrition logs'
        return jsonify({'error': 'Error fetching nutrition logs or no logs found', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error fetching nutrition logs: {e}")
        return jsonify({'error': str(e)}), 500

@log_bp.route('/logs/weight', methods=['GET'])
@token_required
def get_weight_logs(current_user_id):
    log_date_str = request.args.get('date') # expects YYYY-MM-DD
    try:
        query = supabase.table('weight_tracker').select('*').eq('user_id', current_user_id) # Changed table name
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()
        if response.data is not None and not response.error:
            return jsonify(response.data), 200
        error_detail = response.error.message if response.error else 'No data/error fetching weight logs'
        return jsonify({'error': 'Error fetching weight logs or no logs found', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error fetching weight logs: {e}")
        return jsonify({'error': str(e)}), 500

@log_bp.route('/logs/water', methods=['GET'])
@token_required
def get_water_logs(current_user_id):
    log_date_str = request.args.get('date') # expects YYYY-MM-DD
    try:
        query = supabase.table('water_intake_logs').select('*').eq('user_id', current_user_id) # Changed table name
        if log_date_str:
            query = query.eq('date', log_date_str)
        query = query.order('date', desc=True)
        
        response = query.execute()
        if response.data is not None and not response.error:
            return jsonify(response.data), 200
        error_detail = response.error.message if response.error else 'No data/error fetching water logs'
        return jsonify({'error': 'Error fetching water logs or no logs found', 'details': error_detail}), 500
    except Exception as e:
        print(f"Error fetching water logs: {e}")
        return jsonify({'error': str(e)}), 500