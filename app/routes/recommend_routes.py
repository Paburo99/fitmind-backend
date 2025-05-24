from flask import Blueprint, request, jsonify
from db import get_db_client
from auth_utils import token_required
from gemini_service import generate_text_from_gemini

recommend_bp = Blueprint('recommend_bp', __name__)
supabase = get_db_client()

@recommend_bp.route('/recommend/workout', methods=['GET'])
@token_required
def get_workout_recommendation(current_user_id):
    try:
        # Fetch user profile for context
        profile_resp = supabase.table('profiles').select('fitness_level, primary_goal').eq('user_id', current_user_id).maybe_single().execute()
        
        if profile_resp is None:
            print(f"Error getting workout recommendation: Supabase client returned None for profile. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (profile response was None)'}), 500

        if not hasattr(profile_resp, 'data'):
            print(f"Error getting workout recommendation: Supabase profile response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error getting workout recommendation', 'details': 'Malformed database response for profile'}), 500
        
        profile = profile_resp.data if profile_resp.data else {}
        
        # Fetch recent workouts (optional, for more context)
        # ... 

        fitness_level = profile.get('fitness_level', 'beginner')
        primary_goal = profile.get('primary_goal', 'general fitness')        # Fetch recent workout data to avoid repetition and track progress
        recent_workouts_resp = supabase.table('workout_logs').select('date, type, duration_minutes, notes').eq('user_id', current_user_id).order('date', desc=True).limit(5).execute()
        recent_workouts = recent_workouts_resp.data if recent_workouts_resp and hasattr(recent_workouts_resp, 'data') else []
        
        # Build comprehensive, personalized prompt
        prompt = [
            "🏋️ AI FITNESS COACH ROLE: You are an expert personal trainer with 10+ years of experience. Provide a personalized workout recommendation.",
            "",
            f"👤 USER PROFILE:",
            f"• Fitness Level: {fitness_level.title()}",
            f"• Primary Goal: {primary_goal.title()}",
            f"• Recent Activity: {'Active user with ' + str(len(recent_workouts)) + ' logged workouts in past 5 sessions' if recent_workouts else 'New or returning user - design beginner-friendly routine'}",
            "",
            f"📊 RECENT WORKOUT HISTORY (Last 5 sessions):" if recent_workouts else "📊 WORKOUT HISTORY: No recent data - perfect opportunity for a fresh start!",
        ]
        
        if recent_workouts:
            for i, workout in enumerate(recent_workouts[:3], 1):
                workout_type = workout.get('type', 'Unknown').title()
                duration = workout.get('duration_minutes', 'N/A')
                date = workout.get('date', 'Unknown')
                prompt.append(f"  {i}. {workout_type} - {duration} min ({date})")
        
        prompt.extend([
            "",
            "🎯 WORKOUT DESIGN REQUIREMENTS:",
            f"• Difficulty: Match {fitness_level} level (beginner=simple movements, intermediate=moderate complexity, advanced=challenging variations)",
            f"• Goal Alignment: Optimize for '{primary_goal}' (weight loss=cardio focus, muscle gain=strength focus, endurance=cardio+strength mix)",
            "• Variety: Avoid repeating recent workout types unless it's a progressive program",
            "• Time Efficient: 30-45 minute duration ideal",
            "• Equipment: Assume basic gym access or bodyweight alternatives",
            "",
            "📝 OUTPUT FORMAT REQUIRED:",
            "• Workout Title (motivational and goal-specific)",
            "• Brief explanation (why this workout matches their profile)",
            "• Warm-up (5-8 minutes)",
            "• Main workout with specific exercises, sets, reps, and rest periods",
            "• Cool-down (5 minutes)",
            "• Motivational closing tip",
            "",
            "🔥 Make it engaging, specific, and actionable. Include progression tips for next time!"
        ])
        
        # Add variety based on recent workouts
        if recent_workouts:
            recent_types = [w.get('type', '').lower() for w in recent_workouts]
            if 'strength' in ' '.join(recent_types):
                prompt.append("\n💡 VARIETY TIP: User has done strength training recently - consider cardio or HIIT variation")
            elif 'cardio' in ' '.join(recent_types):
                prompt.append("\n💡 VARIETY TIP: User has done cardio recently - consider strength or functional training")
        
        recommendation_text = generate_text_from_gemini(prompt)
        if "Sorry, I couldn\'t generate a response" in recommendation_text:
             return jsonify({'error': 'Could not generate workout recommendation at this time.'}), 503

        return jsonify({'recommendation': recommendation_text}), 200
    except Exception as e:
        print(f"Error getting workout recommendation: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error getting workout recommendation', 'details': details}), 500

@recommend_bp.route('/recommend/meal', methods=['GET'])
@token_required
def get_meal_recommendation(current_user_id):
    meal_type = request.args.get('type', 'lunch') # e.g., 'breakfast', 'lunch', 'dinner'
    try:
        profile_resp = supabase.table('profiles').select('primary_goal, dietary_preferences, allergies_intolerances').eq('user_id', current_user_id).maybe_single().execute()

        if profile_resp is None:
            print(f"Error getting meal recommendation: Supabase client returned None for profile. User: {current_user_id}")
            return jsonify({'error': 'Database communication error (profile response was None)'}), 500

        if not hasattr(profile_resp, 'data'):
            print(f"Error getting meal recommendation: Supabase profile response object malformed (missing 'data'). User: {current_user_id}")
            return jsonify({'error': 'Error getting meal recommendation', 'details': 'Malformed database response for profile'}), 500

        profile = profile_resp.data if profile_resp.data else {}

        primary_goal = profile.get('primary_goal', 'healthy eating')
        diet_prefs = profile.get('dietary_preferences', 'none')
        allergies = profile.get('allergies_intolerances', 'none')        # Fetch recent nutrition data to avoid repetition and provide variety
        recent_meals_resp = supabase.table('nutrition_logs').select('date, meal_type, food_items, calories').eq('user_id', current_user_id).order('date', desc=True).limit(5).execute()
        recent_meals = recent_meals_resp.data if recent_meals_resp and hasattr(recent_meals_resp, 'data') else []
        
        # Get user's calorie and macro goals if available
        profile_nutrition_resp = supabase.table('profiles').select('target_weight_kg, activity_level').eq('user_id', current_user_id).maybe_single().execute()
        profile_nutrition = profile_nutrition_resp.data if profile_nutrition_resp and hasattr(profile_nutrition_resp, 'data') and profile_nutrition_resp.data else {}
        
        # Calculate estimated calorie needs based on goal and activity level
        activity_level = profile_nutrition.get('activity_level', 'moderate')
        calorie_range = {
            'breakfast': '300-500',
            'lunch': '400-700', 
            'dinner': '400-600',
            'snack': '100-300'
        }.get(meal_type, '400-600')
        
        prompt = [
            "🍽️ AI NUTRITION COACH ROLE: You are a certified nutritionist and meal planning expert. Create a personalized, healthy meal recommendation.",
            "",
            f"👤 USER PROFILE:",
            f"• Primary Goal: {primary_goal.title()}",
            f"• Dietary Preferences: {diet_prefs.title() if diet_prefs != 'none' else 'No specific preferences'}",
            f"• Allergies/Intolerances: {allergies.title() if allergies != 'none' else 'None reported'}",
            f"• Activity Level: {activity_level.title()}",
            f"• Meal Type: {meal_type.title()}",
            f"• Target Calorie Range: {calorie_range} calories",
            "",
            f"📊 RECENT MEAL HISTORY:" if recent_meals else "📊 MEAL HISTORY: Fresh start - design a nutritionally balanced meal!",
        ]
        
        if recent_meals:
            recent_foods = []
            for meal in recent_meals[:3]:
                food_items = meal.get('food_items', 'Unknown')
                date = meal.get('date', 'Unknown')
                calories = meal.get('calories', 'N/A')
                recent_foods.append(f"  • {food_items} ({calories} cal) - {date}")
            prompt.extend(recent_foods)
            
            # Extract common ingredients to suggest variety
            all_foods = ' '.join([meal.get('food_items', '') for meal in recent_meals]).lower()
            common_proteins = ['chicken', 'beef', 'fish', 'salmon', 'tuna', 'eggs', 'tofu']
            recent_proteins = [p for p in common_proteins if p in all_foods]
            if recent_proteins:
                prompt.append(f"  📝 Note: Recently consumed proteins: {', '.join(recent_proteins)} - suggest variety")
        
        prompt.extend([
            "",
            "🎯 MEAL DESIGN REQUIREMENTS:",
            f"• Goal Optimization: Tailor for '{primary_goal}' (weight loss=lower cal/high protein, muscle gain=higher protein/moderate carbs, maintenance=balanced)",
            f"• Dietary Compliance: Strictly follow '{diet_prefs}' preferences and avoid '{allergies}' allergens",
            "• Nutritional Balance: Include quality protein, complex carbs, healthy fats, and vegetables",
            "• Variety: Suggest different ingredients from recent meals when possible",
            f"• Preparation: {meal_type.title()}-appropriate (breakfast=quick/energizing, lunch=satisfying/portable, dinner=hearty/relaxing)",
            "• Accessibility: Use common ingredients available in most grocery stores",
            "",
            "📝 OUTPUT FORMAT REQUIRED:",
            f"• Recipe Title (appetizing and goal-aligned for {meal_type})",
            "• Brief nutritional overview (why this meal supports their goal)",
            "• Ingredients list with quantities",
            "• Step-by-step preparation instructions (clear and concise)",
            "• Estimated nutrition facts (calories, protein, carbs, fat)",
            "• Pro tip for meal prep or variations",
            "",
            "🌟 Make it delicious, nutritious, and aligned with their fitness journey!"
        ])
        
        # Add time-specific recommendations
        time_tips = {
            'breakfast': '\n⏰ BREAKFAST TIP: Focus on protein and fiber to maintain energy and satiety throughout the morning',
            'lunch': '\n⏰ LUNCH TIP: Balance energy needs for afternoon activities while avoiding post-meal crashes',
            'dinner': '\n⏰ DINNER TIP: Emphasize protein for overnight muscle recovery and moderate carbs for better sleep',
            'snack': '\n⏰ SNACK TIP: Choose nutrient-dense options that complement daily macro targets'
        }
        if meal_type in time_tips:
            prompt.append(time_tips[meal_type])
        
        recommendation_text = generate_text_from_gemini(prompt)
        if "Sorry, I couldn\'t generate a response" in recommendation_text:
             return jsonify({'error': 'Could not generate meal recommendation at this time.'}), 503
             
        return jsonify({'recommendation': recommendation_text}), 200
    except Exception as e:
        print(f"Error getting meal recommendation: {e}")
        details = str(e)
        if hasattr(e, 'message') and e.message:
            details = e.message
        elif hasattr(e, 'args') and e.args:
            details = str(e.args[0]) if isinstance(e.args[0], dict) and 'message' in e.args[0] else str(e.args)
        return jsonify({'error': 'Error getting meal recommendation', 'details': details}), 500