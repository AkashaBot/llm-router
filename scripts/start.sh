#!/bin/bash
# LLM Router Start Script

ROUTER_DIR="${ROUTER_DIR:-$(dirname "$0")/../service}"
cd "$ROUTER_DIR"

# Load environment
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start
exec uvicorn main:app --host 0.0.0.0 --port 3456
