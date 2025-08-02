// JavaScript for Telegram Card Counter Bot Dashboard

let updateInterval;
let activityLog = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    startAutoUpdate();
    setupEventListeners();
});

function initializeDashboard() {
    updateStatus();
}

function startAutoUpdate() {
    // Update every 3 seconds
    updateInterval = setInterval(updateStatus, 3000);
}

function setupEventListeners() {
    // Reset button
    document.getElementById('reset-btn').addEventListener('click', resetCounters);
    
    // Start bot button
    document.getElementById('start-bot-btn').addEventListener('click', startBot);
    
    // Style selector
    document.getElementById('style-select').addEventListener('change', changeStyle);
}

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateBotStatus(data.bot_status);
        updateCounters(data.counters);
        updateMessagesCount(data.messages_processed);
        updateStyleSelector(data.current_style);
        updateStylePreview(data.styles[data.current_style]);
        
    } catch (error) {
        console.error('Error updating status:', error);
        showError('Erreur de connexion au serveur');
    }
}

function updateBotStatus(status) {
    const statusBadge = document.getElementById('status-badge');
    const lastActivity = document.getElementById('last-activity');
    const errorDiv = document.getElementById('bot-error');
    const errorMessage = document.getElementById('error-message');
    
    if (status.running) {
        statusBadge.className = 'badge badge-status status-online';
        statusBadge.innerHTML = '<i class="fas fa-circle"></i> En ligne';
    } else {
        statusBadge.className = 'badge badge-status status-offline';
        statusBadge.innerHTML = '<i class="fas fa-circle"></i> Hors ligne';
    }
    
    if (status.last_message) {
        lastActivity.textContent = status.last_message;
        addToActivityLog(status.last_message);
    }
    
    if (status.error) {
        errorDiv.classList.remove('d-none');
        errorMessage.textContent = status.error;
    } else {
        errorDiv.classList.add('d-none');
    }
}

function updateCounters(counters) {
    document.getElementById('counter-hearts').textContent = counters['❤️'] || 0;
    document.getElementById('counter-diamonds').textContent = counters['♦️'] || 0;
    document.getElementById('counter-clubs').textContent = counters['♣️'] || 0;
    document.getElementById('counter-spades').textContent = counters['♠️'] || 0;
}

function updateMessagesCount(count) {
    document.getElementById('messages-count').textContent = count;
}

function updateStyleSelector(currentStyle) {
    document.getElementById('style-select').value = currentStyle;
}

function updateStylePreview(styleText) {
    document.getElementById('style-preview').textContent = styleText;
}

async function resetCounters() {
    if (!confirm('Êtes-vous sûr de vouloir réinitialiser tous les compteurs et l\'historique ?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            addToActivityLog('Compteurs et historique réinitialisés');
            updateStatus(); // Refresh immediately
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error resetting counters:', error);
        showError('Erreur lors de la réinitialisation');
    }
}

async function startBot() {
    try {
        const response = await fetch('/api/start_bot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            addToActivityLog('Bot démarré');
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error starting bot:', error);
        showError('Erreur lors du démarrage du bot');
    }
}

async function changeStyle() {
    const newStyle = parseInt(document.getElementById('style-select').value);
    
    try {
        const response = await fetch('/api/style', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ style: newStyle })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(data.message);
            addToActivityLog(`Style changé vers ${newStyle}`);
            updateStatus(); // Refresh preview
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Error changing style:', error);
        showError('Erreur lors du changement de style');
    }
}

function addToActivityLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
        time: timestamp,
        message: message
    };
    
    activityLog.unshift(logEntry);
    
    // Keep only last 10 entries
    if (activityLog.length > 10) {
        activityLog = activityLog.slice(0, 10);
    }
    
    updateActivityLogDisplay();
}

function updateActivityLogDisplay() {
    const activityLogDiv = document.getElementById('activity-log');
    
    if (activityLog.length === 0) {
        activityLogDiv.innerHTML = '<p class="text-muted">Aucune activité récente</p>';
        return;
    }
    
    const logHtml = activityLog.map(entry => `
        <div class="activity-item">
            <div class="activity-time">${entry.time}</div>
            <div>${entry.message}</div>
        </div>
    `).join('');
    
    activityLogDiv.innerHTML = logHtml;
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'danger');
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});
