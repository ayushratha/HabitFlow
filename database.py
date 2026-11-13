import sqlite3
import os
from datetime import datetime, date, timedelta
from flask import g, current_app

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        schema_path = os.path.join(app.config['BASE_DIR'] if 'BASE_DIR' in app.config else os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        db.commit()
        seed_achievements(db)

def seed_achievements(db):
    """Seed system achievements catalogue if not already populated."""
    achievements = [
        ('first-step', 'First Step', 'Completed your very first habit', 'sparkles', 'Milestone', 'first_habit', 1),
        ('streak-3', '3-Day Momentum', 'Maintained an unbroken 3-day daily streak', 'zap', 'Streak', 'streak', 3),
        ('streak-7', 'Unstoppable Week', 'Achieved a perfect 7-day streak', 'flame', 'Streak', 'streak', 7),
        ('streak-21', 'Habit Formed', 'Reached 21 consecutive days of progress', 'target', 'Streak', 'streak', 21),
        ('streak-30', 'Monthly Master', 'Completed 30 days of consistent discipline', 'crown', 'Streak', 'streak', 30),
        ('streak-100', 'Century Club', '100 days of relentless dedication', 'award', 'Streak', 'streak', 100),
        ('completions-25', 'Quarter Century', 'Logged 25 total habit check-ins', 'check-check', 'Volume', 'total_completions', 25),
        ('completions-50', 'Habit Enthusiast', 'Logged 50 total habit check-ins', 'trophy', 'Volume', 'total_completions', 50),
        ('completions-100', 'Discipline Centurion', 'Logged 100 total habit check-ins', 'medal', 'Volume', 'total_completions', 100),
        ('habits-3', 'Triple Threat', 'Created and tracking 3 active habits', 'layers', 'Setup', 'active_habits', 3),
        ('habits-5', 'High Performer', 'Created and tracking 5 active habits', 'star', 'Setup', 'active_habits', 5),
    ]
    for slug, title, desc, icon, cat, req_type, req_val in achievements:
        db.execute('''
            INSERT OR IGNORE INTO achievements (slug, title, description, icon, category, req_type, req_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (slug, title, desc, icon, cat, req_type, req_val))
    db.commit()

def create_default_habits_for_user(db, user_id):
    """
    Pre-populates new users with the required starting habits:
    - Reading (Learning)
    - Study (Productivity)
    - Water Intake (Health)
    """
    default_habits = [
        (
            user_id,
            'Daily Reading',
            'Read 20 pages or 30 minutes of non-fiction or literature to sharpen the mind.',
            'Learning',
            'daily',
            20,
            'pages',
            '08:30',
            1,
            '#3B82F6', # Indigo / Electric Blue
            'book-open'
        ),
        (
            user_id,
            'Focused Study',
            'Dedicated 60-minute deep work or curriculum study session without distractions.',
            'Productivity',
            'daily',
            60,
            'minutes',
            '10:00',
            1,
            '#8B5CF6', # Purple
            'brain'
        ),
        (
            user_id,
            'Water Intake',
            'Drink at least 2.5 liters (8 glasses) of pure water to stay energized and focused.',
            'Health',
            'daily',
            8,
            'glasses',
            '07:30',
            1,
            '#06B6D4', # Cyan / Emerald
            'droplet'
        )
    ]

    for habit in default_habits:
        db.execute('''
            INSERT INTO habits (user_id, name, description, category, frequency, target_value, target_unit, reminder_time, reminder_enabled, color, icon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', habit)

    # Initialize user settings
    db.execute('''
        INSERT OR IGNORE INTO user_settings (user_id, browser_notifications, sound_effects, daily_reminder_time, start_of_week, theme_accent)
        VALUES (?, 1, 1, '20:00', 'monday', 'indigo')
    ''', (user_id,))
    db.commit()

def calculate_user_streak(db, user_id):
    """
    Calculates the user's current consecutive active day streak and their all-time longest streak.
    A day counts towards streak if at least 1 habit was completed on that date.
    """
    rows = db.execute('''
        SELECT DISTINCT completion_date 
        FROM habit_completions 
        WHERE user_id = ? 
        ORDER BY completion_date DESC
    ''', (user_id,)).fetchall()

    if not rows:
        return 0, 0

    dates = [datetime.strptime(r['completion_date'], '%Y-%m-%d').date() for r in rows]
    date_set = set(dates)

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Determine starting point of current streak:
    # If completed today, start today. Else if completed yesterday, start yesterday.
    # Otherwise, current streak is 0.
    current_streak = 0
    if today in date_set:
        check_date = today
        while check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)
    elif yesterday in date_set:
        check_date = yesterday
        while check_date in date_set:
            current_streak += 1
            check_date -= timedelta(days=1)
    else:
        current_streak = 0

    # Calculate longest streak across all recorded unique dates
    sorted_dates = sorted(list(date_set))
    longest_streak = 0
    temp_streak = 0
    last_d = None

    for d in sorted_dates:
        if last_d is None or d == last_d + timedelta(days=1):
            temp_streak += 1
        else:
            temp_streak = 1
        if temp_streak > longest_streak:
            longest_streak = temp_streak
        last_d = d

    longest_streak = max(longest_streak, current_streak)
    return current_streak, longest_streak

def calculate_habit_streak(db, habit_id):
    """Calculates streak for a specific habit."""
    rows = db.execute('''
        SELECT completion_date 
        FROM habit_completions 
        WHERE habit_id = ? 
        ORDER BY completion_date DESC
    ''', (habit_id,)).fetchall()

    if not rows:
        return 0

    date_set = {datetime.strptime(r['completion_date'], '%Y-%m-%d').date() for r in rows}
    today = date.today()
    yesterday = today - timedelta(days=1)

    streak = 0
    if today in date_set:
        check_date = today
    elif yesterday in date_set:
        check_date = yesterday
    else:
        return 0

    while check_date in date_set:
        streak += 1
        check_date -= timedelta(days=1)

    return streak

def get_user_stats(db, user_id):
    today_str = date.today().isoformat()
    
    # Active habits count
    active_habits_row = db.execute(
        "SELECT COUNT(*) as cnt FROM habits WHERE user_id = ? AND is_archived = 0",
        (user_id,)
    ).fetchone()
    total_active = active_habits_row['cnt'] if active_habits_row else 0

    # Habits completed today
    completed_today_row = db.execute('''
        SELECT COUNT(DISTINCT hc.habit_id) as cnt 
        FROM habit_completions hc
        JOIN habits h ON hc.habit_id = h.id
        WHERE hc.user_id = ? AND hc.completion_date = ? AND h.is_archived = 0
    ''', (user_id, today_str)).fetchone()
    completed_today = completed_today_row['cnt'] if completed_today_row else 0

    # Total lifetime completions
    total_completions_row = db.execute(
        "SELECT COUNT(*) as cnt FROM habit_completions WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    total_completions = total_completions_row['cnt'] if total_completions_row else 0

    # Success rate today
    daily_success_rate = round((completed_today / total_active * 100)) if total_active > 0 else 0

    # Streaks
    current_streak, best_streak = calculate_user_streak(db, user_id)

    return {
        'total_active': total_active,
        'completed_today': completed_today,
        'daily_success_rate': daily_success_rate,
        'current_streak': current_streak,
        'best_streak': best_streak,
        'total_completions': total_completions
    }

def check_and_unlock_achievements(db, user_id):
    """
    Evaluates milestone progress and unlocks eligible achievements for user.
    Returns list of newly unlocked achievements.
    """
    stats = get_user_stats(db, user_id)
    current_streak = stats['current_streak']
    best_streak = stats['best_streak']
    total_completions = stats['total_completions']
    total_active = stats['total_active']

    all_achievements = db.execute("SELECT * FROM achievements").fetchall()
    unlocked_ids = {r['achievement_id'] for r in db.execute(
        "SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,)
    ).fetchall()}

    newly_unlocked = []

    for ach in all_achievements:
        ach_id = ach['id']
        if ach_id in unlocked_ids:
            continue

        req_type = ach['req_type']
        req_val = ach['req_value']
        qualifies = False

        if req_type == 'first_habit' and total_completions >= req_val:
            qualifies = True
        elif req_type == 'streak' and best_streak >= req_val:
            qualifies = True
        elif req_type == 'total_completions' and total_completions >= req_val:
            qualifies = True
        elif req_type == 'active_habits' and total_active >= req_val:
            qualifies = True

        if qualifies:
            db.execute('''
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, unlocked_at)
                VALUES (?, ?, ?)
            ''', (user_id, ach_id, datetime.now().isoformat()))
            newly_unlocked.append(ach['title'])

    if newly_unlocked:
        db.commit()

    return newly_unlocked
