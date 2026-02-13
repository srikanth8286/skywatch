// SkyWatch Frontend JavaScript

// Tab switching
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabName = tab.dataset.tab;
        
        // Remove active class from all tabs and contents
        tabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(tc => tc.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        document.getElementById(tabName).classList.add('active');
        
        // Load content when tab is activated
        loadTabContent(tabName);
    });
});

// Load content for specific tab
function loadTabContent(tabName) {
    switch(tabName) {
        case 'timelapse':
            loadTimelapseData();
            break;
        case 'solargraph':
            loadSolargraph();
            break;
        case 'lunar':
            loadLunar();
            break;
        case 'motion':
            loadMotionEvents();
            break;
        case 'status':
            loadStatus();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Snapshot button
document.getElementById('snapshot-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/snapshot');
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `snapshot_${new Date().toISOString()}.jpg`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Error taking snapshot:', error);
        alert('Failed to take snapshot');
    }
});

// Timelapse functionality
async function loadTimelapseData() {
    try {
        const response = await fetch('/api/timelapse/dates');
        const data = await response.json();
        
        const select = document.getElementById('timelapse-date');
        select.innerHTML = data.dates.length > 0
            ? data.dates.map(date => `<option value="${date}">${date}</option>`).join('')
            : '<option value="">No dates available</option>';
        
        if (data.dates.length > 0) {
            await loadTimelapseVideo(data.dates[0]);
        }
    } catch (error) {
        console.error('Error loading timelapse dates:', error);
    }
}

document.getElementById('timelapse-date').addEventListener('change', async (e) => {
    await loadTimelapseVideo(e.target.value);
});

async function loadTimelapseVideo(date) {
    try {
        const response = await fetch(`/api/timelapse/frames/${date}`);
        const data = await response.json();
        
        const video = document.getElementById('timelapse-player');
        const placeholder = document.getElementById('timelapse-placeholder');
        
        if (data.exists) {
            document.getElementById('timelapse-info').textContent = 
                `Playing timelapse for ${data.date}`;
            
            // Set video source and load
            video.querySelector('source').src = `/api/timelapse/video/${date}`;
            video.load();
            video.style.display = 'block';
            placeholder.style.display = 'none';
            
            // Auto-play
            video.play().catch(err => {
                console.log('Auto-play prevented:', err);
            });
        } else {
            document.getElementById('timelapse-info').textContent = 
                data.message || 'No video available for this date.';
            video.style.display = 'none';
            placeholder.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading timelapse video:', error);
    }
}

let timelapseStreamActive = false;

document.getElementById('download-timelapse').addEventListener('click', async () => {
    const date = document.getElementById('timelapse-date').value;
    
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    const statusEl = document.getElementById('download-status');
    const btn = document.getElementById('download-timelapse');
    
    try {
        btn.disabled = true;
        statusEl.style.display = 'block';
        statusEl.textContent = '⏳ Compiling video... This may take a minute...';
        statusEl.style.color = '#667eea';
        
        const response = await fetch(`/api/timelapse/download/${date}?fps=24`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Download failed');
        }
        
        // Download the file
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `skywatch_timelapse_${date}.mp4`;
        a.click();
        URL.revokeObjectURL(url);
        
        statusEl.textContent = '✅ Video downloaded successfully!';
        statusEl.style.color = '#28a745';
        
        setTimeout(() => {
            statusEl.style.display = 'none';
        }, 3000);
    } catch (error) {
        console.error('Error downloading timelapse:', error);
        statusEl.textContent = '❌ ' + error.message;
        statusEl.style.color = '#dc3545';
    } finally {
        btn.disabled = false;
    }
});

// Solargraph functionality
function loadSolargraph() {
    const img = document.getElementById('solargraph-composite');
    const placeholder = document.getElementById('solargraph-placeholder');
    
    img.onload = () => {
        img.style.display = 'block';
        placeholder.style.display = 'none';
    };
    
    img.onerror = () => {
        img.style.display = 'none';
        placeholder.style.display = 'block';
    };
    
    img.src = `/api/solargraph/composite?t=${Date.now()}`;
}

document.getElementById('refresh-solargraph').addEventListener('click', loadSolargraph);

document.getElementById('clear-solargraph').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear the solargraph composite? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/solargraph/reset', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
            loadSolargraph();
        } else {
            alert('Failed to clear composite');
        }
    } catch (error) {
        console.error('Error clearing solargraph:', error);
        alert('Failed to clear composite');
    }
});

// Lunar functionality
function loadLunar() {
    const img = document.getElementById('lunar-composite');
    const placeholder = document.getElementById('lunar-placeholder');
    
    img.onload = () => {
        img.style.display = 'block';
        placeholder.style.display = 'none';
    };
    
    img.onerror = () => {
        img.style.display = 'none';
        placeholder.style.display = 'block';
    };
    
    img.src = `/api/lunar/composite?t=${Date.now()}`;
}

document.getElementById('refresh-lunar').addEventListener('click', loadLunar);

document.getElementById('clear-lunar').addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear the lunar composite? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/lunar/reset', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
            loadLunar();
        } else {
            alert('Failed to clear composite');
        }
    } catch (error) {
        console.error('Error clearing lunar:', error);
        alert('Failed to clear composite');
    }
});

// Motion detection functionality
async function loadMotionEvents() {
    try {
        const response = await fetch('/api/motion/events');
        const data = await response.json();
        
        const container = document.getElementById('motion-events');
        
        if (data.events.length === 0) {
            container.innerHTML = '<p class="placeholder">No motion events detected yet</p>';
            return;
        }
        
        container.innerHTML = data.events.map(event => `
            <div class="motion-event" onclick="viewMotionEvent('${event.path}')">
                <img src="/api/storage/motion/${event.path}/trigger.jpg" alt="Motion Event">
                <div class="details">
                    <strong>${event.timestamp}</strong><br>
                    ${event.frame_count} frames captured
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading motion events:', error);
    }
}

function viewMotionEvent(path) {
    // Open motion event in new window/tab
    window.open(`/api/storage/motion/${path}/trigger.jpg`, '_blank');
}

document.getElementById('refresh-motion').addEventListener('click', loadMotionEvents);

// Status functionality
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        const container = document.getElementById('status-info');
        
        // Camera status with warning if disconnected
        const cameraStatus = data.camera.is_connected ? '✅ Connected' : '⚠️ Disconnected';
        const showWarning = !data.camera.is_connected;
        
        const cameraCard = createStatusCard('Camera', {
            'Status': cameraStatus,
            'Message': data.camera.status_message || 'N/A',
            'Frame Count': data.camera.frame_count.toLocaleString(),
            'Last Frame': data.camera.last_frame_time ? new Date(data.camera.last_frame_time).toLocaleTimeString() : 'N/A',
            'Subscribers': data.camera.subscribers
        }, showWarning);
        
        // Service cards
        const serviceCards = Object.entries(data.services).map(([name, stats]) => {
            const serviceName = name.charAt(0).toUpperCase() + name.slice(1);
            const serviceData = {
                'Status': stats.is_running ? '✅ Running' : '⏹ Stopped',
                'Enabled': stats.enabled ? 'Yes' : 'No'
            };
            
            // Add service-specific stats
            if (stats.capture_count !== undefined) {
                serviceData['Captures'] = stats.capture_count.toLocaleString();
            }
            if (stats.detection_count !== undefined) {
                serviceData['Detections'] = stats.detection_count.toLocaleString();
            }
            if (stats.interval !== undefined) {
                serviceData['Interval'] = `${stats.interval}s`;
            }
            
            return createStatusCard(serviceName, serviceData);
        });
        
        container.innerHTML = cameraCard + serviceCards.join('');
    } catch (error) {
        console.error('Error loading status:', error);
        document.getElementById('status-info').innerHTML = 
            '<p class="placeholder">Failed to load status</p>';
    }
}

function createStatusCard(title, data, highlightWarning = false) {
    const cardClass = highlightWarning ? 'status-card status-warning-card' : 'status-card';
    const stats = Object.entries(data).map(([label, value]) => `
        <div class="stat">
            <span class="stat-label">${label}:</span>
            <span class="stat-value">${value}</span>
        </div>
    `).join('');
    
    return `
        <div class="${cardClass}">
            <h3>${title}</h3>
            ${stats}
        </div>
    `;
}

document.getElementById('refresh-status').addEventListener('click', loadStatus);

// Auto-refresh status when tab is active
setInterval(() => {
    const statusTab = document.getElementById('status');
    if (statusTab.classList.contains('active')) {
        loadStatus();
    }
}, 5000);

// Initial load
loadStatus();

// Settings Management
let currentSettings = {};

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        currentSettings = settings;
        populateSettingsForm(settings);
    } catch (error) {
        console.error('Error loading settings:', error);
        showSettingsMessage('Failed to load settings', 'error');
    }
}

function populateSettingsForm(settings) {
    // Camera settings
    document.getElementById('camera-url').value = settings.camera?.rtsp_url || '';
    document.getElementById('camera-reconnect').value = settings.camera?.reconnect_interval || 5;
    document.getElementById('camera-width').value = settings.camera?.frame_width || 1920;
    document.getElementById('camera-height').value = settings.camera?.frame_height || 1080;
    
    // Storage settings
    document.getElementById('storage-path').value = settings.storage?.base_path || '';
    document.getElementById('storage-retention').value = settings.storage?.retention_days || 30;
    
    // Timelapse settings
    document.getElementById('timelapse-enabled').checked = settings.timelapse?.enabled !== false;
    document.getElementById('timelapse-interval').value = settings.timelapse?.interval || 60;
    document.getElementById('timelapse-quality').value = settings.timelapse?.quality || 90;
    document.getElementById('timelapse-fps').value = settings.timelapse?.video_fps || 24;
    document.getElementById('timelapse-daily').checked = settings.timelapse?.daily_video !== false;
    
    // Motion settings
    document.getElementById('motion-enabled').checked = settings.motion?.enabled !== false;
    document.getElementById('motion-sensitivity').value = settings.motion?.sensitivity || 25;
    document.getElementById('motion-sensitivity-value').textContent = settings.motion?.sensitivity || 25;
    document.getElementById('motion-min-area').value = settings.motion?.min_area || 500;
    document.getElementById('motion-burst-count').value = settings.motion?.burst_count || 10;
    document.getElementById('motion-burst-fps').value = settings.motion?.burst_fps || 10;
    document.getElementById('motion-cooldown').value = settings.motion?.cooldown || 5;
    
    // Solargraph settings
    document.getElementById('solargraph-enabled').checked = settings.solargraph?.enabled !== false;
    document.getElementById('solargraph-interval').value = settings.solargraph?.detection_interval || 30;
    document.getElementById('solargraph-latitude').value = settings.solargraph?.latitude || 0;
    document.getElementById('solargraph-longitude').value = settings.solargraph?.longitude || 0;
    
    // Lunar settings
    document.getElementById('lunar-enabled').checked = settings.lunar?.enabled !== false;
    document.getElementById('lunar-interval').value = settings.lunar?.detection_interval || 60;
}

function getSettingsFromForm() {
    const formData = new FormData(document.getElementById('settings-form'));
    const settings = {
        camera: {
            rtsp_url: document.getElementById('camera-url').value,
            reconnect_interval: parseInt(document.getElementById('camera-reconnect').value),
            frame_width: parseInt(document.getElementById('camera-width').value),
            frame_height: parseInt(document.getElementById('camera-height').value)
        },
        storage: {
            base_path: document.getElementById('storage-path').value,
            nas_enabled: currentSettings.storage?.nas_enabled || false,
            nas_path: currentSettings.storage?.nas_path || "",
            retention_days: parseInt(document.getElementById('storage-retention').value)
        },
        timelapse: {
            enabled: document.getElementById('timelapse-enabled').checked,
            interval: parseInt(document.getElementById('timelapse-interval').value),
            quality: parseInt(document.getElementById('timelapse-quality').value),
            daily_video: document.getElementById('timelapse-daily').checked,
            video_fps: parseInt(document.getElementById('timelapse-fps').value)
        },
        solargraph: {
            enabled: document.getElementById('solargraph-enabled').checked,
            detection_interval: parseInt(document.getElementById('solargraph-interval').value),
            brightness_threshold: currentSettings.solargraph?.brightness_threshold || 200,
            min_radius: currentSettings.solargraph?.min_radius || 10,
            max_radius: currentSettings.solargraph?.max_radius || 100,
            daytime_only: currentSettings.solargraph?.daytime_only !== false,
            latitude: parseFloat(document.getElementById('solargraph-latitude').value),
            longitude: parseFloat(document.getElementById('solargraph-longitude').value)
        },
        lunar: {
            enabled: document.getElementById('lunar-enabled').checked,
            detection_interval: parseInt(document.getElementById('lunar-interval').value),
            brightness_threshold: currentSettings.lunar?.brightness_threshold || 150,
            min_radius: currentSettings.lunar?.min_radius || 15,
            max_radius: currentSettings.lunar?.max_radius || 150,
            nighttime_only: currentSettings.lunar?.nighttime_only !== false
        },
        motion: {
            enabled: document.getElementById('motion-enabled').checked,
            sensitivity: parseInt(document.getElementById('motion-sensitivity').value),
            min_area: parseInt(document.getElementById('motion-min-area').value),
            burst_count: parseInt(document.getElementById('motion-burst-count').value),
            burst_fps: parseInt(document.getElementById('motion-burst-fps').value),
            cooldown: parseInt(document.getElementById('motion-cooldown').value)
        },
        server: currentSettings.server || {
            host: "0.0.0.0",
            port: 8080,
            cors_origins: ["*"]
        },
        advanced: currentSettings.advanced || {
            max_frame_queue: 30,
            jpeg_quality_live: 85,
            log_level: "INFO"
        }
    };
    
    return settings;
}

async function saveSettings() {
    try {
        const settings = getSettingsFromForm();
        const response = await fetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSettingsMessage('✅ ' + result.message, 'success');
            currentSettings = settings;
        } else {
            showSettingsMessage('❌ ' + result.detail, 'error');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        showSettingsMessage('❌ Failed to save settings', 'error');
    }
}

function showSettingsMessage(message, type) {
    const messageDiv = document.getElementById('settings-message');
    messageDiv.textContent = message;
    messageDiv.className = 'settings-message ' + type;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Settings event listeners
document.getElementById('save-settings').addEventListener('click', saveSettings);
document.getElementById('reset-settings').addEventListener('click', () => {
    populateSettingsForm(currentSettings);
    showSettingsMessage('Settings reset to current values', 'info');
});

// Motion sensitivity slider
document.getElementById('motion-sensitivity').addEventListener('input', (e) => {
    document.getElementById('motion-sensitivity-value').textContent = e.target.value;
});