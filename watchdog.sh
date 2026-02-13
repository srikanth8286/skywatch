#!/bin/bash
# SkyWatch Watchdog - automatically restarts if server becomes unresponsive

SKYWATCH_DIR="/home/srboga/Documents/Projects/skywatch"
PYTHON_CMD="$SKYWATCH_DIR/.venv/bin/python"
LOG_FILE="/tmp/skywatch.log"
WATCHDOG_LOG="/tmp/skywatch_watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$WATCHDOG_LOG"
}

# Check if server is responding
check_health() {
    response=$(curl -s --max-time 3 http://localhost:8080/api/status 2>&1)
    if [ $? -eq 0 ] && echo "$response" | grep -q "running"; then
        return 0
    else
        return 1
    fi
}

# Start skywatch if not running
start_skywatch() {
    log "Starting SkyWatch..."
    cd "$SKYWATCH_DIR"
    $PYTHON_CMD main.py > "$LOG_FILE" 2>&1 &
    sleep 5
}

# Main watchdog loop
log "Watchdog started"

while true; do
    # Check if process is running
    if ! pgrep -f "python.*main.py" > /dev/null; then
        log "ERROR: SkyWatch process not found. Starting..."
        start_skywatch
    elif ! check_health; then
        log "WARNING: Server not responding. Restarting..."
        pkill -9 -f "python.*main.py"
        sleep 2
        start_skywatch
    fi
    
    # Check every 30 seconds
    sleep 30
done
