#!/bin/bash
# Automated Test Workflow Script
# Runs Playwright tests → Captures logs on failure → Attempts auto-fix → Re-runs tests

set -e

TEST_SUITE="${1:-all}"
MAX_FIX_ATTEMPTS=2

echo "🧪 Starting automated test workflow..."
echo "Test suite: $TEST_SUITE"
echo "Max auto-fix attempts: $MAX_FIX_ATTEMPTS"
echo ""

# Function to run tests
run_tests() {
    local suite=$1
    echo "▶️  Running tests: $suite"
    
    if [ "$suite" == "all" ]; then
        cd frontend && npm run test:e2e
    else
        cd frontend && npm run test:e2e -- "$suite"
    fi
}

# Function to capture logs
capture_logs() {
    echo "📋 Test failed - capturing Docker logs..."
    bash scripts/docker-log-capture.sh
}

# Function to attempt auto-fix
attempt_autofix() {
    local log_dir=$1
    echo "🔧 Attempting automated error fix..."
    
    if [ -f "frontend/tests/utils/auto-fix.ts" ]; then
        cd frontend && npx ts-node tests/utils/auto-fix-cli.ts --logs "$log_dir"
    else
        echo "⚠️  Auto-fix utility not yet implemented"
        return 1
    fi
}

# Main test loop
attempt=1
test_passed=false

while [ $attempt -le $((MAX_FIX_ATTEMPTS + 1)) ]; do
    echo ""
    echo "====================================="
    echo "Test Attempt $attempt"
    echo "====================================="
    
    if run_tests "$TEST_SUITE"; then
        echo "✅ Tests passed!"
        test_passed=true
        break
    else
        echo "❌ Tests failed on attempt $attempt"
        
        # Capture logs after failure
        capture_logs
        
        # Try auto-fix if we have attempts remaining
        if [ $attempt -lt $((MAX_FIX_ATTEMPTS + 1)) ]; then
            log_dir=$(cat ./test-results/last-log-path.txt)
            if attempt_autofix "$log_dir"; then
                echo "🔄 Auto-fix applied - restarting containers..."
                docker-compose -f docker-compose.dev.yml restart
                sleep 10  # Wait for services to stabilize
                ((attempt++))
            else
                echo "⚠️  Auto-fix failed - manual intervention required"
                break
            fi
        else
            echo "⚠️  Max auto-fix attempts reached"
            break
        fi
    fi
done

echo ""
echo "====================================="
echo "Test Workflow Summary"
echo "====================================="
if [ "$test_passed" = true ]; then
    echo "✅ Status: PASSED"
    echo "Attempts: $attempt"
    exit 0
else
    echo "❌ Status: FAILED"
    echo "Attempts: $attempt"
    echo ""
    echo "Logs available at: $(cat ./test-results/last-log-path.txt 2>/dev/null || echo 'N/A')"
    echo "Please review logs and fix manually"
    exit 1
fi
