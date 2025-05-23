from flask import Blueprint, jsonify
from db import get_db_client
from auth_utils import token_required
from datetime import date, timedelta

dashboard_bp = Blueprint('dashboard_bp', __name__)
supabase = get_db_client()

@dashboard_bp.route('/dashboard/summary', methods=['GET'])
@token_required
def get_dashboard_summary(current_user_id):
    today_str = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
    
    summary = {
        'calories_today': 0,
        'protein_today': 0,
        'workouts_today_count': 0,
        'current_weight_kg': None,
        'water_intake_today_ml': 0,
        'workouts_this_week': 0,
        'calories_burned_this_week': 0,
        'current_streak': 0,
        'total_workouts': 0,
        'nutrition_logs_today': 0,        'water_logs_today': 0,
        'target_workouts_weekly': 5,  # Default values, could be fetched from user preferences
        'target_activities_daily': 3
    }

    try:
        # Get user preferences for goals (if they exist)
        profile_response = supabase.table('profiles').select('weekly_workout_goal, daily_activity_goal').eq('user_id', current_user_id).maybe_single().execute()
        if profile_response and profile_response.data:
            summary['target_workouts_weekly'] = profile_response.data.get('weekly_workout_goal', 5)
            summary['target_activities_daily'] = profile_response.data.get('daily_activity_goal', 3)

        # Nutrition for today
        nut_response = supabase.table('nutrition_logs').select('calories, protein_g').eq('user_id', current_user_id).eq('date', today_str).execute()
        
        if nut_response is None:
            print(f"Error fetching nutrition for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
        elif nut_response.data:
            summary['nutrition_logs_today'] = len(nut_response.data)
            for item in nut_response.data:
                summary['calories_today'] += item.get('calories', 0) or 0
                summary['protein_today'] += item.get('protein_g', 0) or 0
        
        # Workouts for today
        wo_response = supabase.table('workout_logs').select('id', count='exact').eq('user_id', current_user_id).eq('date', today_str).execute()
        
        if wo_response is None:
            print(f"Error fetching workouts for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
        elif wo_response.count:
             summary['workouts_today_count'] = wo_response.count

        # Workouts this week and calories burned
        week_workouts_response = supabase.table('workout_logs').select('id, calories_burned', count='exact').eq('user_id', current_user_id).gte('date', week_start).execute()
        if week_workouts_response and week_workouts_response.data:
            summary['workouts_this_week'] = len(week_workouts_response.data)
            summary['calories_burned_this_week'] = sum(item.get('calories_burned', 0) or 0 for item in week_workouts_response.data)

        # Total workouts ever
        total_workouts_response = supabase.table('workout_logs').select('id', count='exact').eq('user_id', current_user_id).execute()
        if total_workouts_response:
            summary['total_workouts'] = total_workouts_response.count or 0

        # Calculate current streak (simplified - consecutive days with workouts)
        streak_days = 0
        current_date = date.today()
        while True:
            day_str = current_date.isoformat()
            day_workouts = supabase.table('workout_logs').select('id', count='exact').eq('user_id', current_user_id).eq('date', day_str).execute()
            if day_workouts and day_workouts.count and day_workouts.count > 0:
                streak_days += 1
                current_date -= timedelta(days=1)
            else:
                break
            if streak_days > 30:  # Prevent infinite loops
                break
        summary['current_streak'] = streak_days

        # Latest weight
        lw_response = supabase.table('weight_tracker').select('weight_kg').eq('user_id', current_user_id).order('date', desc=True).limit(1).maybe_single().execute()

        if lw_response is None:
            print(f"Error fetching latest weight for dashboard: Supabase response was None. User: {current_user_id}")
        elif lw_response.data:
            summary['current_weight_kg'] = lw_response.data.get('weight_kg')

        # Water intake today
        wi_response = supabase.table('water_intake_logs').select('amount_ml').eq('user_id', current_user_id).eq('date', today_str).execute()

        if wi_response is None:
            print(f"Error fetching water intake for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
        elif wi_response.data:
            summary['water_logs_today'] = len(wi_response.data)
            for item in wi_response.data:
                 summary['water_intake_today_ml'] += item.get('amount_ml', 0) or 0

        return jsonify(summary), 200
    except Exception as e:
        print(f"Error fetching dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500