# Test script for LLM Router Service
# Run this to validate Phase 1 implementation

echo "=== LLM Router Service - Phase 1 Validation ==="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example to .env and add your API key."
    exit 1
fi

# Check if OPENROUTER_API_KEY is set
source .env
if [ -z "$OPENROUTER_API_KEY" ] || [ "$OPENROUTER_API_KEY" = "your_openrouter_api_key_here" ]; then
    echo "❌ OPENROUTER_API_KEY not set in .env"
    exit 1
fi

echo "✅ Configuration found"
echo ""

# Start the server in background
echo "Starting server..."
cd "$(dirname "$0")"
uvicorn main:app --host 0.0.0.0 --port 3456 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test 1: Health check
echo ""
echo "=== Test 1: Health Check ==="
HEALTH_RESPONSE=$(curl -s http://localhost:3456/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed"
    echo "   Response: $HEALTH_RESPONSE"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test 2: Models endpoint
echo ""
echo "=== Test 2: Models Endpoint ==="
MODELS_RESPONSE=$(curl -s http://localhost:3456/models)
if echo "$MODELS_RESPONSE" | grep -q "router"; then
    echo "✅ Models endpoint passed"
    echo "   Response: $MODELS_RESPONSE"
else
    echo "❌ Models endpoint failed"
    echo "   Response: $MODELS_RESPONSE"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Test 3: Chat completions (basic)
echo ""
echo "=== Test 3: Chat Completions ==="
CHAT_RESPONSE=$(curl -s -X POST http://localhost:3456/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "router",
        "messages": [{"role": "user", "content": "Say hello in one word"}],
        "max_tokens": 10
    }')

if echo "$CHAT_RESPONSE" | grep -q "choices"; then
    echo "✅ Chat completions passed"
    echo "   Response received (truncated): ${CHAT_RESPONSE:0:200}..."
else
    echo "❌ Chat completions failed"
    echo "   Response: $CHAT_RESPONSE"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Cleanup
kill $SERVER_PID 2>/dev/null

echo ""
echo "=== All Phase 1 Tests Passed! ✅ ==="
echo ""
echo "To run the service permanently:"
echo "  uvicorn main:app --host 0.0.0.0 --port 3456"
echo ""
echo "To configure OpenClaw, see integration.md"