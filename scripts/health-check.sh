#!/bin/bash
# LLM Router Health Check
# Run every 5 minutes via cron

ROUTER_URL="${ROUTER_URL:-http://localhost:3456}"
ROUTER_DIR="${ROUTER_DIR:-$HOME/llm-router/service}"
LOG_FILE="${ROUTER_DIR}/health.log"

check_health() {
    curl -s -f "$ROUTER_URL/health" > /dev/null 2>&1
    return $?
}

start_router() {
    echo "$(date): Router down, starting..." >> "$LOG_FILE"
    cd "$ROUTER_DIR"
    nohup uvicorn main:app --host 0.0.0.0 --port 3456 >> "$LOG_FILE" 2>&1 &
    sleep 3
    if check_health; then
        echo "$(date): Router restarted successfully" >> "$LOG_FILE"
    else
        echo "$(date): Failed to restart router" >> "$LOG_FILE"
    fi
}

if ! check_health; then
    start_router
fi
