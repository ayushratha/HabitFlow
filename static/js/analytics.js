/**
 * HabitFlow — Analytics Charts & Filtering
 */

document.addEventListener('DOMContentLoaded', () => {
  let trendChart = null;
  const trendCanvas = document.getElementById('analyticsTrendChart');
  const categoryCanvas = document.getElementById('categoryDoughnutChart');

  // 1. Initial Load of Trend Chart (30 Days default)
  if (trendCanvas && window.Chart) {
    loadTrendData(30);
  }

  // 2. Range Selector Buttons (7d, 30d, 90d)
  const rangeBtns = document.querySelectorAll('.range-btn');
  rangeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      rangeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const days = parseInt(btn.getAttribute('data-days'), 10) || 30;
      loadTrendData(days);
    });
  });

  async function loadTrendData(days) {
    try {
      const res = await fetch(`/app/analytics/api/chart-data?days=${days}`);
      const data = await res.json();

      if (trendChart) {
        trendChart.destroy();
      }

      const ctx = trendCanvas.getContext('2d');
      // Create subtle gradient for area chart
      const gradient = ctx.createLinearGradient(0, 0, 0, 300);
      gradient.addColorStop(0, 'rgba(79, 70, 229, 0.25)');
      gradient.addColorStop(1, 'rgba(79, 70, 229, 0.0)');

      trendChart = new Chart(trendCanvas, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [{
            label: 'Completion Rate (%)',
            data: data.completion_rates,
            borderColor: '#4F46E5',
            backgroundColor: gradient,
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointBackgroundColor: '#FFFFFF',
            pointBorderColor: '#4F46E5',
            pointBorderWidth: 2,
            pointRadius: days <= 14 ? 4 : 2,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0F172A',
              padding: 12,
              titleFont: { size: 13, weight: '600' },
              callbacks: {
                label: (ctx) => `Success Rate: ${ctx.raw}%`
              }
            }
          },
          scales: {
            y: {
              min: 0,
              max: 100,
              ticks: {
                stepSize: 25,
                callback: (v) => `${v}%`,
                color: '#94A3B8'
              },
              grid: { color: '#F1F5F9' }
            },
            x: {
              ticks: {
                color: '#64748B',
                maxTicksLimit: days > 30 ? 12 : 10
              },
              grid: { display: false }
            }
          }
        }
      });
    } catch (err) {
      console.error('Failed to load chart data:', err);
    }
  }

  // 3. Category Doughnut Chart
  if (categoryCanvas && window.Chart) {
    const rawCategories = categoryCanvas.getAttribute('data-categories');
    const rawCounts = categoryCanvas.getAttribute('data-counts');

    const cats = rawCategories ? JSON.parse(rawCategories) : [];
    const counts = rawCounts ? JSON.parse(rawCounts) : [];

    const palette = ['#4F46E5', '#3B82F6', '#8B5CF6', '#10B981', '#06B6D4', '#F59E0B', '#EC4899'];

    new Chart(categoryCanvas, {
      type: 'doughnut',
      data: {
        labels: cats.length > 0 ? cats : ['No Data'],
        datasets: [{
          data: counts.length > 0 ? counts : [1],
          backgroundColor: cats.length > 0 ? palette.slice(0, cats.length) : ['#E2E8F0'],
          borderWidth: 2,
          borderColor: '#FFFFFF'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              padding: 14,
              color: '#334155',
              font: { size: 12 }
            }
          }
        },
        cutout: '72%'
      }
    });
  }
});
