"""
HabitFlow Database Seeder
Sets up initial tables and seeds a rich demo account with historical data.
"""
import sqlite3
import os
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from config import Config
from database import seed_achievements

def seed_database(target_db_path=None):
    db_path = target_db_path or Config.DATABASE
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON;")

    # Run schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()

    # Seed achievements catalogue
    seed_achievements(db)

    # Check if demo user exists
    demo_email = 'demo@habitflow.com'
    existing = db.execute("SELECT id FROM users WHERE email = ?", (demo_email,)).fetchone()
    
    if existing:
        user_id = existing['id']
        print(f"Demo user already exists (id: {user_id}).")
    else:
        # Create demo user
        hashed = generate_password_hash('password123')
        cursor = db.execute('''
            INSERT INTO users (name, email, password_hash, bio, avatar)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Alex Vance', demo_email, hashed, 'SaaS Product Designer & Habit Enthusiast', 'indigo'))
        user_id = cursor.lastrowid

        # User settings
        db.execute('''
            INSERT INTO user_settings (user_id, browser_notifications, sound_effects, daily_reminder_time, start_of_week, theme_accent)
            VALUES (?, 1, 1, '20:30', 'monday', 'indigo')
        ''', (user_id,))
        print(f"Created demo user: {demo_email} (id: {user_id})")

    # Ensure required default habits exist for demo user:
    # 1) Reading
    # 2) Study
    # 3) Water Intake
    # plus Morning Meditation and Evening Reflection
    habits_data = [
        ('Daily Reading', 'Read 20 pages or 30 minutes of high-value books daily.', 'Learning', 'daily', 20, 'pages', '08:30', 1, '#3B82F6', 'book-open'),
        ('Focused Study', 'Dedicated 60-minute deep work / study block with zero distractions.', 'Productivity', 'daily', 60, 'minutes', '10:00', 1, '#8B5CF6', 'brain'),
        ('Water Intake', 'Drink at least 2.5L (8 glasses) of pure water daily.', 'Health', 'daily', 8, 'glasses', '07:30', 1, '#06B6D4', 'droplet'),
        ('Morning Movement', '20-30 min mobility, gym session, or light yoga.', 'Health', 'daily', 30, 'minutes', '07:00', 1, '#10B981', 'activity'),
        ('Evening Review', 'Reflect on daily wins, learnings, and plan tomorrow.', 'Mindfulness', 'daily', 10, 'minutes', '21:30', 1, '#F59E0B', 'sun')
    ]

    habit_ids = {}
    for name, desc, cat, freq, tval, tunit, rtime, renable, color, icon in habits_data:
        row = db.execute("SELECT id FROM habits WHERE user_id = ? AND name = ?", (user_id, name)).fetchone()
        if not row:
            cur = db.execute('''
                INSERT INTO habits (user_id, name, description, category, frequency, target_value, target_unit, reminder_time, reminder_enabled, color, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, desc, cat, freq, tval, tunit, rtime, renable, color, icon))
            habit_ids[name] = cur.lastrowid
        else:
            habit_ids[name] = row['id']

    # Generate realistic historical completions over the past 28 days
    # To create an active 12-day current streak and great analytics charts
    today = date.today()
    for days_ago in range(28, -1, -1):
        target_date = today - timedelta(days=days_ago)
        target_date_str = target_date.isoformat()

        # Simulate completion patterns:
        # Last 12 days: nearly 100% completion (creating strong current streak)
        # Older days: 70-80% completion with realistic minor variations
        for h_name, h_id in habit_ids.items():
            should_complete = False
            if days_ago <= 12:
                # Active streak period: complete almost everything
                if days_ago == 0:
                    # Today: complete Reading and Water Intake, leave Study to check off interactively!
                    if h_name in ('Daily Reading', 'Water Intake'):
                        should_complete = True
                else:
                    if h_name != 'Evening Review' or days_ago % 4 != 0:
                        should_complete = True
            else:
                # Earlier history (past 28 days down to 13 days ago)
                # Some completed, creating a natural realistic curve
                if (days_ago + hash(h_name)) % 7 not in (2, 5):
                    should_complete = True

            if should_complete:
                db.execute('''
                    INSERT OR IGNORE INTO habit_completions (habit_id, user_id, completion_date, notes)
                    VALUES (?, ?, ?, ?)
                ''', (h_id, user_id, target_date_str, 'Completed daily target.'))

    db.commit()

    # Now unlock eligible achievements for demo user
    from database import check_and_unlock_achievements
    unlocked = check_and_unlock_achievements(db, user_id)
    print(f"Unlocked achievements for demo user: {unlocked}")

    db.close()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_database()
