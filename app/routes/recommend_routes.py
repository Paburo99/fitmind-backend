from flask import Blueprint, request, jsonify
from ..db import get_db_client
from ..auth_utils import token_required
from ..gemini_service import generate_text_from_gemini

recommend_bp = Blueprint('recommend_bp', __name__)
supabase = get_db_client()

@recommend_bp.route('/recommend/workout', methods=['GET'])
@token_required
def get_workout_recommendation(current_user_id):
    try:
        # Fetch user profile for context
        profile_resp = supabase.table('profiles').select('fitness_level, primary_goal, dietary_preferences').eq('user_id', current_user_id).maybe_single().execute()
        profile = profile_resp.data if profile_resp.data else {}
        
        # Fetch recent workouts (optional, for more context)
        # ... 

        fitness_level = profile.get('fitness_level', 'beginner')
        primary_goal = profile.get('primary_goal', 'general fitness')

        prompt = [
            f"I am a user with a fitness level of '{fitness_level}' and my primary goal is '{primary_goal}'.",
            "Please suggest a challenging but appropriate workout for me today.",
            "Include specific exercises, sets, and reps. If it's a cardio workout, suggest type and duration.",
            "Provide the response as a simple text description. Avoid complex formatting."
        ]
        
        recommendation_text = generate_text_from_gemini(prompt)
        return jsonify({'recommendation': recommendation_text}), 200
    except Exception as e:
        print(f"Error getting workout recommendation: {e}")
        return jsonify({'error': str(e)}), 500

@recommend_bp.route('/recommend/meal', methods=['GET'])
@token_required
def get_meal_recommendation(current_user_id):
    meal_type = request.args.get('type', 'lunch') # e.g., 'breakfast', 'lunch', 'dinner'
    try:
        profile_resp = supabase.table('profiles').select('primary_goal, dietary_preferences, allergies_intolerances').eq('user_id', current_user_id).maybe_single().execute()
        profile = profile_resp.data if profile_resp.data else {}

        primary_goal = profile.get('primary_goal', 'healthy eating')
        diet_prefs = profile.get('dietary_preferences', 'none')
        allergies = profile.get('allergies_intolerances', 'none')

        prompt = [
            f"My primary health goal is '{primary_goal}'. My dietary preferences are: '{diet_prefs}'. I have the following allergies/intolerances: '{allergies}'.",
            f"Please suggest a healthy and simple recipe for {meal_type}.",
            "Include ingredients and basic instructions. Aim for a moderate calorie count unless specified by my goal.",
            "Provide the response as simple text."
        ]
        
        recommendation_text = generate_text_from_gemini(prompt)
        return jsonify({'recommendation': recommendation_text}), 200
    except Exception as e:
        print(f"Error getting meal recommendation: {e}")
        return jsonify({'error': str(e)}), 500