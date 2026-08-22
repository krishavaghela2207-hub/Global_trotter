/* ==========================================================================
   GlobeTrotter - Chart.js Visualizations for Budget & Analytics
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  // 1. Trip Budget Donut Chart
  const budgetDonutEl = document.getElementById('tripBudgetDonutChart') || document.getElementById('tripBudgetChart');
  if (budgetDonutEl && window.categoryData) {
    const labels = Object.keys(window.categoryData);
    const dataValues = Object.values(window.categoryData);
    const currency = window.currencySymbol || '₹';

    new Chart(budgetDonutEl, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: dataValues,
          backgroundColor: [
            '#2563eb', // Accommodation (Blue)
            '#06b6d4', // Transport (Cyan)
            '#10b981', // Activities (Green)
            '#f59e0b', // Meals (Amber)
            '#ec4899', // Shopping (Pink)
            '#8b5cf6', // Misc (Purple)
          ],
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
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
              font: { family: 'Plus Jakarta Sans', size: 12, weight: '600' },
              padding: 15
            }
          },
          tooltip: {
            callbacks: {
              label: function (context) {
                const value = context.raw || 0;
                return ` ${context.label}: ${currency}${Number(value).toLocaleString()}`;
              }
            }
          }
        },
        cutout: '70%'
      }
    });
  }

  // 2. Admin Dashboard Charts
  const adminDestinationsEl = document.getElementById('adminDestinationsChart');
  if (adminDestinationsEl && window.topCitiesLabels && window.topCitiesData) {
    new Chart(adminDestinationsEl, {
      type: 'bar',
      data: {
        labels: window.topCitiesLabels,
        datasets: [{
          label: 'Trips Planned',
          data: window.topCitiesData,
          backgroundColor: '#2563eb',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  const adminStatusEl = document.getElementById('adminStatusChart');
  if (adminStatusEl && window.statusLabels && window.statusData) {
    new Chart(adminStatusEl, {
      type: 'doughnut',
      data: {
        labels: window.statusLabels,
        datasets: [{
          data: window.statusData,
          backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#64748b', '#94a3b8']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  const adminStyleEl = document.getElementById('adminStyleChart');
  if (adminStyleEl && window.styleLabels && window.styleData) {
    new Chart(adminStyleEl, {
      type: 'polarArea',
      data: {
        labels: window.styleLabels,
        datasets: [{
          data: window.styleData,
          backgroundColor: [
            'rgba(37, 99, 235, 0.7)',
            'rgba(16, 185, 129, 0.7)',
            'rgba(245, 158, 11, 0.7)',
            'rgba(244, 63, 94, 0.7)',
            'rgba(139, 92, 246, 0.7)',
            'rgba(6, 182, 212, 0.7)',
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }
});
