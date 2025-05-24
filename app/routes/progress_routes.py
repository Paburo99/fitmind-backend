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
        workout_summary_last_30_days = workout_summary_resp.data if workout_summary_resp.data else []        # Enhanced insights generation with comprehensive analysis
        insights = []
        
        # Calculate progress metrics
        weight_trend = "stable"
        weight_change = 0
        if len(weight_summary_last_30_days) >= 2:
            initial_weight = weight_summary_last_30_days[0]['weight_kg']
            current_weight = weight_summary_last_30_days[-1]['weight_kg']
            weight_change = current_weight - initial_weight
            if weight_change > 1:
                weight_trend = "increasing"
            elif weight_change < -1:
                weight_trend = "decreasing"
        
        # Calculate workout consistency
        workout_days = len(set(w['date'] for w in workout_summary_last_30_days))
        workout_types = list(set(w.get('type', 'Unknown') for w in workout_summary_last_30_days))
        total_workout_time = sum(w.get('duration_minutes', 0) for w in workout_summary_last_30_days)
        
        # Calculate nutrition consistency  
        nutrition_days = len(set(n['date'] for n in nutrition_summary_last_30_days))
        avg_calories = sum(n.get('calories', 0) for n in nutrition_summary_last_30_days) / len(nutrition_summary_last_30_days) if nutrition_summary_last_30_days else 0
        
        # Build comprehensive AI coach prompt
        prompt_parts = [
            "🧠 AI FITNESS INSIGHTS COACH ROLE: You are an expert data analyst and personal trainer with deep knowledge in fitness psychology and behavior change. Provide meaningful, actionable insights.",
            "",
            f"👤 USER PROFILE ANALYSIS:",
            f"• Primary Goal: {profile.get('primary_goal', 'Not specified')}",
            f"• Fitness Level: {profile.get('fitness_level', 'Not specified')}",
            f"• Starting Weight: {profile.get('initial_weight_kg', 'Not recorded')} kg" if profile.get('initial_weight_kg') else "• Starting Weight: Not recorded",
            "",
            f"📊 30-DAY PERFORMANCE METRICS:",
            f"• Data Collection: {max(workout_days, nutrition_days)}/30 days tracked ({round(max(workout_days, nutrition_days)/30*100)}% consistency)",
            f"• Workout Frequency: {workout_days} days active ({round(workout_days/30*100)}% of month)",
            f"• Total Exercise Time: {total_workout_time} minutes ({round(total_workout_time/60, 1)} hours)",
            f"• Workout Variety: {len(workout_types)} different types: {', '.join(workout_types) if workout_types else 'None'}",
            f"• Nutrition Tracking: {nutrition_days} days logged ({round(nutrition_days/30*100)}% of month)",
            f"• Average Daily Calories: {round(avg_calories)} kcal" if avg_calories > 0 else "• Average Daily Calories: No data",
            f"• Weight Progress: {weight_trend.title()} ({weight_change:+.1f} kg change)" if weight_change != 0 else "• Weight Progress: Stable (no significant change)",
            ""
        ]
        
        # Add detailed data context
        if weight_summary_last_30_days:
            weight_entries = len(weight_summary_last_30_days)
            prompt_parts.append(f"🏋️ WEIGHT DATA ({weight_entries} entries): {weight_summary_last_30_days}")
        
        if nutrition_summary_last_30_days:
            prompt_parts.append(f"🍽️ NUTRITION DATA ({len(nutrition_summary_last_30_days)} entries - showing calories, protein, carbs, fat): {nutrition_summary_last_30_days}")
        
        if workout_summary_last_30_days:
            prompt_parts.append(f"💪 WORKOUT DATA ({len(workout_summary_last_30_days)} sessions): {workout_summary_last_30_days}")
        
        prompt_parts.extend([
            "",
            "🎯 ANALYSIS REQUIREMENTS:",
            "1. PROGRESS ASSESSMENT: Analyze trends, patterns, and alignment with their stated goal",
            "2. BEHAVIORAL INSIGHTS: Identify strengths in their routine and areas needing attention", 
            "3. MOTIVATION BOOST: Celebrate achievements and progress, no matter how small",
            "4. ACTIONABLE GUIDANCE: Provide 1-2 specific, implementable recommendations",
            "5. PERSONALIZATION: Reference their actual data points and goal in your insights",
            "",
            "📝 OUTPUT FORMAT (Return exactly 3-4 bullet points):",
            "• Insight 1: Highlight a positive trend or achievement with specific data",
            "• Insight 2: Identify a key pattern or area for improvement with constructive advice", 
            "• Insight 3: Provide one specific, actionable recommendation for next week",
            "• [Optional] Insight 4: Motivational perspective on their overall journey",
            "",
            "🌟 TONE: Encouraging, professional, data-driven, and personally relevant. Act as their supportive AI fitness coach who genuinely cares about their success.",
            "",
            "⚠️ IMPORTANT: If data is limited, focus on encouraging consistency in tracking and celebrating the commitment to start their fitness journey. Never criticize - always motivate!"
        ])
        
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