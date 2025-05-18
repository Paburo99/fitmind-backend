from flask import Blueprint, jsonify
from ..db import get_db_client
from ..auth_utils import token_required
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
        nut_data, nut_count = supabase.table('nutrition_logs').select('calories, protein_g').eq('user_id', current_user_id).eq('date', today_str).execute()
        if nut_data: # Check if the list of nutrition logs is not empty
            for item in nut_data: # Iterate over the list of dictionaries
                summary['calories_today'] += item.get('calories', 0) or 0
                summary['protein_today'] += item.get('protein_g', 0) or 0
        
        # Workouts for today
        wo_data, wo_count = supabase.table('workout_logs').select('id', count='exact').eq('user_id', current_user_id).eq('date', today_str).execute()
        if wo_count is not None: # Use the count returned by the query
             summary['workouts_today_count'] = wo_count
        
        # Latest weight
        # lw_data will be a dict if found due to maybe_single(), or None
        lw_data, lw_count = supabase.table('weight_tracker').select('weight_kg').eq('user_id', current_user_id).order('date', desc=True).limit(1).maybe_single().execute()
        if lw_data: # lw_data is the dictionary itself if a record is found
            summary['current_weight_kg'] = lw_data.get('weight_kg')

        # Water intake today
        wi_data, wi_count = supabase.table('water_intake_logs').select('amount_ml').eq('user_id', current_user_id).eq('date', today_str).execute()
        if wi_data: # Check if the list of water intake logs is not empty
            for item in wi_data: # Iterate over the list of dictionaries
                 summary['water_intake_today_ml'] += item.get('amount_ml', 0) or 0

        return jsonify(summary), 200
    except Exception as e:
        print(f"Error fetching dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500