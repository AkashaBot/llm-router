#!/usr/bin/env python3
"""Test script for Phase 2 routing intelligence"""
import httpx
import sys

def test_route(category, message, user_id, expected_category_hint=None):
    """Test a single routing scenario"""
    payload = {
        "model": "router",
        "messages": [{"role": "user", "content": message}],
        "user": user_id,
        "max_tokens": 10  # Just test routing, don't waste tokens
    }
    
    try:
        resp = httpx.post("http://localhost:3456/v1/chat/completions", 
                         json=payload, timeout=30)
        data = resp.json()
        model = data.get("model", "ERROR")
        return model
    except Exception as e:
        return f"ERROR: {e}"

# Test 1: Code
code_model = test_route("code", "Write a Python function to sort a list", "test1")
print(f"1. CODE -> {code_model}")

# Test 2: Reasoning
reasoning_model = test_route("reasoning", "Why is the sky blue? Explain the physics", "test2")
print(f"2. REASONING -> {reasoning_model}")

# Test 3: Conversation  
conv_model = test_route("conversation", "Hello, how are you today?", "test3")
print(f"3. CONVERSATION → {conv_model}")

# Test 4: Continuation - should keep same model as previous
continuations = ["ok", "yes", "thanks", "please"]
for cont in continuations:
    model = test_route("continuation", cont, "test2")  # Same user as reasoning
    print(f"4. CONTINUATION ('{cont}') → {model}")

print("\n✅ Phase 2 tests complete")
