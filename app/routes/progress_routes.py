from flask import Blueprint, jsonify
from db import get_db_client
from auth_utils import token_required
from gemini_service import generate_text_from_gemini
from datetime import date, timedelta

progress_bp = Blueprint('progress_bp', __name__)
supabase = get_db_client()

@progress_bp.route('/progress/weight', methods=['GET'])
@token_required
def get_weight_progress(current_user_id):
    try:
        # Fetch all weight entries, ordered by date
        # 'data' will be a list of dictionaries.
        # If no records are found, it will be an empty list. This is a successful response.
        data, count = supabase.table('weight_tracker').select('date, weight_kg').eq('user_id', current_user_id).order('date', desc=False).execute()
        return jsonify(data), 200
    except Exception as e:
        print(f"Error fetching weight progress: {e}")
        return jsonify({'error': str(e)}), 500

@progress_bp.route('/progress/nutrition', methods=['GET'])
@token_required
def get_nutrition_progress(current_user_id):
    try:
        # Fetch all nutrition log entries, ordered by date
        nutrition_logs, count = supabase.table('nutrition_logs').select('*').eq('user_id', current_user_id).order('date', desc=False).execute()
        return jsonify(nutrition_logs), 200
    except Exception as e:
        print(f"Error fetching nutrition progress: {e}")
        return jsonify({'error': str(e)}), 500

@progress_bp.route('/progress/workouts', methods=['GET'])
@token_required
def get_workout_progress(current_user_id):
    try:
        # Fetch all workout log entries, ordered by date
        # Consider if exercise_details should be embedded: select('*, exercise_details(*)')
        workout_logs, count = supabase.table('workout_logs').select('*').eq('user_id', current_user_id).order('date', desc=False).execute()
        return jsonify(workout_logs), 200
    except Exception as e:
        print(f"Error fetching workout progress: {e}")
        return jsonify({'error': str(e)}), 500

@progress_bp.route('/insights/generate', methods=['GET'])
@token_required
def generate_fitness_insights(current_user_id):
    try:
        # 1. Fetch relevant data: profile, recent workouts, nutrition, weight
        profile_resp = supabase.table('profiles').select('primary_goal, fitness_level, initial_weight_kg').eq('user_id', current_user_id).maybe_single().execute()
        profile = profile_resp.data if profile_resp.data else {}

        # Last 30 days of data
        thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
        
        weight_data_resp = supabase.table('weight_tracker').select('date, weight_kg').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        weight_summary_last_30_days = weight_data_resp.data if weight_data_resp.data else []

        nutrition_summary_resp = supabase.table('nutrition_logs').select('date, calories, protein_g, carbs_g, fat_g').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        nutrition_summary_last_30_days = nutrition_summary_resp.data if nutrition_summary_resp.data else []

        workout_summary_resp = supabase.table('workout_logs').select('date, type, duration_minutes').eq('user_id', current_user_id).gte('date', thirty_days_ago).order('date').execute()
        workout_summary_last_30_days = workout_summary_resp.data if workout_summary_resp.data else []

        insights = [] # Initialize insights list

        # 3. Prepare prompt for Gemini for nuanced insights
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
            # Split insights if Gemini returns multiple in one string (e.g., separated by newlines)
            # This is a simple split; more sophisticated parsing might be needed depending on Gemini's output format.
            for insight_line in gemini_insight.strip().split('\n'):
                if insight_line.strip(): # Avoid adding empty lines
                    insights.append(insight_line.strip())
        else:
            insights.append("I'm having a little trouble generating detailed insights right now. Please try again in a moment!")
            if gemini_insight: # Log the actual error from Gemini if one was returned
                 print(f"Gemini service returned: {gemini_insight}")

        if not insights: # Fallback if Gemini fails and the above error message wasn't added
            insights.append("Keep tracking your activities and measurements to see insights here!")

        return jsonify({'insights': insights}), 200

    except Exception as e:
        print(f"Error generating insights: {e}")
        return jsonify({'error': str(e)}), 500