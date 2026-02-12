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
            await loadTimelapseFrames(data.dates[0]);
        }
    } catch (error) {
        console.error('Error loading timelapse dates:', error);
    }
}

document.getElementById('timelapse-date').addEventListener('change', async (e) => {
    await loadTimelapseFrames(e.target.value);
});

async function loadTimelapseFrames(date) {
    try {
        const response = await fetch(`/api/timelapse/frames/${date}`);
        const data = await response.json();
        document.getElementById('timelapse-info').textContent = 
            `Frame count: ${data.count} | Date: ${data.date}`;
    } catch (error) {
        console.error('Error loading timelapse frames:', error);
    }
}

let timelapseStreamActive = false;

document.getElementById('play-timelapse').addEventListener('click', () => {
    const date = document.getElementById('timelapse-date').value;
    const speed = document.getElementById('playback-speed').value;
    
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    const img = document.getElementById('timelapse-player');
    const placeholder = document.getElementById('timelapse-placeholder');
    
    img.src = `/api/timelapse/play/${date}?speed=${speed}&t=${Date.now()}`;
    img.style.display = 'block';
    placeholder.style.display = 'none';
    timelapseStreamActive = true;
});

document.getElementById('stop-timelapse').addEventListener('click', () => {
    const img = document.getElementById('timelapse-player');
    const placeholder = document.getElementById('timelapse-placeholder');
    
    img.src = '';
    img.style.display = 'none';
    placeholder.style.display = 'block';
    timelapseStreamActive = false;
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
        
        // Camera status
        const cameraCard = createStatusCard('Camera', {
            'Status': data.camera.is_connected ? '✅ Connected' : '❌ Disconnected',
            'Frame Count': data.camera.frame_count.toLocaleString(),
            'Last Frame': data.camera.last_frame_time ? new Date(data.camera.last_frame_time).toLocaleTimeString() : 'N/A',
            'Subscribers': data.camera.subscribers
        });
        
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

function createStatusCard(title, data) {
    const stats = Object.entries(data).map(([label, value]) => `
        <div class="stat">
            <span class="stat-label">${label}:</span>
            <span class="stat-value">${value}</span>
        </div>
    `).join('');
    
    return `
        <div class="status-card">
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
