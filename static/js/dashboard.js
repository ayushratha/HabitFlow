/**
 * HabitFlow — Dashboard Logic & Charts
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Interactive Habit Toggle Checkboxes
  const habitToggles = document.querySelectorAll('.habit-toggle-checkbox');

  habitToggles.forEach(checkbox => {
    checkbox.addEventListener('change', async (e) => {
      const habitId = checkbox.getAttribute('data-habit-id');
      const card = checkbox.closest('.habit-checklist-card');

      try {
        const response = await fetch('/app/api/toggle-habit', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ habit_id: habitId })
        });

        const data = await response.json();
        if (data.success) {
          if (data.completed) {
            card.classList.add('is-completed');
            showToast(data.message, 'success');
          } else {
            card.classList.remove('is-completed');
            showToast(data.message, 'info');
          }

          // Update streak badge on card
          const streakEl = card.querySelector('.habit-streak-count');
          if (streakEl) {
            streakEl.textContent = `${data.habit_streak}d`;
          }

          // Update Top Metric Cards dynamically
          if (data.stats) {
            const completedEl = document.getElementById('statCompletedToday');
            if (completedEl) completedEl.textContent = data.stats.completed_today;

            const rateEl = document.getElementById('statDailySuccessRate');
            if (rateEl) rateEl.textContent = `${data.stats.daily_success_rate}%`;

            const streakMetricEl = document.getElementById('statCurrentStreak');
            if (streakMetricEl) streakMetricEl.textContent = `${data.stats.current_streak} days`;

            const bestStreakEl = document.getElementById('statBestStreak');
            if (bestStreakEl) bestStreakEl.textContent = `${data.stats.best_streak} days`;

            const progressFill = document.getElementById('statTodayProgressFill');
            if (progressFill) progressFill.style.width = `${data.stats.daily_success_rate}%`;
          }

          // Check if new achievement unlocked
          if (data.new_achievements && data.new_achievements.length > 0) {
            data.new_achievements.forEach(ach => {
              showToast(`🏆 Achievement Unlocked: ${ach}!`, 'success');
            });
          }
        } else {
          showToast(data.error || 'Failed to update habit', 'danger');
          checkbox.checked = !checkbox.checked; // revert
        }
      } catch (err) {
        console.error('Toggle error:', err);
        showToast('Network error while updating habit', 'danger');
        checkbox.checked = !checkbox.checked;
      }
    });
  });

  // 2. Mini Weekly Activity Chart (Chart.js)
  const weeklyCanvas = document.getElementById('weeklyActivityChart');
  if (weeklyCanvas && window.Chart) {
    const rawLabels = weeklyCanvas.getAttribute('data-labels');
    const rawRates = weeklyCanvas.getAttribute('data-rates');

    const labels = rawLabels ? JSON.parse(rawLabels) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const rates = rawRates ? JSON.parse(rawRates) : [80, 90, 75, 100, 85, 90, 95];

    new Chart(weeklyCanvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Success Rate (%)',
          data: rates,
          backgroundColor: '#4F46E5',
          borderRadius: 6,
          barThickness: 20
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#0F172A',
            padding: 10,
            callbacks: {
              label: (item) => `Completion: ${item.raw}%`
            }
          }
        },
        scales: {
          y: {
            min: 0,
            max: 100,
            ticks: {
              stepSize: 25,
              callback: (val) => `${val}%`,
              color: '#94A3B8',
              font: { size: 11 }
            },
            grid: {
              color: '#F1F5F9',
              drawBorder: false
            }
          },
          x: {
            ticks: {
              color: '#64748B',
              font: { size: 12, weight: '500' }
            },
            grid: { display: false }
          }
        }
      }
    });
  }
});
