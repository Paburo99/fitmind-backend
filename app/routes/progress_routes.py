from flask import Blueprint, jsonify, request
from db import get_db_client
from auth_utils import token_required
from gemini_service import generate_text_from_gemini
from datetime import date, timedelta

progress_bp = Blueprint('progress_bp', __name__)
supabase = get_db_client()

@progress_bp.route('/progress/weight', methods=['GET'])
@token_required
def get_weight_progress(current_user_id):
    days = request.args.get('days')
    
    try:
        query = supabase.table('weight_tracker').select('date, weight_kg').eq('user_id', current_user_id)
        
        # Apply date filtering if days parameter is provided
        if days and days != 'all':
            cutoff_date = (date.today() - timedelta(days=int(days))).isoformat()
            query = query.gte('date', cutoff_date)
            
        response = query.order('date', desc=False).execute()
        
        if response is None:
            print(f"Error fetching weight progress: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (response was None)'}), 500
        
        if not hasattr(response, 'data'):
            print(f"Error fetching weight progress: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching weight progress', 'details': 'Malformed database response'}), 500
            
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching weight progress: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching weight progress', 'details': details}), 500

@progress_bp.route('/progress/nutrition', methods=['GET'])
@token_required
def get_nutrition_progress(current_user_id):
    try:
        response = supabase.table('nutrition_logs').select('*').eq('user_id', current_user_id).order('date', desc=False).execute()
        
        if response is None:
            print(f"Error fetching nutrition progress: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (response was None)'}), 500

        if not hasattr(response, 'data'):
            print(f"Error fetching nutrition progress: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching nutrition progress', 'details': 'Malformed database response'}), 500

        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching nutrition progress: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching nutrition progress', 'details': details}), 500

@progress_bp.route('/progress/workouts', methods=['GET'])
@token_required
def get_workout_progress(current_user_id):
    try:
        response = supabase.table('workout_logs').select('*, exercise_details(*)').eq('user_id', current_user_id).order('date', desc=False).execute()
        
        if response is None:
            print(f"Error fetching workout progress: Supabase client returned None. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (response was None)'}), 500

        if not hasattr(response, 'data'):
            print(f"Error fetching workout progress: Supabase response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error fetching workout progress', 'details': 'Malformed database response'}), 500
            
        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error fetching workout progress: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error fetching workout progress', 'details': details}), 500

@progress_bp.route('/insights/generate', methods=['GET'])
@token_required
def generate_fitness_insights(current_user_id):
    try:
        # 1. Fetch relevant data
        profile_resp = supabase.table('profiles').select('primary_goal, fitness_level, initial_weight_kg').eq('user_id', current_user_id).maybe_single().execute()
        
        if profile_resp is None :
             print(f"Error generating insights: Supabase client returned None for profile. User: {current_user_id}")
             return jsonify({'error': 'Database communication error (profile response was None)'}), 500
        if not hasattr(profile_resp, 'data'):
            print(f"Error generating insights: Supabase profile response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error generating insights', 'details': 'Malformed database response for profile'}), 500
        profile = profile_resp.data if profile_resp.data else {}


        thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
        
        weight_data_resp = supabase.table('weight_tracker').select('date, weight_kg').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        if weight_data_resp is None:
            print(f"Error generating insights: Supabase client returned None for weight data. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (weight data response was None)'}), 500
        if not hasattr(weight_data_resp, 'data'):
            print(f"Error generating insights: Supabase weight data response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error generating insights', 'details': 'Malformed database response for weight data'}), 500
        weight_summary_last_30_days = weight_data_resp.data if weight_data_resp.data else []


        nutrition_summary_resp = supabase.table('nutrition_logs').select('date, calories, protein_g, carbs_g, fat_g').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        if nutrition_summary_resp is None:
            print(f"Error generating insights: Supabase client returned None for nutrition data. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (nutrition data response was None)'}), 500
        if not hasattr(nutrition_summary_resp, 'data'):
            print(f"Error generating insights: Supabase nutrition data response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error generating insights', 'details': 'Malformed database response for nutrition data'}), 500
        nutrition_summary_last_30_days = nutrition_summary_resp.data if nutrition_summary_resp.data else []


        workout_summary_resp = supabase.table('workout_logs').select('date, type, duration_minutes').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        if workout_summary_resp is None:
            print(f"Error generating insights: Supabase client returned None for workout data. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (workout data response was None)'}), 500
        if not hasattr(workout_summary_resp, 'data'):
            print(f"Error generating insights: Supabase workout data response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error generating insights', 'details': 'Malformed database response for workout data'}), 500
        workout_summary_last_30_days = workout_summary_resp.data if workout_summary_resp.data else []

        insights = [] 

        prompt_parts = [
            f"User Profile: Goal - {profile.get('primary_goal', 'Not set')}, Fitness Level - {profile.get('fitness_level', 'Not set')}."
        ]

        if weight_summary_last_30_days:
            prompt_parts.append(f"Recent weight data (last 30 days, format: [{{'date': 'YYYY-MM-DD', 'weight_kg': KG}}]): {weight_summary_last_30_days}")
        else:
            prompt_parts.append("No weight data recorded in the last 30 days.")

        if nutrition_summary_last_30_days:
            prompt_parts.append(f"Recent nutrition summary (last 30 days - list of daily logs, format: [{{'date': 'YYYY-MM-DD', 'calories': CAL, ...}}]): {nutrition_summary_last_30_days}")
        else:
            prompt_parts.append("No nutrition data recorded in the last 30 days.")

        if workout_summary_last_30_days:
            prompt_parts.append(f"Recent workout summary (last 30 days - list of workouts, format: [{{'date': 'YYYY-MM-DD', 'type': TYPE, ...}}]): {workout_summary_last_30_days}")
        else:
            prompt_parts.append("No workout data recorded in the last 30 days.")
        
        prompt_parts.append(
            "Based on all the provided data (user profile, weight, nutrition, and workouts over the last 30 days), "
            "provide 2-3 encouraging and personalized fitness/health insights. "
            "Also, include one actionable tip for improvement directly related to their primary goal and recent activity. "
            "If there is very little data, acknowledge that and provide general encouragement to keep tracking."
            "Phrase the insights as if you are an AI Fitness Coach."
        )
        
        gemini_insight = generate_text_from_gemini(prompt_parts)
        
        if gemini_insight and "Sorry, I couldn\'t generate a response" not in gemini_insight:
            for insight_line in gemini_insight.strip().split('\n'):
                if insight_line.strip(): 
                    insights.append(insight_line.strip())
        else:
            insights.append("I'm having a little trouble generating detailed insights right now. Please try again in a moment!")
            if gemini_insight: 
                 print(f"Gemini service returned: {gemini_insight}")

        if not insights: 
            insights.append("Keep tracking your activities and measurements to see insights here!")

        return jsonify({'insights': insights}), 200

    except Exception as e:
        print(f"Error generating insights: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error generating insights', 'details': details}), 500