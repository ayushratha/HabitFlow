from flask import Blueprint, render_template, request, g, jsonify
import calendar
from datetime import date, datetime
from auth import login_required
from database import get_db

calendar_bp = Blueprint('calendar', __name__, url_prefix='/app/calendar')

@calendar_bp.route('/')
@login_required
def index():
    today = date.today()
    try:
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
    except ValueError:
        year = today.year
        month = today.month

    # Boundary safety
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    db = get_db()
    user_id = g.user['id']

    # Total active habits
    total_active_row = db.execute(
        "SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0",
        (user_id,)
    ).fetchone()
    total_active = total_active_row['cnt'] if total_active_row else 0

    # Fetch all completions in this month for this user
    month_start = f"{year:04d}-{month:02d}-01"
    num_days = calendar.monthrange(year, month)[1]
    month_end = f"{year:04d}-{month:02d}-{num_days:02d}"

    completions = db.execute('''
        SELECT completion_date, COUNT(DISTINCT habit_id) as completed_count
        FROM habit_completions
        WHERE user_id = ? AND completion_date BETWEEN ? AND ?
        GROUP BY completion_date
    ''', (user_id, month_start, month_end)).fetchall()

    completions_map = {r['completion_date']: r['completed_count'] for r in completions}

    # Build calendar matrix (weeks, days)
    # calendar.monthcalendar starts on Monday by default
    cal_matrix = calendar.monthcalendar(year, month)

    month_days = []
    for week in cal_matrix:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'date_str': '', 'status': 'empty'})
            else:
                d_str = f"{year:04d}-{month:02d}-{day:02d}"
                comp_cnt = completions_map.get(d_str, 0)
                is_today = (d_str == today.isoformat())
                is_future = (d_str > today.isoformat())

                if total_active == 0:
                    status = 'none'
                    pct = 0
                elif comp_cnt >= total_active and comp_cnt > 0:
                    status = 'complete'
                    pct = 100
                elif comp_cnt > 0:
                    status = 'partial'
                    pct = round((comp_cnt / total_active) * 100)
                else:
                    status = 'future' if is_future else 'missed'
                    pct = 0

                week_data.append({
                    'day': day,
                    'date_str': d_str,
                    'is_today': is_today,
                    'is_future': is_future,
                    'completed_count': comp_cnt,
                    'total_active': total_active,
                    'percentage': pct,
                    'status': status
                })
        month_days.append(week_data)

    # Prev and Next month navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = calendar.month_name[month]

    return render_template(
        'app/calendar.html',
        month_days=month_days,
        year=year,
        month=month,
        month_name=month_name,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        today_str=today.isoformat(),
        total_active=total_active
    )

@calendar_bp.route('/api/day-details')
@login_required
def day_details():
    """Returns all habits and their completion state on a specific date."""
    target_date = request.args.get('date')
    if not target_date:
        return jsonify({'error': 'Missing date'}), 400

    db = get_db()
    user_id = g.user['id']

    habits = db.execute('''
        SELECT h.id, h.name, h.category, h.color, h.icon,
               CASE WHEN hc.id IS NOT NULL THEN 1 ELSE 0 END as completed,
               hc.notes, hc.created_at as completed_at
        FROM habits h
        LEFT JOIN habit_completions hc 
          ON h.id = hc.habit_id 
          AND hc.user_id = h.user_id 
          AND hc.completion_date = ?
        WHERE h.user_id = ? AND h.is_archived = 0
        ORDER BY completed DESC, h.name ASC
    ''', (target_date, user_id)).fetchall()

    habits_list = [dict(h) for h in habits]
    completed_count = sum(1 for h in habits_list if h['completed'])
    total = len(habits_list)
    percentage = round((completed_count / total * 100)) if total > 0 else 0

    return jsonify({
        'date': target_date,
        'habits': habits_list,
        'completed_count': completed_count,
        'total': total,
        'percentage': percentage
    })
