/**
 * HabitFlow — Calendar Interaction & Day Inspector
 */

document.addEventListener('DOMContentLoaded', () => {
  const dayCells = document.querySelectorAll('.cal-day-cell:not(.empty)');
  const dayModal = document.getElementById('dayDetailsModal');
  const modalTitle = document.getElementById('dayModalTitle');
  const modalList = document.getElementById('dayModalHabitsList');
  const modalSummary = document.getElementById('dayModalSummary');

  dayCells.forEach(cell => {
    cell.addEventListener('click', async () => {
      const dateStr = cell.getAttribute('data-date');
      if (!dateStr) return;

      try {
        const res = await fetch(`/app/calendar/api/day-details?date=${dateStr}`);
        const data = await res.json();

        if (modalTitle) {
          const dateObj = new Date(dateStr + 'T00:00:00');
          modalTitle.textContent = dateObj.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          });
        }

        if (modalSummary) {
          modalSummary.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <span class="text-sm text-muted">Habits Completed: <strong>${data.completed_count} / ${data.total}</strong></span>
              <span class="badge ${data.percentage === 100 ? 'badge-success' : (data.percentage > 0 ? 'badge-warning' : 'badge-neutral')}">${data.percentage}% Success</span>
            </div>
            <div class="progress-bar-wrap" style="height:6px; margin-bottom:16px;">
              <div class="progress-bar-fill" style="width: ${data.percentage}%; background-color: ${data.percentage === 100 ? '#10B981' : '#4F46E5'};"></div>
            </div>
          `;
        }

        if (modalList) {
          if (!data.habits || data.habits.length === 0) {
            modalList.innerHTML = `<p class="text-sm text-muted" style="text-align:center; padding:20px;">No active habits found for this date.</p>`;
          } else {
            modalList.innerHTML = data.habits.map(h => `
              <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border:1px solid #E2E8F0; border-radius:10px; margin-bottom:8px; background:${h.completed ? '#F8FAFC' : '#FFFFFF'};">
                <div style="display:flex; align-items:center; gap:10px;">
                  <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${h.color || '#4F46E5'};"></span>
                  <span style="font-weight:600; font-size:0.9rem; ${h.completed ? 'text-decoration:none;' : ''}">${h.name}</span>
                  <span class="badge badge-neutral" style="font-size:0.7rem;">${h.category}</span>
                </div>
                <div>
                  ${h.completed 
                    ? `<span class="badge badge-success"><svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg> Completed</span>` 
                    : `<span class="badge badge-neutral">Incomplete</span>`}
                </div>
              </div>
            `).join('');
          }
        }

        if (dayModal) dayModal.classList.add('active');

      } catch (err) {
        console.error('Day details error:', err);
      }
    });
  });
});
