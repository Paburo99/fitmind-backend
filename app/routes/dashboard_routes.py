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
    summary = {
        'calories_today': 0,
        'protein_today': 0,
        'workouts_today_count': 0,
        'current_weight_kg': None,
        'water_intake_today_ml': 0
    }

    try:
        # Nutrition for today
        nut_response = supabase.table('nutrition_logs').select('calories, protein_g').eq('user_id', current_user_id).eq('date', today_str).execute()
        
        if nut_response is None:
            print(f"Error fetching nutrition for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
            # Decide if you want to return 500 or continue with default values
        elif nut_response.error:
            print(f"Error fetching nutrition for dashboard: {nut_response.error.message}. User: {current_user_id}, Date: {today_str}")
            # Decide if you want to return 500 or continue
        elif nut_response.data:
            for item in nut_response.data:
                summary['calories_today'] += item.get('calories', 0) or 0
                summary['protein_today'] += item.get('protein_g', 0) or 0
        
        # Workouts for today
        wo_response = supabase.table('workout_logs').select('id', count='exact').eq('user_id', current_user_id).eq('date', today_str).execute()
        
        if wo_response is None:
            print(f"Error fetching workouts for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
        elif wo_response.error:
            print(f"Error fetching workouts for dashboard: {wo_response.error.message}. User: {current_user_id}, Date: {today_str}")
        elif wo_response.count:
             summary['workouts_today_count'] = wo_response.count
        
        # Latest weight
        lw_response = supabase.table('weight_tracker').select('weight_kg').eq('user_id', current_user_id).order('date', desc=True).limit(1).maybe_single().execute()

        if lw_response is None:
            print(f"Error fetching latest weight for dashboard: Supabase response was None. User: {current_user_id}")
        elif lw_response.error:
            print(f"Error fetching latest weight for dashboard: {lw_response.error.message}. User: {current_user_id}")
        elif lw_response.data: # lw_response.data is the dictionary itself if a record is found, or None
            summary['current_weight_kg'] = lw_response.data.get('weight_kg')

        # Water intake today
        wi_response = supabase.table('water_intake_logs').select('amount_ml').eq('user_id', current_user_id).eq('date', today_str).execute()

        if wi_response is None:
            print(f"Error fetching water intake for dashboard: Supabase response was None. User: {current_user_id}, Date: {today_str}")
        elif wi_response.error:
            print(f"Error fetching water intake for dashboard: {wi_response.error.message}. User: {current_user_id}, Date: {today_str}")
        elif wi_response.data:
            for item in wi_response.data:
                 summary['water_intake_today_ml'] += item.get('amount_ml', 0) or 0

        return jsonify(summary), 200
    except Exception as e:
        print(f"Error fetching dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500