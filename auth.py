from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import functools
from database import get_db, create_default_habits_for_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Please sign in to access HabitFlow.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        return view(**kwargs)
    return wrapped_view

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if g.user is not None:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []
        if not name:
            errors.append('Full name is required.')
        if not email or '@' not in email:
            errors.append('A valid email address is required.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        db = get_db()
        if not errors:
            existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing:
                errors.append('An account with this email already exists.')

        if not errors:
            hashed = generate_password_hash(password)
            cur = db.execute('''
                INSERT INTO users (name, email, password_hash, avatar)
                VALUES (?, ?, ?, ?)
            ''', (name, email, hashed, 'indigo'))
            user_id = cur.lastrowid
            
            # Automatically populate the default habits (Reading, Study, Water Intake)
            create_default_habits_for_user(db, user_id)
            db.commit()

            session.clear()
            session['user_id'] = user_id
            flash(f'Welcome to HabitFlow, {name}! Your starter habits have been initialized.', 'success')
            return redirect(url_for('dashboard.index'))

        for err in errors:
            flash(err, 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html')

        session.clear()
        session['user_id'] = user['id']
        flash(f'Welcome back, {user["name"]}!', 'success')

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html')

@auth_bp.route('/demo-login', methods=['GET', 'POST'])
def demo_login():
    """One-click instant login as Alex Vance for effortless review/demoing."""
    db = get_db()
    demo_user = db.execute('SELECT * FROM users WHERE email = ?', ('demo@habitflow.com',)).fetchone()
    
    if not demo_user:
        # If database wasn't seeded yet, seed it now
        from seed import seed_database
        target_path = current_app.config.get('DATABASE')
        seed_database(target_path)
        demo_user = db.execute('SELECT * FROM users WHERE email = ?', ('demo@habitflow.com',)).fetchone()

    session.clear()
    session['user_id'] = demo_user['id']
    flash('Signed in as Demo User (Alex Vance) with loaded habits and analytics.', 'success')
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out safely.', 'info')
    return redirect(url_for('main.index'))
