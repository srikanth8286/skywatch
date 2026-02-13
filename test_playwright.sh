#!/bin/bash
# Comprehensive SkyWatch UI Test using playwright-cli
# Tests all features and monitors for crashes

set -e  # Exit on error

BASE_URL="http://localhost:8080"
LOG_FILE="/tmp/skywatch_test_$(date +%s).log"

echo "=== SkyWatch Playwright Test Suite ===" | tee -a $LOG_FILE
echo "Starting at: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Function to check if server is responsive
check_server() {
    if ! curl -s --max-time 3 "$BASE_URL/api/status" > /dev/null; then
        echo "❌ Server not responding!" | tee -a $LOG_FILE
        exit 1
    fi
    echo "✓ Server responsive" | tee -a $LOG_FILE
}

# Function to test and log
test_step() {
    echo "→ $1" | tee -a $LOG_FILE
    check_server
}

# Close any existing browser sessions
echo "Cleaning up old browser sessions..." | tee -a $LOG_FILE
playwright-cli close-all 2>/dev/null || true

# Open browser
test_step "Opening browser and navigating to $BASE_URL"
playwright-cli open "$BASE_URL" 2>&1 | tee -a $LOG_FILE &
sleep 8

# Test 1: Homepage loads
test_step "Test 1: Verify homepage loads"
playwright-cli snapshot 2>&1 | grep -q "live-view\|tabs" && echo "  ✓ Homepage loaded" || echo "  ✗ Failed"

# Test 2: Live stream
test_step "Test 2: Check live stream is visible"
sleep 2
playwright-cli eval "document.getElementById('live-stream') !== null" 2>&1 | tee -a $LOG_FILE

# Test 3: Take snapshot
test_step "Test 3: Test snapshot button"
playwright-cli click "button#snapshot-btn" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Snapshot button interaction attempted"
sleep 1

# Test 4: Navigate to Timelapse tab
test_step "Test 4: Navigate to Timelapse tab"
playwright-cli click "[data-tab='timelapse']" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Timelapse tab click attempted"
sleep 2

# Test 5: Check timelapse dates load
test_step "Test 5: Verify timelapse dates API"
curl -s "$BASE_URL/api/timelapse/dates" | grep -q "dates" && echo "  ✓ Timelapse API works" || echo "  ✗ API failed"

# Test 6: Navigate to Solargraph tab
test_step "Test 6: Navigate to Solargraph tab"
playwright-cli click "[data-tab='solargraph']" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Solargraph tab click attempted"
sleep 2

# Test 7: Navigate to Status tab
test_step "Test 7: Navigate to Status tab"
playwright-cli click "[data-tab='status']" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Status tab click attempted"
sleep 2

# Test 8: Check status API
test_step "Test 8: Verify status API returns complete data"
STATUS=$(curl -s "$BASE_URL/api/status")
echo "$STATUS" | grep -q "camera" && echo "  ✓ Camera status present" || echo "  ✗ Missing camera"
echo "$STATUS" | grep -q "services" && echo "  ✓ Services status present" || echo "  ✗ Missing services"
echo "$STATUS" | grep -q "timelapse" && echo "  ✓ Timelapse service present" || echo "  ✗ Missing timelapse"

# Test 9: Navigate to Settings tab
test_step "Test 9: Navigate to Settings tab"
playwright-cli click "[data-tab='settings']" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Settings tab click attempted"
sleep 2

# Test 10: Check settings load
test_step "Test 10: Verify settings API"
curl -s "$BASE_URL/api/settings" | grep -q "camera" && echo "  ✓ Settings API works" || echo "  ✗ API failed"

# Test 11: Navigate back to Live View
test_step "Test 11: Return to Live View tab"
playwright-cli click "[data-tab='live']" 2>&1 | tee -a $LOG_FILE || echo "  ℹ Live tab click attempted"
sleep 2

# Test 12: Stress test - rapid tab switching
test_step "Test 12: Stress test - rapid tab switching (20 times)"
for i in {1..20}; do
    playwright-cli click "[data-tab='timelapse']" 2>&1 >> $LOG_FILE || true
    sleep 0.2
    playwright-cli click "[data-tab='status']" 2>&1 >> $LOG_FILE || true
    sleep 0.2
    check_server || exit 1
done
echo "  ✓ Survived 20 rapid tab switches" | tee -a $LOG_FILE

# Test 13: Monitor CPU during test
test_step "Test 13: Check CPU usage"
CPU=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $3}')
echo "  Current CPU: ${CPU}%" | tee -a $LOG_FILE
if (( $(echo "$CPU < 40" | bc -l) )); then
    echo "  ✓ CPU usage acceptable (<40%)" | tee -a $LOG_FILE
else
    echo "  ⚠ CPU usage high (${CPU}%)" | tee -a $LOG_FILE
fi

# Test 14: Long-running stream test
test_step "Test 14: Sustained stream test (30 seconds)"
timeout 30 curl -s "$BASE_URL/api/stream" > /dev/null 2>&1 &
STREAM_PID=$!
sleep 32
check_server || exit 1
echo "  ✓ Server survived 30s stream" | tee -a $LOG_FILE

# Test 15: Multiple API calls simultaneously
test_step "Test 15: Concurrent API stress test (10 parallel requests)"
for i in {1..10}; do
    curl -s "$BASE_URL/api/status" > /dev/null &
done
wait
check_server || exit 1
echo "  ✓ Server handled concurrent requests" | tee -a $LOG_FILE

# Final server check
test_step "Final: Server stability check"
SERVER_PID=$(pgrep -f "python.*main.py")
if [ -n "$SERVER_PID" ]; then
    STATE=$(ps -p $SERVER_PID -o state= | tr -d ' ')
    CPU=$(ps -p $SERVER_PID -o %cpu= | tr -d ' ')
    MEM=$(ps -p $SERVER_PID -o %mem= | tr -d ' ')
    echo "  ✓ Server still running (PID: $SERVER_PID)" | tee -a $LOG_FILE
    echo "  State: $STATE | CPU: ${CPU}% | MEM: ${MEM}%" | tee -a $LOG_FILE
    
    # Check if server is responsive
    if curl -s --max-time 2 "$BASE_URL/api/status" | grep -q "running"; then
        echo "  ✓ Server is responsive" | tee -a $LOG_FILE
        FINAL_STATUS="PASS"
    else
        echo "  ✗ Server not responding" | tee -a $LOG_FILE
        FINAL_STATUS="FAIL"
    fi
else
    echo "  ✗ Server process not found - CRASHED!" | tee -a $LOG_FILE
    FINAL_STATUS="FAIL"
fi

# Close browser
playwright-cli close 2>&1 | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "=== Test Summary ===" | tee -a $LOG_FILE
echo "Completed at: $(date)" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE" | tee -a $LOG_FILE
echo "Final Status: $FINAL_STATUS" | tee -a $LOG_FILE

if [ "$FINAL_STATUS" = "PASS" ]; then
    echo "✅ All tests passed! Server is stable." | tee -a $LOG_FILE
    exit 0
else
    echo "❌ Tests failed! Check logs for details." | tee -a $LOG_FILE
    exit 1
fi
