from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from auth import login_required
from database import get_db

settings_bp = Blueprint('settings', __name__, url_prefix='/app/settings')

@settings_bp.route('/', methods=['GET'])
@login_required
def index():
    db = get_db()
    user_id = g.user['id']

    settings = db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    if not settings:
        db.execute('''
            INSERT INTO user_settings (user_id, browser_notifications, sound_effects, daily_reminder_time, start_of_week, theme_accent)
            VALUES (?, 1, 1, '20:00', 'monday', 'indigo')
        ''', (user_id,))
        db.commit()
        settings = db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()

    # Get user's active habits to show reminder configuration
    habits = db.execute("SELECT * FROM habits WHERE user_id = ? AND is_archived = 0 ORDER BY reminder_time ASC", (user_id,)).fetchall()

    return render_template('app/settings.html', settings=settings, habits=habits)

@settings_bp.route('/profile', methods=['POST'])
@login_required
def update_profile():
    db = get_db()
    user_id = g.user['id']

    name = request.form.get('name', '').strip()
    bio = request.form.get('bio', '').strip()
    avatar = request.form.get('avatar', 'indigo')

    if not name:
        flash('Display name cannot be empty.', 'danger')
        return redirect(url_for('settings.index'))

    db.execute('''
        UPDATE users 
        SET name = ?, bio = ?, avatar = ? 
        WHERE id = ?
    ''', (name, bio, avatar, user_id))
    db.commit()

    flash('Profile updated successfully.', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/password', methods=['POST'])
@login_required
def update_password():
    db = get_db()
    user_id = g.user['id']

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    user = db.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()

    if not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.index'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'danger')
        return redirect(url_for('settings.index'))

    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('settings.index'))

    new_hash = generate_password_hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    db.commit()

    flash('Password changed successfully.', 'success')
    return redirect(url_for('settings.index'))

@settings_bp.route('/preferences', methods=['POST'])
@login_required
def update_preferences():
    db = get_db()
    user_id = g.user['id']

    browser_notifications = 1 if request.form.get('browser_notifications') else 0
    sound_effects = 1 if request.form.get('sound_effects') else 0
    daily_reminder_time = request.form.get('daily_reminder_time', '20:00')
    start_of_week = request.form.get('start_of_week', 'monday')
    theme_accent = request.form.get('theme_accent', 'indigo')

    db.execute('''
        UPDATE user_settings 
        SET browser_notifications = ?, sound_effects = ?, daily_reminder_time = ?, start_of_week = ?, theme_accent = ?
        WHERE user_id = ?
    ''', (browser_notifications, sound_effects, daily_reminder_time, start_of_week, theme_accent, user_id))
    db.commit()

    flash('Preferences saved successfully.', 'success')
    return redirect(url_for('settings.index'))
