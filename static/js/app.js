// Shared progressive enhancement entry point. Complex itinerary ordering stays server-authoritative.
document.querySelectorAll('form').forEach((form) => {
  form.querySelectorAll('input, select, textarea').forEach((field) => {
    if (!field.classList.contains('form-control') && !field.classList.contains('form-select')) {
      field.classList.add(field.tagName === 'SELECT' ? 'form-select' : 'form-control');
    }
  });
});
