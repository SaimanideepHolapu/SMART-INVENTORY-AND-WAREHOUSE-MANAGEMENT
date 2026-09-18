// Main UI behaviors and notifications drawer
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash alerts after 4 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {}
        }, 4000);
    });

    // Notification Drawer Toggle
    const notifBtn = document.getElementById('notification-toggle-btn');
    const notifDrawer = document.getElementById('notifications-drawer');
    const closeDrawerBtn = document.getElementById('close-drawer-btn');

    if (notifBtn && notifDrawer) {
        notifBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notifDrawer.classList.toggle('open');
            loadNotifications();
        });
    }

    if (closeDrawerBtn && notifDrawer) {
        closeDrawerBtn.addEventListener('click', function() {
            notifDrawer.classList.remove('open');
        });
    }

    // Close drawer when clicking outside
    document.addEventListener('click', function(e) {
        if (notifDrawer && notifDrawer.classList.contains('open')) {
            if (!notifDrawer.contains(e.target) && notifBtn && !notifBtn.contains(e.target)) {
                notifDrawer.classList.remove('open');
            }
        }
    });

    // Global search in navbar
    const navSearch = document.getElementById('global-search-input');
    if (navSearch) {
        navSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = encodeURIComponent(navSearch.value.trim());
                if (query) {
                    window.location.href = `/products?search=${query}`;
                }
            }
        });
    }
});

// Fetch notifications dynamically
function loadNotifications() {
    const listEl = document.getElementById('notification-list');
    if (!listEl) return;

    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.count === 0) {
                listEl.innerHTML = `
                    <div class="text-center py-4 text-muted">
                        <i class="fas fa-check-circle text-success mb-2" style="font-size: 2rem;"></i>
                        <p class="mb-0 small">All inventory levels are healthy!</p>
                    </div>
                `;
                return;
            }

            let html = '';
            data.alerts.forEach(item => {
                const cls = item.is_critical ? 'critical' : 'warning';
                const badge = item.is_critical ? '<span class="badge bg-danger">OUT OF STOCK</span>' : '<span class="badge bg-warning text-dark">LOW STOCK</span>';
                html += `
                    <div class="alert-item ${cls}">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <strong class="small text-truncate" style="max-width: 180px;">${item.name}</strong>
                            ${badge}
                        </div>
                        <div class="d-flex justify-content-between align-items-center small text-muted">
                            <code>${item.sku}</code>
                            <span>Stock: <strong>${item.stock}</strong> / Min: ${item.min}</span>
                        </div>
                        <div class="mt-2 text-end">
                            <a href="/inventory/stock-in?product_id=${item.id}" class="btn btn-xs btn-outline-primary py-0 px-2" style="font-size: 0.75rem;">
                                <i class="fas fa-plus"></i> Restock
                            </a>
                        </div>
                    </div>
                `;
            });
            listEl.innerHTML = html;
        })
        .catch(err => {
            console.error('Failed to load notifications:', err);
        });
}
