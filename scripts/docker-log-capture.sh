#!/bin/bash
# Docker Log Capture Script for Test Failures
# Captures logs from all containers when Playwright tests fail

set -e

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_DIR="./test-results/logs/$TIMESTAMP"
mkdir -p "$LOG_DIR"

echo "📋 Capturing Docker container logs..."
echo "Timestamp: $TIMESTAMP"
echo "Log directory: $LOG_DIR"

# Capture backend logs (last 500 lines)
echo "Capturing backend logs..."
docker compose -f docker-compose.dev.yml logs --tail=500 backend > "$LOG_DIR/backend.log" 2>&1 || echo "Backend container not running"

# Capture frontend logs
echo "Capturing frontend logs..."
docker compose -f docker-compose.dev.yml logs --tail=500 frontend > "$LOG_DIR/frontend.log" 2>&1 || echo "Frontend container not running"

# Capture database logs
echo "Capturing database logs..."
docker compose -f docker-compose.dev.yml logs --tail=500 supabase > "$LOG_DIR/supabase.log" 2>&1 || echo "Supabase container not running"

# Capture container stats
echo "Capturing container status..."
docker compose -f docker-compose.dev.yml ps > "$LOG_DIR/container-status.txt" 2>&1 || echo "Docker compose not running"

# Save environment info
echo "Capturing environment info..."
{
    echo "=== System Info ==="
    uname -a
    echo ""
    echo "=== Docker Version ==="
    docker --version
    echo ""
    echo "=== Docker Compose Version ==="
    docker compose version
    echo ""
    echo "=== Disk Usage ==="
    df -h
} > "$LOG_DIR/environment.txt" 2>&1

# Save the log path for test automation
echo "$LOG_DIR" > ./test-results/last-log-path.txt

echo "✅ Logs saved to: $LOG_DIR"
echo ""
echo "Log files created:"
ls -lh "$LOG_DIR"

exit 0
