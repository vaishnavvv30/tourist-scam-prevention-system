/* ScamGuard AI - Main JavaScript */

// CSRF Token helper
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

const csrftoken = getCookie('csrftoken');

// Vote on scam report
function voteReport(reportId, voteType) {
    fetch(`/scams/report/${reportId}/vote/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken,
        },
        body: `vote_type=${voteType}`
    })
    .then(res => res.json())
    .then(data => {
        if (data.upvotes !== undefined) {
            const upEl = document.getElementById(`upvotes-${reportId}`);
            const downEl = document.getElementById(`downvotes-${reportId}`);
            if (upEl) upEl.textContent = data.upvotes;
            if (downEl) downEl.textContent = data.downvotes;
        }
    })
    .catch(err => console.error('Vote error:', err));
}

// Mark alert as read
function markAlertRead(alertId) {
    fetch(`/alerts/${alertId}/read/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
    })
    .then(res => res.json())
    .then(data => {
        const el = document.getElementById(`alert-${alertId}`);
        if (el) el.classList.add('opacity-50');
        const badge = document.getElementById('alert-badge');
        if (badge) {
            let count = parseInt(badge.textContent) - 1;
            if (count <= 0) badge.style.display = 'none';
            else badge.textContent = count;
        }
    });
}

// AI Chat
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send');

function addChatMessage(content, type) {
    if (!chatMessages) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${type}`;
    bubble.innerHTML = content.replace(/\n/g, '<br>');
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendChatMessage() {
    if (!chatInput) return;
    const message = chatInput.value.trim();
    if (!message) return;

    addChatMessage(message, 'user');
    chatInput.value = '';

    // Loading indicator
    const loadingId = 'loading-' + Date.now();
    const loadingEl = document.createElement('div');
    loadingEl.id = loadingId;
    loadingEl.className = 'chat-bubble ai';
    loadingEl.innerHTML = '<div class="spinner-glow" style="width:20px;height:20px;border-width:2px;"></div> Analyzing...';
    chatMessages.appendChild(loadingEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    fetch('/ai/api/chat/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        const loading = document.getElementById(loadingId);
        if (loading) loading.remove();
        addChatMessage(data.response || 'No response received.', 'ai');
        if (data.suggestions && data.suggestions.length > 0) {
            const suggestionsHtml = data.suggestions.map(s =>
                `<button class="btn btn-sm btn-glass mt-1 me-1" onclick="document.getElementById('chat-input').value='${s}';sendChatMessage();">${s}</button>`
            ).join('');
            addChatMessage(suggestionsHtml, 'ai');
        }
    })
    .catch(err => {
        const loading = document.getElementById(loadingId);
        if (loading) loading.remove();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
    });
}

if (chatSendBtn) {
    chatSendBtn.addEventListener('click', sendChatMessage);
}

if (chatInput) {
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert-auto-dismiss');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 4000);
    });

    // Animate stat values
    document.querySelectorAll('.stat-value[data-target]').forEach(el => {
        const target = parseFloat(el.dataset.target);
        let current = 0;
        const increment = target / 40;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = Number.isInteger(target) ? Math.round(current) : current.toFixed(1);
        }, 30);
    });

    // Animate risk meter fills
    document.querySelectorAll('.risk-meter-fill[data-width]').forEach(el => {
        setTimeout(() => {
            el.style.width = el.dataset.width + '%';
        }, 300);
    });
});

// Initialize Leaflet map
function initScamMap(elementId, reports, locations) {
    if (!document.getElementById(elementId)) return;

    const map = L.map(elementId).setView([20.5937, 78.9629], 5);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19
    }).addTo(map);

    const severityColors = {
        'low': '#10b981',
        'medium': '#f59e0b',
        'high': '#ef4444',
        'critical': '#a855f7'
    };

    if (reports && reports.length > 0) {
        reports.forEach(report => {
            if (report.latitude && report.longitude && report.latitude !== 0) {
                const color = severityColors[report.severity] || '#14b8a6';
                const marker = L.circleMarker([report.latitude, report.longitude], {
                    radius: 8,
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 0.8,
                    fillOpacity: 0.5
                }).addTo(map);

                marker.bindPopup(`
                    <div style="color:#333;min-width:200px;">
                        <strong>${report.title}</strong><br>
                        <small>Category: ${report.category}</small><br>
                        <small>Severity: ${report.severity}</small><br>
                        ${report.scam_probability ? `<small>Scam Prob: ${report.scam_probability}%</small>` : ''}
                        <br><a href="/scams/report/${report.id}/" style="color:#14b8a6;">View Details →</a>
                    </div>
                `);
            }
        });
    }

    if (locations && locations.length > 0) {
        locations.forEach(loc => {
            if (loc.latitude && loc.longitude && loc.latitude !== 0) {
                L.circleMarker([loc.latitude, loc.longitude], {
                    radius: 12 + Math.min(loc.total_reports * 2, 20),
                    fillColor: '#ef4444',
                    color: '#ef4444',
                    weight: 1,
                    opacity: 0.3,
                    fillOpacity: 0.15
                }).addTo(map);
            }
        });
    }

    return map;
}


