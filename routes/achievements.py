from flask import Blueprint, render_template, g
from auth import login_required
from database import get_db, get_user_stats, check_and_unlock_achievements

achievements_bp = Blueprint('achievements', __name__, url_prefix='/app/achievements')

@achievements_bp.route('/')
@login_required
def index():
    db = get_db()
    user_id = g.user['id']

    # Trigger fresh check for unlocks
    check_and_unlock_achievements(db, user_id)

    stats = get_user_stats(db, user_id)
    current_streak = stats['current_streak']
    best_streak = stats['best_streak']
    total_completions = stats['total_completions']
    total_active = stats['total_active']

    # Fetch all achievements with unlocked timestamp if user has earned it
    rows = db.execute('''
        SELECT a.*, ua.unlocked_at
        FROM achievements a
        LEFT JOIN user_achievements ua 
          ON a.id = ua.achievement_id AND ua.user_id = ?
        ORDER BY (ua.unlocked_at IS NOT NULL) DESC, a.req_value ASC
    ''', (user_id,)).fetchall()

    badges = []
    unlocked_count = 0

    for r in rows:
        b = dict(r)
        is_unlocked = b['unlocked_at'] is not None
        if is_unlocked:
            unlocked_count += 1
            progress_pct = 100
            current_val = b['req_value']
        else:
            req_type = b['req_type']
            req_val = b['req_value']

            if req_type in ('first_habit', 'total_completions'):
                current_val = total_completions
            elif req_type == 'streak':
                current_val = best_streak
            elif req_type == 'active_habits':
                current_val = total_active
            else:
                current_val = 0

            progress_pct = min(100, round((current_val / req_val) * 100)) if req_val > 0 else 0

        b['is_unlocked'] = is_unlocked
        b['progress_pct'] = progress_pct
        b['current_val'] = current_val
        badges.append(b)

    total_achievements = len(badges)
    completion_rate = round((unlocked_count / total_achievements * 100)) if total_achievements > 0 else 0

    return render_template(
        'app/achievements.html',
        stats=stats,
        badges=badges,
        unlocked_count=unlocked_count,
        total_achievements=total_achievements,
        completion_rate=completion_rate
    )
