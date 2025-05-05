// Main JavaScript for the donation platform

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
  // Image preview for donation uploads
  const imageInput = document.getElementById('image');
  const imagePreview = document.getElementById('image-preview');
  
  if (imageInput && imagePreview) {
    imageInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
          imagePreview.src = e.target.result;
          imagePreview.style.display = 'block';
        };
        
        reader.readAsDataURL(this.files[0]);
      }
    });
  }
  
  // Enable Bootstrap tooltips
  const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  
  // Enable Bootstrap popovers
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
  
  // Donation status update confirmation
  const statusForms = document.querySelectorAll('.status-update-form');
  
  if (statusForms) {
    statusForms.forEach(form => {
      form.addEventListener('submit', function(e) {
        if (!confirm('Are you sure you want to update the donation status?')) {
          e.preventDefault();
        }
      });
    });
  }
  
  // Auto-hide flash messages after 5 seconds
  setTimeout(function() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);
});
