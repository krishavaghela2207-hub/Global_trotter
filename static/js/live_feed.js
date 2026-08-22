/* ==========================================================================
   GlobeTrotter Live Community Feed & Interactive Interactions
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  let lastActivityId = 0;
  let isFirstLoad = true;
  const feedContainer = document.getElementById('live-activity-stream');
  const toastContainer = document.getElementById('toast-container');

  // Fetch initial latest activity ID so we only toast for NEW events
  fetch('/api/live-feed/')
    .then(response => response.json())
    .then(data => {
      if (data.max_id) {
        lastActivityId = data.max_id;
      }
      isFirstLoad = false;
    })
    .catch(err => {
      isFirstLoad = false;
    });

  // Live Activity Polling Function
  function pollLiveActivity() {
    if (isFirstLoad) return;

    fetch(`/api/live-feed/?last_id=${lastActivityId}`)
      .then(response => response.json())
      .then(data => {
        if (data.count > 0 && data.activities.length > 0) {
          lastActivityId = data.max_id;

          data.activities.forEach(act => {
            // Prepend to live feed if widget is present on current page
            if (feedContainer) {
              const itemHtml = `
                <div class="live-feed-item" data-activity-id="${act.id}">
                  <div class="live-icon-box">
                    <i class="fas ${act.icon || 'fa-globe-americas'}"></i>
                  </div>
                  <div class="flex-grow-1">
                    <div class="d-flex justify-content-between align-items-center">
                      <span class="fw-bold text-dark fs-7">${act.user}</span>
                      <small class="text-muted fs-8">${act.timestamp}</small>
                    </div>
                    <p class="mb-0 text-secondary fs-7">${act.description}</p>
                    ${act.reference_url ? `<a href="${act.reference_url}" class="text-primary text-decoration-none fs-8 fw-semibold">View &rarr;</a>` : ''}
                  </div>
                </div>
              `;
              feedContainer.insertAdjacentHTML('afterbegin', itemHtml);

              // Limit displayed items to 15
              const currentItems = feedContainer.querySelectorAll('.live-feed-item');
              if (currentItems.length > 15) {
                currentItems[currentItems.length - 1].remove();
              }
            }

            // Show Toast Alert for newly received activity
            showLiveToast(act);
          });
        }
      })
      .catch(err => console.debug('Live feed polling paused', err));
  }

  function showLiveToast(act) {
    if (!toastContainer) return;

    // Limit active toasts to 2 at a time
    const existingToasts = toastContainer.querySelectorAll('.toast');
    if (existingToasts.length >= 2) {
      existingToasts[0].remove();
    }

    const toastId = 'toast-' + Date.now();
    const toastHtml = `
      <div id="${toastId}" class="toast align-items-center text-bg-dark border-0 mb-2 shadow-lg rounded-3" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="d-flex">
          <div class="toast-body d-flex align-items-center gap-2 py-2">
            <span class="badge bg-primary p-2 rounded-circle"><i class="fas ${act.icon || 'fa-bell'}"></i></span>
            <div>
              <div class="fw-bold text-white small">${act.title}</div>
              <div class="text-light text-opacity-75 fs-8">${act.description.substring(0, 55)}...</div>
            </div>
          </div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
      </div>
    `;
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    if (window.bootstrap && toastEl) {
      const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
      toast.show();
    }
  }

  // Poll every 8 seconds
  setInterval(pollLiveActivity, 8000);

  // Global Wishlist AJAX Toggle
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-wishlist-toggle');
    if (!btn) return;
    e.preventDefault();

    const cityId = btn.getAttribute('data-city-id');
    const csrfToken = getCookie('csrftoken');

    fetch(`/api/wishlist/toggle/${cityId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json'
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          if (data.is_wishlisted) {
            btn.classList.add('text-danger', 'active');
            btn.innerHTML = '<i class="fas fa-heart"></i>';
          } else {
            btn.classList.remove('text-danger', 'active');
            btn.innerHTML = '<i class="far fa-heart"></i>';
          }

          // Update header badge if exists
          const badge = document.getElementById('wishlist-badge-count');
          if (badge) {
            badge.innerText = data.total_wishlist;
            badge.style.display = data.total_wishlist > 0 ? 'inline-block' : 'none';
          }
        }
      })
      .catch(err => console.error(err));
  });

  // Global Trip Like AJAX Toggle
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-trip-like');
    if (!btn) return;
    e.preventDefault();

    const tripId = btn.getAttribute('data-trip-id');
    const csrfToken = getCookie('csrftoken');

    fetch(`/trips/${tripId}/like/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json'
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const countSpan = btn.querySelector('.like-count');
          if (countSpan) countSpan.innerText = data.likes_count;

          if (data.liked) {
            btn.classList.add('btn-danger');
            btn.classList.remove('btn-outline-danger');
          } else {
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-outline-danger');
          }
        }
      })
      .catch(err => console.error(err));
  });

  // Helper to read CSRF token
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
});
