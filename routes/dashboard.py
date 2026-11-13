from flask import Blueprint, render_template, g, jsonify, request
from datetime import date, timedelta, datetime
from auth import login_required
from database import get_db, get_user_stats, calculate_habit_streak, check_and_unlock_achievements

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/app')

MOTIVATIONAL_QUOTES = [
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Will Durant"),
    ("Small disciplines repeated with consistency every day lead to great achievements.", "John C. Maxwell"),
    ("Atomic habits are the compound interest of self-improvement.", "James Clear"),
    ("You do not rise to the level of your goals. You fall to the level of your systems.", "James Clear"),
    ("Consistency is the DNA of mastery.", "Robin Sharma")
]

@dashboard_bp.route('/')
@dashboard_bp.route('/overview')
@login_required
def index():
    db = get_db()
    user_id = g.user['id']
    today_str = date.today().isoformat()
    today_obj = date.today()

    # Get user metrics
    stats = get_user_stats(db, user_id)

    # Fetch active habits for this user with today's status
    habits = db.execute('''
        SELECT h.*, 
               CASE WHEN hc.id IS NOT NULL THEN 1 ELSE 0 END as completed_today,
               hc.id as completion_id
        FROM habits h
        LEFT JOIN habit_completions hc 
          ON h.id = hc.habit_id 
          AND hc.user_id = h.user_id 
          AND hc.completion_date = ?
        WHERE h.user_id = ? AND h.is_archived = 0
        ORDER BY completed_today ASC, h.id ASC
    ''', (today_str, user_id)).fetchall()

    # Calculate streaks for each individual habit
    habits_list = []
    for h in habits:
        h_dict = dict(h)
        h_dict['streak'] = calculate_habit_streak(db, h['id'])
        habits_list.append(h_dict)

    # 7-Day Activity data for mini weekly chart
    weekly_labels = []
    weekly_rates = []
    total_habits_count = stats['total_active']

    for i in range(6, -1, -1):
        d = today_obj - timedelta(days=i)
        d_str = d.isoformat()
        weekly_labels.append(d.strftime('%a'))

        completed_count = db.execute('''
            SELECT COUNT(DISTINCT habit_id) as cnt
            FROM habit_completions
            WHERE user_id = ? AND completion_date = ?
        ''', (user_id, d_str)).fetchone()['cnt']

        rate = round((completed_count / total_habits_count * 100)) if total_habits_count > 0 else 0
        weekly_rates.append(rate)

    # Recent activity logs (last 5 completions)
    recent_activity = db.execute('''
        SELECT hc.completion_date, hc.created_at, h.name, h.category, h.color, h.icon
        FROM habit_completions hc
        JOIN habits h ON hc.habit_id = h.id
        WHERE hc.user_id = ?
        ORDER BY hc.created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    # Select quote of the day
    day_idx = today_obj.toordinal() % len(MOTIVATIONAL_QUOTES)
    quote, author = MOTIVATIONAL_QUOTES[day_idx]

    # Greeting based on time of day
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # User settings
    settings = db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()

    return render_template(
        'app/dashboard.html',
        stats=stats,
        habits=habits_list,
        weekly_labels=weekly_labels,
        weekly_rates=weekly_rates,
        recent_activity=recent_activity,
        quote=quote,
        author=author,
        greeting=greeting,
        settings=settings,
        today_date=today_obj.strftime('%A, %B %d, %Y')
    )

@dashboard_bp.route('/api/toggle-habit', methods=['POST'])
@login_required
def toggle_habit():
    """Toggle completion of a habit for today or a specific date."""
    db = get_db()
    user_id = g.user['id']
    data = request.get_json() or request.form

    habit_id = data.get('habit_id')
    target_date = data.get('date', date.today().isoformat())

    if not habit_id:
        return jsonify({'success': False, 'error': 'Missing habit_id'}), 400

    # Verify ownership
    habit = db.execute(
        "SELECT * FROM habits WHERE id = ? AND user_id = ?",
        (habit_id, user_id)
    ).fetchone()

    if not habit:
        return jsonify({'success': False, 'error': 'Habit not found or unauthorized'}), 404

    # Check if already completed on this date
    existing = db.execute('''
        SELECT id FROM habit_completions
        WHERE habit_id = ? AND user_id = ? AND completion_date = ?
    ''', (habit_id, user_id, target_date)).fetchone()

    if existing:
        # Undo completion
        db.execute("DELETE FROM habit_completions WHERE id = ?", (existing['id'],))
        completed = False
        message = f"Marked '{habit['name']}' as incomplete."
    else:
        # Mark as completed
        db.execute('''
            INSERT INTO habit_completions (habit_id, user_id, completion_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (habit_id, user_id, target_date, 'Completed via dashboard'))
        completed = True
        message = f"Bravo! '{habit['name']}' completed."

    db.commit()

    # Re-evaluate achievements
    new_achievements = check_and_unlock_achievements(db, user_id)

    # Fresh stats
    stats = get_user_stats(db, user_id)
    habit_streak = calculate_habit_streak(db, habit_id)

    return jsonify({
        'success': True,
        'completed': completed,
        'message': message,
        'stats': stats,
        'habit_streak': habit_streak,
        'new_achievements': new_achievements
    })
