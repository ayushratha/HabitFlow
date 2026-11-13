/**
 * HabitFlow — My Habits Management JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Grid vs List View Toggle
  const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
  const habitsContainer = document.getElementById('habitsContainer');

  const savedView = localStorage.getItem('habitflow_view_mode') || 'grid';
  setView(savedView);

  viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-view');
      setView(mode);
      localStorage.setItem('habitflow_view_mode', mode);
    });
  });

  function setView(mode) {
    if (!habitsContainer) return;
    viewToggleBtns.forEach(b => {
      if (b.getAttribute('data-view') === mode) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });

    if (mode === 'list') {
      habitsContainer.classList.remove('grid-3');
      habitsContainer.classList.add('habits-list-layout');
    } else {
      habitsContainer.classList.remove('habits-list-layout');
      habitsContainer.classList.add('grid-3');
    }
  }

  // 2. Real-time Search Filter
  const habitSearchInput = document.getElementById('habitSearchInput');
  const habitCards = document.querySelectorAll('.habit-item-card');

  if (habitSearchInput) {
    habitSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      let visibleCount = 0;

      habitCards.forEach(card => {
        const title = card.getAttribute('data-name')?.toLowerCase() || '';
        const desc = card.getAttribute('data-desc')?.toLowerCase() || '';
        const category = card.getAttribute('data-category')?.toLowerCase() || '';

        if (title.includes(query) || desc.includes(query) || category.includes(query)) {
          card.style.display = '';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });

      const emptySearchState = document.getElementById('emptySearchState');
      if (emptySearchState) {
        emptySearchState.style.display = visibleCount === 0 ? 'block' : 'none';
      }
    });
  }

  // 3. Edit Habit Modal Setup
  const editModal = document.getElementById('editHabitModal');
  const editForm = document.getElementById('editHabitForm');

  document.querySelectorAll('.btn-edit-habit').forEach(btn => {
    btn.addEventListener('click', () => {
      const habitId = btn.getAttribute('data-id');
      const name = btn.getAttribute('data-name');
      const description = btn.getAttribute('data-description');
      const category = btn.getAttribute('data-category');
      const frequency = btn.getAttribute('data-frequency');
      const targetValue = btn.getAttribute('data-target-value');
      const targetUnit = btn.getAttribute('data-target-unit');
      const reminderTime = btn.getAttribute('data-reminder-time');
      const reminderEnabled = btn.getAttribute('data-reminder-enabled') === '1';
      const color = btn.getAttribute('data-color');
      const icon = btn.getAttribute('data-icon');

      if (editForm) {
        editForm.action = `/app/habits/${habitId}/edit`;
        document.getElementById('edit_name').value = name;
        document.getElementById('edit_description').value = description;
        document.getElementById('edit_category').value = category;
        document.getElementById('edit_frequency').value = frequency;
        document.getElementById('edit_target_value').value = targetValue;
        document.getElementById('edit_target_unit').value = targetUnit;
        document.getElementById('edit_reminder_time').value = reminderTime;
        document.getElementById('edit_reminder_enabled').checked = reminderEnabled;
        document.getElementById('edit_color').value = color;
        document.getElementById('edit_icon').value = icon;
      }

      if (editModal) editModal.classList.add('active');
    });
  });
});
