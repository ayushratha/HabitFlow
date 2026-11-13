from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import date
from auth import login_required
from database import get_db, calculate_habit_streak, check_and_unlock_achievements

habits_bp = Blueprint('habits', __name__, url_prefix='/app/habits')

CATEGORIES = ['General', 'Health', 'Learning', 'Productivity', 'Mindfulness', 'Fitness', 'Finance']
COLORS = ['#4F46E5', '#3B82F6', '#8B5CF6', '#10B981', '#06B6D4', '#F59E0B', '#EC4899', '#64748B']
ICONS = ['check-circle', 'book-open', 'brain', 'droplet', 'activity', 'sun', 'zap', 'target', 'heart', 'feather']

@habits_bp.route('/')
@login_required
def index():
    db = get_db()
    user_id = g.user['id']
    today_str = date.today().isoformat()

    # Query params for search & filter
    category_filter = request.args.get('category', '').strip()
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'created_desc')

    sql = '''
        SELECT h.*, 
               CASE WHEN hc.id IS NOT NULL THEN 1 ELSE 0 END as completed_today,
               (SELECT COUNT(*) FROM habit_completions WHERE habit_id = h.id) as total_completions
        FROM habits h
        LEFT JOIN habit_completions hc 
          ON h.id = hc.habit_id 
          AND hc.user_id = h.user_id 
          AND hc.completion_date = ?
        WHERE h.user_id = ? AND h.is_archived = 0
    '''
    params = [today_str, user_id]

    if category_filter and category_filter != 'All':
        sql += ' AND h.category = ?'
        params.append(category_filter)

    if search_query:
        sql += ' AND (h.name LIKE ? OR h.description LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if sort_by == 'name_asc':
        sql += ' ORDER BY h.name ASC'
    elif sort_by == 'name_desc':
        sql += ' ORDER BY h.name DESC'
    elif sort_by == 'completions_desc':
        sql += ' ORDER BY total_completions DESC'
    elif sort_by == 'created_asc':
        sql += ' ORDER BY h.created_at ASC'
    else: # created_desc
        sql += ' ORDER BY h.created_at DESC'

    habits_rows = db.execute(sql, params).fetchall()

    habits = []
    for r in habits_rows:
        h = dict(r)
        h['streak'] = calculate_habit_streak(db, h['id'])
        habits.append(h)

    # If sorted by streak
    if sort_by == 'streak_desc':
        habits.sort(key=lambda x: x['streak'], reverse=True)

    # Categories count for filter pills
    counts = db.execute('''
        SELECT category, COUNT(*) as cnt 
        FROM habits 
        WHERE user_id = ? AND is_archived = 0 
        GROUP BY category
    ''', (user_id,)).fetchall()
    category_counts = {r['category']: r['cnt'] for r in counts}
    total_count = sum(category_counts.values())

    return render_template(
        'app/habits.html',
        habits=habits,
        categories=CATEGORIES,
        category_counts=category_counts,
        total_count=total_count,
        current_category=category_filter or 'All',
        search_query=search_query,
        sort_by=sort_by,
        colors=COLORS,
        icons=ICONS
    )

@habits_bp.route('/create', methods=['POST'])
@login_required
def create():
    db = get_db()
    user_id = g.user['id']

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'General')
    frequency = request.form.get('frequency', 'daily')
    target_value = request.form.get('target_value', '1')
    target_unit = request.form.get('target_unit', 'times').strip()
    reminder_time = request.form.get('reminder_time', '09:00')
    reminder_enabled = 1 if request.form.get('reminder_enabled') else 0
    color = request.form.get('color', '#4F46E5')
    icon = request.form.get('icon', 'check-circle')

    if not name:
        flash('Habit title is required.', 'danger')
        return redirect(url_for('habits.index'))

    try:
        t_val = int(target_value) if int(target_value) > 0 else 1
    except ValueError:
        t_val = 1

    db.execute('''
        INSERT INTO habits (user_id, name, description, category, frequency, target_value, target_unit, reminder_time, reminder_enabled, color, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, description, category, frequency, t_val, target_unit, reminder_time, reminder_enabled, color, icon))
    db.commit()

    check_and_unlock_achievements(db, user_id)
    flash(f"Habit '{name}' successfully created.", 'success')
    return redirect(url_for('habits.index'))

@habits_bp.route('/<int:habit_id>/edit', methods=['POST'])
@login_required
def edit(habit_id):
    db = get_db()
    user_id = g.user['id']

    habit = db.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id)).fetchone()
    if not habit:
        flash('Habit not found.', 'danger')
        return redirect(url_for('habits.index'))

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'General')
    frequency = request.form.get('frequency', 'daily')
    target_value = request.form.get('target_value', '1')
    target_unit = request.form.get('target_unit', 'times').strip()
    reminder_time = request.form.get('reminder_time', '09:00')
    reminder_enabled = 1 if request.form.get('reminder_enabled') else 0
    color = request.form.get('color', '#4F46E5')
    icon = request.form.get('icon', 'check-circle')

    if not name:
        flash('Habit title cannot be empty.', 'danger')
        return redirect(url_for('habits.index'))

    try:
        t_val = int(target_value) if int(target_value) > 0 else 1
    except ValueError:
        t_val = 1

    db.execute('''
        UPDATE habits 
        SET name = ?, description = ?, category = ?, frequency = ?, target_value = ?, target_unit = ?, reminder_time = ?, reminder_enabled = ?, color = ?, icon = ?
        WHERE id = ? AND user_id = ?
    ''', (name, description, category, frequency, t_val, target_unit, reminder_time, reminder_enabled, color, icon, habit_id, user_id))
    db.commit()

    flash(f"Habit '{name}' updated successfully.", 'success')
    return redirect(url_for('habits.index'))

@habits_bp.route('/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete(habit_id):
    db = get_db()
    user_id = g.user['id']

    habit = db.execute("SELECT * FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id)).fetchone()
    if not habit:
        flash('Habit not found or unauthorized.', 'danger')
        return redirect(url_for('habits.index'))

    db.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
    db.commit()

    flash(f"Habit '{habit['name']}' has been removed.", 'info')
    return redirect(url_for('habits.index'))
