/**
 * Notifications management script
 * Handles real-time notifications using periodic AJAX calls
 */

// Global variables
let notificationCheckInterval = null;
const CHECK_INTERVAL = 30000; // 30 seconds

/**
 * Initialize notifications system
 */
function initNotifications() {
    // Only run if the user is logged in
    if (!document.getElementById('notification-dropdown')) {
        return;
    }
    
    // Load initial notifications
    loadNotifications();
    
    // Set up periodic checking
    notificationCheckInterval = setInterval(checkNewNotifications, CHECK_INTERVAL);
    
    // Add event listeners
    setupNotificationEvents();
}

/**
 * Load notifications into the dropdown
 */
function loadNotifications() {
    fetch('/notifications/api/recent/')
        .then(response => response.json())
        .then(data => {
            updateNotificationDropdown(data.notifications, data.unread_count);
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
        });
}

/**
 * Check for new notifications (unread count only)
 */
function checkNewNotifications() {
    fetch('/notifications/api/unread-count/')
        .then(response => response.json())
        .then(data => {
            updateUnreadCount(data.count);
            
            // If we have new notifications, refresh the dropdown content
            const currentCount = parseInt(document.getElementById('notification-badge').textContent) || 0;
            if (data.count > currentCount) {
                loadNotifications();
                // Optionally play a sound or show a toast for new notifications
                showNewNotificationToast();
            }
        })
        .catch(error => {
            console.error('Error checking notifications:', error);
        });
}

/**
 * Update the notification dropdown with notifications
 */
function updateNotificationDropdown(notifications, unreadCount) {
    const dropdownMenu = document.querySelector('.notification-dropdown-items');
    if (!dropdownMenu) return;
    
    // Update unread count
    updateUnreadCount(unreadCount);
    
    // If no notifications
    if (notifications.length === 0) {
        dropdownMenu.innerHTML = `
            <li>
                <div class="dropdown-item text-center py-3">
                    <i class="fas fa-bell-slash fa-lg text-muted"></i>
                    <p class="mb-0 mt-2">No notifications</p>
                </div>
            </li>
        `;
        return;
    }
    
    // Create HTML for notifications
    let html = '';
    
    notifications.forEach(notification => {
        let iconClass = 'fa-bell';
        let iconBg = 'bg-secondary';
        
        // Determine icon based on notification type
        switch (notification.notification_type) {
            case 'JOB':
                iconClass = 'fa-briefcase';
                iconBg = 'bg-primary';
                break;
            case 'DOCUMENT':
                iconClass = 'fa-file-alt';
                iconBg = 'bg-info';
                break;
            case 'PAYMENT':
                iconClass = 'fa-euro-sign';
                iconBg = 'bg-success';
                break;
            case 'MESSAGE':
                iconClass = 'fa-envelope';
                iconBg = 'bg-warning';
                break;
        }
        
        html += `
            <li>
                <a class="dropdown-item notification-item ${notification.read ? '' : 'unread'}" 
                   href="/notifications/${notification.id}/mark-read/">
                    <div class="d-flex align-items-center">
                        <div class="notification-icon me-3">
                            <span class="icon-wrapper ${iconBg} text-white">
                                <i class="fas ${iconClass} fa-sm"></i>
                            </span>
                        </div>
                        <div class="notification-content">
                            <div class="notification-title">${notification.title}</div>
                            <div class="notification-text">${notification.message}</div>
                            <div class="notification-time">${notification.created_at}</div>
                        </div>
                    </div>
                </a>
            </li>
        `;
    });
    
    // Add "View all" link
    html += `
        <li><hr class="dropdown-divider"></li>
        <li>
            <a class="dropdown-item text-center view-all" href="/notifications/">
                View all notifications
            </a>
        </li>
    `;
    
    dropdownMenu.innerHTML = html;
    
    // Re-add event listeners to the new elements
    setupNotificationEvents();
}

/**
 * Update the unread notification count badge
 */
function updateUnreadCount(count) {
    const badge = document.getElementById('notification-badge');
    if (!badge) return;
    
    badge.textContent = count;
    
    if (count > 0) {
        badge.classList.remove('d-none');
    } else {
        badge.classList.add('d-none');
    }
    
    // Update title with unread count
    if (count > 0) {
        document.title = `(${count}) ${document.title.replace(/^\(\d+\)\s/, '')}`;
    } else {
        document.title = document.title.replace(/^\(\d+\)\s/, '');
    }
}

/**
 * Set up event listeners for notification actions
 */
function setupNotificationEvents() {
    // Mark all as read button
    const markAllReadForm = document.querySelector('.mark-all-read-form');
    if (markAllReadForm) {
        markAllReadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: new FormData(this)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the UI
                    updateUnreadCount(0);
                    
                    // Update notification items in the dropdown
                    document.querySelectorAll('.notification-item.unread').forEach(item => {
                        item.classList.remove('unread');
                    });
                    
                    // Remove the mark all as read button
                    this.parentElement.innerHTML = '<span>Notifications</span>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }
    
    // Individual notification items
    document.querySelectorAll('.notification-dropdown-items .notification-item').forEach(item => {
        // Handle AJAX marking as read when clicking a notification
        item.addEventListener('click', function(e) {
            // Only apply AJAX behavior if it's unread
            if (!this.classList.contains('unread')) return;
            
            e.preventDefault();
            
            const url = this.getAttribute('href');
            const notificationItem = this;
            
            fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove unread class
                    notificationItem.classList.remove('unread');
                    
                    // Decrement the unread count
                    const badge = document.getElementById('notification-badge');
                    const currentCount = parseInt(badge.textContent);
                    updateUnreadCount(currentCount - 1);
                    
                    // After a brief delay, navigate to the notification's action URL
                    setTimeout(() => {
                        window.location.href = notificationItem.getAttribute('data-action-url') || url;
                    }, 300);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Fall back to regular navigation
                window.location.href = url;
            });
        });
    });
}

/**
 * Show a toast notification for new notifications
 */
function showNewNotificationToast() {
    // Check if the Bootstrap toast library is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
        const toastEl = document.getElementById('notification-toast');
        if (toastEl) {
            const toast = new bootstrap.Toast(toastEl);
            toast.show();
        } else {
            // Create a toast element if it doesn't exist
            const toastHtml = `
                <div class="toast-container position-fixed bottom-0 end-0 p-3">
                    <div id="notification-toast" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                        <div class="toast-header bg-primary text-white">
                            <i class="fas fa-bell me-2"></i>
                            <strong class="me-auto">New Notification</strong>
                            <small>Just now</small>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                        </div>
                        <div class="toast-body">
                            You have new notifications. Click to view them.
                        </div>
                    </div>
                </div>
            `;
            
            // Append the toast container to the body
            const toastContainer = document.createElement('div');
            toastContainer.innerHTML = toastHtml;
            document.body.appendChild(toastContainer);
            
            // Initialize and show the toast
            const toast = new bootstrap.Toast(document.getElementById('notification-toast'));
            
            // Add click event to navigate to notifications page
            document.getElementById('notification-toast').addEventListener('click', function() {
                window.location.href = '/notifications/';
            });
            
            toast.show();
        }
    }
    
    // Play a notification sound if audio is available
    const notificationSound = document.getElementById('notification-sound');
    if (notificationSound) {
        notificationSound.play().catch(e => {
            // Browser might block autoplay, ignore error
            console.log('Could not play notification sound:', e);
        });
    }
}

// Initialize notifications when the DOM is loaded
document.addEventListener('DOMContentLoaded', initNotifications);