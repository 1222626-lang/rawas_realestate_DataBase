// ============================================
// Rawas Real Estate System - Main JavaScript
// ============================================

// Document ready function
$(document).ready(function() {
    console.log('Rawas Real Estate System Loaded');
    
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts after 5 seconds
    $('.alert').not('.alert-permanent').delay(5000).fadeOut(300);
    
    // Confirm before delete actions
    $('a[data-confirm], button[data-confirm]').on('click', function(e) {
        var message = $(this).data('confirm') || 'Are you sure?';
        if (!confirm(message)) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });
    
    // Form validation helper
    $('form.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Phone number auto-formatting
    $('input[type="tel"]').on('input', function() {
        var value = $(this).val().replace(/\D/g, '');
        if (value.length > 3 && value.length <= 6) {
            value = value.replace(/(\d{3})(\d+)/, '$1-$2');
        } else if (value.length > 6) {
            value = value.replace(/(\d{3})(\d{3})(\d+)/, '$1-$2-$3');
        }
        $(this).val(value);
    });
    
    // Currency formatting
    $('.currency-input').on('blur', function() {
        var value = $(this).val();
        if (value) {
            var number = parseFloat(value.replace(/[^\d.]/g, ''));
            if (!isNaN(number)) {
                $(this).val(number.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }));
            }
        }
    });
    
    // Toggle password visibility
    $('.toggle-password').on('click', function() {
        var input = $(this).closest('.input-group').find('input');
        var icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('bi-eye').addClass('bi-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('bi-eye-slash').addClass('bi-eye');
        }
    });
    
    // AJAX setup for CSRF token
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
});

// Helper function to get cookie value
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Export data to Excel function
function exportToExcel(tableId, filename) {
    var table = document.getElementById(tableId);
    var html = table.outerHTML;
    var url = 'data:application/vnd.ms-excel,' + escape(html);
    
    var link = document.createElement('a');
    link.href = url;
    link.download = filename + '.xls';
    link.click();
}

// Print element function
function printElement(elementId) {
    var printContents = document.getElementById(elementId).innerHTML;
    var originalContents = document.body.innerHTML;
    
    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
    location.reload();
}

// Format date
function formatDate(dateString) {
    var date = new Date(dateString);
    var options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
    return date.toLocaleDateString('en-US', options);
}

// Show loading spinner
function showLoading() {
    $('#loading-spinner').fadeIn();
}

// Hide loading spinner
function hideLoading() {
    $('#loading-spinner').fadeOut();
}

// Show toast notification
function showToast(message, type = 'success') {
    var toast = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    $('#toast-container').append(toast);
    var toastElement = new bootstrap.Toast($('#toast-container .toast').last()[0]);
    toastElement.show();
}

// Initialize when document is ready
$(function() {
    // Add loading spinner to body
    $('body').append(`
        <div id="loading-spinner" style="display: none;">
            <div class="spinner-overlay">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        </div>
        
        <div id="toast-container" class="toast-container position-fixed top-0 end-0 p-3"></div>
    `);
    
    // Add spinner styles
    $('head').append(`
        <style>
            #loading-spinner .spinner-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
        </style>
    `);
});