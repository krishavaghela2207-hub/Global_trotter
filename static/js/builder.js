/* ==========================================================================
   GlobeTrotter - Itinerary Builder Interactive Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  // Activity modal pre-fill based on selected activity catalog item
  const activitySelect = document.getElementById('id_builder_activity_select');
  const titleInput = document.getElementById('id_builder_activity_title');
  const costInput = document.getElementById('id_builder_activity_cost');
  const categorySelect = document.getElementById('id_builder_activity_category');
  const durationInput = document.getElementById('id_builder_activity_duration');
  const locationInput = document.getElementById('id_builder_activity_location');

  if (activitySelect) {
    activitySelect.addEventListener('change', function () {
      const selectedOption = activitySelect.options[activitySelect.selectedIndex];
      if (selectedOption && selectedOption.value) {
        const name = selectedOption.getAttribute('data-name');
        const cost = selectedOption.getAttribute('data-cost');
        const category = selectedOption.getAttribute('data-category');
        const duration = selectedOption.getAttribute('data-duration');
        const loc = selectedOption.getAttribute('data-location');

        if (name && titleInput) titleInput.value = name;
        if (cost && costInput) costInput.value = cost;
        if (category && categorySelect) categorySelect.value = category;
        if (duration && durationInput) durationInput.value = Math.round(parseFloat(duration) * 60);
        if (loc && locationInput) locationInput.value = loc;
      }
    });
  }

  // Handle Quick Add Activity button click on specific day cards
  const addActButtons = document.querySelectorAll('.btn-add-activity-to-day');
  addActButtons.forEach(btn => {
    btn.addEventListener('click', function () {
      const dateVal = this.getAttribute('data-date');
      const stopId = this.getAttribute('data-stop-id');

      const dateInput = document.getElementById('id_builder_scheduled_date');
      const stopSelect = document.getElementById('id_builder_stop_select');

      if (dateInput && dateVal) dateInput.value = dateVal;
      if (stopSelect && stopId) stopSelect.value = stopId;
    });
  });

  // Filter activities dynamically inside modal
  const searchInput = document.getElementById('modal_activity_search');
  if (searchInput && activitySelect) {
    searchInput.addEventListener('input', function () {
      const term = this.value.toLowerCase();
      Array.from(activitySelect.options).forEach(opt => {
        if (!opt.value) return;
        const text = opt.text.toLowerCase();
        opt.style.display = text.includes(term) ? '' : 'none';
      });
    });
  }
});
