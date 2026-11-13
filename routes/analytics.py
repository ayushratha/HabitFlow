from flask import Blueprint, render_template, g, jsonify, request
from datetime import date, timedelta
from auth import login_required
from database import get_db, get_user_stats, calculate_habit_streak

analytics_bp = Blueprint('analytics', __name__, url_prefix='/app/analytics')

@analytics_bp.route('/')
@login_required
def index():
    db = get_db()
    user_id = g.user['id']
    stats = get_user_stats(db, user_id)
    today = date.today()

    # Active habits
    habits = db.execute('''
        SELECT h.*,
               (SELECT COUNT(*) FROM habit_completions WHERE habit_id = h.id) as total_completions
        FROM habits h
        WHERE h.user_id = ? AND h.is_archived = 0
    ''', (user_id,)).fetchall()

    # Calculate completion rates per habit for the last 30 days
    last_30_start = today - timedelta(days=29)
    habit_performance = []

    for h in habits:
        h_id = h['id']
        comp_count_30 = db.execute('''
            SELECT COUNT(*) as cnt 
            FROM habit_completions 
            WHERE habit_id = ? AND completion_date >= ?
        ''', (h_id, last_30_start.isoformat())).fetchone()['cnt']
        
        rate = round((comp_count_30 / 30) * 100)
        streak = calculate_habit_streak(db, h_id)

        habit_performance.append({
            'id': h_id,
            'name': h['name'],
            'category': h['category'],
            'color': h['color'],
            'icon': h['icon'],
            'total_completions': h['total_completions'],
            'rate_30_days': rate,
            'streak': streak
        })

    # Sort into best performers and needs attention
    best_performers = sorted(habit_performance, key=lambda x: x['rate_30_days'], reverse=True)[:3]
    needs_attention = sorted([h for h in habit_performance if h['rate_30_days'] < 60], key=lambda x: x['rate_30_days'])[:3]

    # Category completion distribution
    category_data = db.execute('''
        SELECT h.category, COUNT(hc.id) as completion_count
        FROM habit_completions hc
        JOIN habits h ON hc.habit_id = h.id
        WHERE hc.user_id = ?
        GROUP BY h.category
    ''', (user_id,)).fetchall()

    categories_list = [r['category'] for r in category_data]
    categories_counts = [r['completion_count'] for r in category_data]

    # Overall completion rate across all past 30 days
    total_active = stats['total_active']
    possible_completions_30 = total_active * 30 if total_active > 0 else 1
    actual_completions_30 = db.execute('''
        SELECT COUNT(*) as cnt FROM habit_completions 
        WHERE user_id = ? AND completion_date >= ?
    ''', (user_id, last_30_start.isoformat())).fetchone()['cnt']
    overall_rate_30 = round((actual_completions_30 / possible_completions_30) * 100) if total_active > 0 else 0

    return render_template(
        'app/analytics.html',
        stats=stats,
        habit_performance=habit_performance,
        best_performers=best_performers,
        needs_attention=needs_attention,
        categories_list=categories_list,
        categories_counts=categories_counts,
        overall_rate_30=overall_rate_30,
        actual_completions_30=actual_completions_30
    )

@analytics_bp.route('/api/chart-data')
@login_required
def chart_data():
    """Returns JSON time-series data for dynamic charts (7d, 30d, 90d)."""
    db = get_db()
    user_id = g.user['id']
    days_range = int(request.args.get('days', 30))
    if days_range not in (7, 30, 90):
        days_range = 30

    today = date.today()
    labels = []
    completion_counts = []
    completion_rates = []

    total_active_row = db.execute("SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0", (user_id,)).fetchone()
    total_active = total_active_row['cnt'] if total_active_row else 1

    for i in range(days_range - 1, -1, -1):
        target_d = today - timedelta(days=i)
        target_str = target_d.isoformat()
        
        # Label formatting
        if days_range == 7:
            labels.append(target_d.strftime('%a (%b %d)'))
        elif days_range == 30:
            labels.append(target_d.strftime('%b %d'))
        else:
            labels.append(target_d.strftime('%m/%d'))

        cnt = db.execute('''
            SELECT COUNT(DISTINCT habit_id) as cnt
            FROM habit_completions
            WHERE user_id = ? AND completion_date = ?
        ''', (user_id, target_str)).fetchone()['cnt']

        completion_counts.append(cnt)
        rate = round((cnt / total_active) * 100) if total_active > 0 else 0
        completion_rates.append(rate)

    return jsonify({
        'labels': labels,
        'completion_counts': completion_counts,
        'completion_rates': completion_rates,
        'total_active': total_active
    })
