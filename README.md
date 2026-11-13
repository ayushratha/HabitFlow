# HabitFlow — Premium SaaS Habit Tracker

> **Build better days. One habit at a time.**

HabitFlow is a production-quality, minimal SaaS daily habit tracking web application inspired by the design precision of Linear, Notion, and Stripe. Engineered with **Python Flask** and **SQLite**, it combines atomic consistency, clean visual analytics, and frictionless check-ins into an intentional productivity workspace.

---

## 🌟 Key Highlights & Features

### 1. Pre-Loaded Starter Habits
Every newly registered user (and the pre-seeded demo user) immediately starts with three foundational daily habits:
- 📖 **Daily Reading**: 20 pages or 30 minutes of high-value books (Category: *Learning*)
- 🧠 **Focused Study**: 60-minute deep work session without distractions (Category: *Productivity*)
- 💧 **Water Intake**: Drink 2.5L / 8 glasses of pure water (Category: *Health*)

### 2. High-Converting Landing Page
- Minimal SaaS hero with live interactive dashboard mock preview.
- Social proof metrics (94.2% streak retention, 100k+ completions).
- Feature showcases (unbroken streaks, visual analytics, rhythm calendar, gamified milestones).
- "How HabitFlow Works" 3-step walkthrough.
- Sample user testimonials and interactive FAQ accordion.

### 3. Application Dashboard (Overview)
- **Top 5 KPI Metrics**: Total Active Habits, Completed Today, Daily Success Rate (%), Current Streak, and Best Streak.
- **Today's Habits Checklist**: Interactive check-off with instant AJAX state update, streak counters, and category pills.
- **Weekly Activity Chart**: Mini Chart.js bar chart showing 7-day completion percentages.
- **Recent Activity Feed**: Real-time audit log of recent check-ins.
- **Daily Motivational Quote**: Dynamic quote of the day.

### 4. My Habits Management
- **Dual View Modes**: Switch between Grid and List view layouts.
- **Real-Time Client Search**: Search habits instantly by title or category.
- **Category Filters**: Filter by All, Health, Learning, Productivity, Mindfulness, Fitness, Finance.
- **Sorting**: Sort by Newest, Highest Streak, Most Completions, or Name.
- **Full CRUD**: Create, edit, and delete habits with customizable targets, units, colors, and reminder times.

### 5. Deep Visual Analytics
- **Dynamic Time-Series Chart**: Switch between Last 7 Days, Last 30 Days, and Last 90 Days.
- **Category Distribution**: Doughnut chart visualizing completion concentration.
- **Consistency Rankings**: Identify highest consistency habits vs. habits needing attention (<60%).
- **KPI Metrics**: 30-day consistency percentage and total lifetime completions.

### 6. Interactive Rhythm Calendar
- Monthly calendar grid with color-coded completion badges:
  - 🟢 **100% Completed**: Emerald badge
  - 🟡 **Partially Completed**: Warm amber badge
  - ⚪ **Missed / Incomplete**: Subtle neutral badge
- Month/Year navigation (`Prev`, `Next`, `Today`).
- **Day Inspector Modal**: Click any calendar day to inspect every habit's status on that specific date.

### 7. Streaks & Gamified Achievements
- Unbroken streak calculation based on real SQLite database records.
- 11 Milestone Badges (First Step, 3-Day Momentum, 7-Day Unstoppable, 21-Day Habit Formed, 30-Day Master, 100-Day Century Club, Volume Badges, and Multi-Habit Builder).
- Unlocked badges display timestamps; locked badges display live progress bars.

### 8. Notifications & Reminders
- Schedule custom reminder times per habit.
- In-app notification bell with active remaining count.
- Web Browser Notification API integration with one-click permission request.
- Technically honest disclosure: clear explanation that browser notifications require an open tab.

### 9. User Settings & Security
- Edit profile (Display Name, Bio).
- Account preferences (Calendar start day: Monday/Sunday, daily digest reminder time).
- Security: Change password with verification of current password.
- Secure password hashing with Werkzeug (`generate_password_hash` / `check_password_hash`).
- Session-based CSRF protection and parameterized SQL queries.

---

## 🏗️ Technical Architecture & Stack

- **Backend**: Python 3.12+ / Flask 3.0
- **Database**: SQLite3 with foreign keys, unique constraints (`habit_id` + `completion_date`), and indexed queries.
- **Frontend**: HTML5, CSS3 Custom Properties (Design System), Vanilla JavaScript.
- **Charts**: Chart.js 4.4
- **Typography**: Inter (Google Fonts)

```
habitflow/
│
├── app.py                     # Flask application factory, routes registration & lifecycle
├── config.py                  # Environment configurations & database paths
├── database.py                # Database connection, streak math, stats & achievement triggers
├── schema.sql                 # SQLite schema definitions & indexes
├── seed.py                    # Seeder populating demo user and 28-day completion history
├── auth.py                    # Authentication blueprint (Login, Register, Demo Login, Logout)
├── wsgi.py                    # WSGI entry point for PythonAnywhere & production servers
├── requirements.txt           # Python dependencies
├── routes/
│   ├── main.py                # Public landing page, privacy, terms
│   ├── dashboard.py           # App overview, metrics, AJAX toggle API
│   ├── habits.py              # Habits CRUD & search filters
│   ├── analytics.py           # Analytics view & time-series data endpoint
│   ├── calendar_view.py       # Calendar matrix & day details endpoint
│   ├── achievements.py        # Gamified milestone badges & progress
│   └── settings.py            # Profile, security, reminders & preferences
├── static/
│   ├── css/
│   │   ├── style.css          # Core design system tokens, typography, buttons, forms
│   │   └── components.css     # App shell, landing page, cards, calendar, badges
│   ├── js/
│   │   ├── main.js            # Sidebar drawer, notifications, modal handlers, toasts
│   │   ├── dashboard.js       # AJAX habit toggle, live KPI counters, weekly chart
│   │   ├── habits.js          # Client-side search, grid/list toggle, modal setup
│   │   ├── analytics.js       # Chart.js time-series trend & category doughnut
│   │   └── calendar.js        # Interactive day inspector modal
│   └── img/
│       └── logo.svg           # HabitFlow geometric vector logo
└── templates/
    ├── base.html              # Core HTML shell
    ├── app_base.html          # Authenticated app layout with sidebar & topbar
    ├── index.html             # High-converting landing page
    ├── privacy.html           # Privacy policy
    ├── terms.html             # Terms of service
    ├── auth/
    │   ├── login.html         # Split-screen sign in with 1-click Demo Account
    │   └── register.html      # Split-screen registration (pre-seeds Reading, Study, Water)
    ├── app/
    │   ├── dashboard.html     # App overview dashboard
    │   ├── habits.html        # My Habits management & filters
    │   ├── analytics.html     # Deep dive charts & consistency ranking
    │   ├── calendar.html      # Monthly rhythm calendar & inspector
    │   ├── achievements.html  # Streaks & milestone badges
    │   └── settings.html      # Profile, security & notification settings
    └── errors/
        ├── 404.html           # Custom 404
        └── 500.html           # Custom 500
```

---

## 🚀 Getting Started Locally

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- `pip` package manager

### 2. Clone or Navigate to Directory
```bash
cd habitflow
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Seed the Database (Optional but Recommended)
Populates demo user (`demo@habitflow.com` / `password123`) with 28 days of historical data:
```bash
python seed.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to:
**http://127.0.0.1:5000**

---

## 🔑 Demo Account Credentials

For instant evaluation, you can either click the **"One-Click Demo Account"** button on the Login page, or enter:
- **Email**: `demo@habitflow.com`
- **Password**: `password123`

Or register any new account to automatically receive:
1. **Daily Reading** (Learning)
2. **Focused Study** (Productivity)
3. **Water Intake** (Health)

---

## 🌐 Deploying to PythonAnywhere

HabitFlow is 100% compatible with [PythonAnywhere](https://www.pythonanywhere.com/):

1. **Sign Up / Log In** to PythonAnywhere.
2. Open a **Bash Console** in PythonAnywhere and clone/upload your repository:
   ```bash
   git clone <your-repo-url> habitflow
   cd habitflow
   ```
3. Create and activate a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.12 habitflow-venv
   pip install -r requirements.txt
   python seed.py
   ```
4. In the PythonAnywhere **Web** tab:
   - Click **Add a new web app**.
   - Choose **Manual configuration** and select **Python 3.12**.
   - Under **Virtualenv**, set the path: `/home/<your-username>/.virtualenvs/habitflow-venv`.
   - Under **Code**, set the Source directory: `/home/<your-username>/habitflow`.
5. Open the **WSGI configuration file** link and set it to:
   ```python
   import sys
   import os

   path = '/home/<your-username>/habitflow'
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```
6. Click the green **Reload** button in the Web tab. Your HabitFlow SaaS application is now live!

---

## 🛡️ Security Best Practices
- **Password Protection**: Passwords hashed using Werkzeug PBKDF2/SHA256. Plain passwords are never stored.
- **SQL Injection Prevention**: 100% parameterized SQLite queries via `?` place-holders.
- **CSRF Defense**: Session-tied cryptographic tokens attached to forms and API calls.
- **Access Control**: `@login_required` decorators ensure users only access and modify their own records.
- **Session Safety**: HTTPOnly cookies with `SameSite=Lax` protection.

---

## 📄 License
MIT License. Built for intentional living and high performance.
