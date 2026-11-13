import unittest
import os
import tempfile
import sqlite3
from app import create_app
from database import get_db, calculate_user_streak, calculate_habit_streak
from datetime import date, timedelta

class HabitFlowComprehensiveTests(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app({
            'TESTING': True,
            'DATABASE': self.db_path,
            'SECRET_KEY': 'test-secret-key'
        })
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def register_user(self, name='Tester', email='test@habitflow.com', password='password123'):
        return self.client.post('/auth/register', data={
            'name': name,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

    def login_user(self, email='test@habitflow.com', password='password123'):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_landing_page(self):
        """Test public landing page loads properly."""
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'HabitFlow', rv.data)
        self.assertIn(b'Small habits.', rv.data)
        self.assertIn(b'Extraordinary progress.', rv.data)
        self.assertIn(b'Daily Reading', rv.data)
        self.assertIn(b'Focused Study', rv.data)
        self.assertIn(b'Water Intake', rv.data)

    def test_registration_and_preloaded_habits(self):
        """Test user registration automatically provisions Reading, Study, and Water Intake."""
        rv = self.register_user('John Doe', 'john@test.com', 'securepass123')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Welcome to HabitFlow', rv.data)

        with self.app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'john@test.com'").fetchone()
            self.assertIsNotNone(user)
            habits = db.execute("SELECT name, category FROM habits WHERE user_id = ?", (user['id'],)).fetchall()
            habit_names = [h['name'] for h in habits]
            
            # Check for the required pre-loaded habits requested by the user
            self.assertIn('Daily Reading', habit_names)
            self.assertIn('Focused Study', habit_names)
            self.assertIn('Water Intake', habit_names)

    def test_demo_login(self):
        """Test 1-click Demo Login functionality."""
        rv = self.client.post('/auth/demo-login', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Overview', rv.data)
        self.assertIn(b'Alex Vance', rv.data)

    def test_login_and_logout(self):
        """Test login with valid and invalid credentials."""
        self.register_user('Jane Doe', 'jane@test.com', 'mypassword')
        # Logout
        rv = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn(b'signed out safely', rv.data)

        # Invalid login
        rv = self.login_user('jane@test.com', 'wrongpassword')
        self.assertIn(b'Invalid email or password', rv.data)

        # Valid login
        rv = self.login_user('jane@test.com', 'mypassword')
        self.assertIn(b'Welcome back', rv.data)
        self.assertIn(b'Overview', rv.data)

    def test_habit_creation_editing_and_deletion(self):
        """Test creating, editing, and deleting a habit."""
        self.register_user('Alex', 'alex@test.com', 'pass1234')

        # Create
        rv = self.client.post('/app/habits/create', data={
            'name': 'Evening Meditation',
            'description': 'Mindfulness practice',
            'category': 'Mindfulness',
            'frequency': 'daily',
            'target_value': '15',
            'target_unit': 'minutes',
            'reminder_time': '21:00',
            'reminder_enabled': '1',
            'color': '#8B5CF6'
        }, follow_redirects=True)
        self.assertIn(b'Evening Meditation', rv.data)

        with self.app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'alex@test.com'").fetchone()
            habit = db.execute("SELECT id FROM habits WHERE user_id = ? AND name = 'Evening Meditation'", (user['id'],)).fetchone()
            self.assertIsNotNone(habit)
            h_id = habit['id']

        # Edit
        rv = self.client.post(f'/app/habits/{h_id}/edit', data={
            'name': 'Night Meditation',
            'description': 'Deep breathing before sleep',
            'category': 'Mindfulness',
            'frequency': 'daily',
            'target_value': '20',
            'target_unit': 'minutes',
            'reminder_time': '22:00',
            'reminder_enabled': '1',
            'color': '#8B5CF6'
        }, follow_redirects=True)
        self.assertIn(b'Night Meditation', rv.data)

        # Delete
        rv = self.client.post(f'/app/habits/{h_id}/delete', follow_redirects=True)
        self.assertIn(b'has been removed', rv.data)

    def test_habit_completion_toggle(self):
        """Test toggling habit completion via AJAX API."""
        self.register_user('Chris', 'chris@test.com', 'pass1234')
        with self.app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'chris@test.com'").fetchone()
            habit = db.execute("SELECT id FROM habits WHERE user_id = ?", (user['id'],)).fetchone()
            habit_id = habit['id']

        # Toggle on
        rv = self.client.post('/app/api/toggle-habit', json={'habit_id': habit_id})
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['completed'])
        self.assertEqual(data['stats']['completed_today'], 1)

        # Toggle off
        rv = self.client.post('/app/api/toggle-habit', json={'habit_id': habit_id})
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertTrue(data['success'])
        self.assertFalse(data['completed'])
        self.assertEqual(data['stats']['completed_today'], 0)

    def test_streak_calculation(self):
        """Test multi-day streak calculation logic."""
        self.register_user('Sam', 'sam@test.com', 'pass1234')
        with self.app.app_context():
            db = get_db()
            user = db.execute("SELECT id FROM users WHERE email = 'sam@test.com'").fetchone()
            habit = db.execute("SELECT id FROM habits WHERE user_id = ?", (user['id'],)).fetchone()
            
            today = date.today()
            # 3-day streak
            for i in range(3):
                d_str = (today - timedelta(days=i)).isoformat()
                db.execute(
                    "INSERT INTO habit_completions (habit_id, user_id, completion_date) VALUES (?, ?, ?)",
                    (habit['id'], user['id'], d_str)
                )
            db.commit()

            curr_streak, longest_streak = calculate_user_streak(db, user['id'])
            self.assertEqual(curr_streak, 3)
            self.assertEqual(longest_streak, 3)

    def test_settings_updates(self):
        """Test updating profile, preferences, and password."""
        self.register_user('Emma', 'emma@test.com', 'initialpass')

        # Update profile
        rv = self.client.post('/app/settings/profile', data={
            'name': 'Emma Watson',
            'bio': 'Passionate reader and learner',
            'avatar': 'indigo'
        }, follow_redirects=True)
        self.assertIn(b'Profile updated successfully', rv.data)

        # Update preferences
        rv = self.client.post('/app/settings/preferences', data={
            'start_of_week': 'sunday',
            'daily_reminder_time': '21:30',
            'sound_effects': '1',
            'browser_notifications': '1'
        }, follow_redirects=True)
        self.assertIn(b'Preferences saved successfully', rv.data)

        # Change password
        rv = self.client.post('/app/settings/password', data={
            'current_password': 'initialpass',
            'new_password': 'brandnewpass123',
            'confirm_password': 'brandnewpass123'
        }, follow_redirects=True)
        self.assertIn(b'Password changed successfully', rv.data)

    def test_protected_routes(self):
        """Verify unauthenticated users cannot access /app/ routes."""
        for path in ['/app/', '/app/habits/', '/app/analytics/', '/app/calendar/', '/app/achievements/', '/app/settings/']:
            rv = self.client.get(path, follow_redirects=False)
            self.assertEqual(rv.status_code, 302)
            self.assertIn('/auth/login', rv.headers['Location'])

    def test_api_endpoints(self):
        """Test analytics chart-data and calendar day-details API."""
        self.register_user('David', 'david@test.com', 'pass1234')
        
        # Test analytics chart-data
        rv = self.client.get('/app/analytics/api/chart-data?days=7')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn('labels', data)
        self.assertEqual(len(data['labels']), 7)

        # Test calendar day-details
        today_str = date.today().isoformat()
        rv = self.client.get(f'/app/calendar/api/day-details?date={today_str}')
        self.assertEqual(rv.status_code, 200)
        data = rv.get_json()
        self.assertIn('habits', data)
        self.assertGreaterEqual(len(data['habits']), 3)

if __name__ == '__main__':
    unittest.main()
