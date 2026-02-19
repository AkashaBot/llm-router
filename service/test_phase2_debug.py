"""Tests Phase 2 - Routing intelligent"""
import sys
from main import detect_category, is_continuation, route_message, MODEL_MAPPINGS, current_model_per_session


def test_category_detection():
    """Test 2.1: Detection de categorie"""
    # Code
    result = detect_category("ecris une fonction python")
    print(f"  'ecris une fonction python' -> {result}")
    assert result == "code", f"Expected 'code', got '{result}'"
    
    result = detect_category("def fibonacci(n):")
    print(f"  'def fibonacci(n):' -> {result}")
    assert result == "code"
    print("[OK] Detection code")
    
    # Reasoning
    result = detect_category("pourquoi le ciel est bleu")
    print(f"  'pourquoi...' -> {result}")
    assert detect_category("explique comment") == "reasoning"
    print("[OK] Detection reasoning")
    
    # Conversation
    assert detect_category("bonjour") == "conversation"
    assert detect_category("merci") == "conversation"
    print("[OK] Detection conversation")


def test_continuation():
    """Test 2.2: Detection de continuite"""
    assert is_continuation("ok") == True
    assert is_continuation("yes") == True
    assert is_continuation("merci") == True
    assert is_continuation("ecris une fonction complete") == False
    print("[OK] Detection continuation")


def test_model_mappings():
    """Test 2.3 et 2.4: Mappings et fallbacks"""
    assert "code" in MODEL_MAPPINGS
    assert "reasoning" in MODEL_MAPPINGS
    assert "conversation" in MODEL_MAPPINGS
    print("[OK] Categories definies")
    
    # Fallbacks exist
    assert len(MODEL_MAPPINGS["code"]) >= 2
    print(f"  Code models: {MODEL_MAPPINGS['code']}")
    print("[OK] Fallbacks disponibles")
    
    # GLM-5 present
    assert "z-ai/glm-5" in MODEL_MAPPINGS["code"]
    print("[OK] GLM-5 dans mappings")


def test_routing():
    """Test routing"""
    # Clear session state first
    current_model_per_session.clear()
    
    # Code -> should get first model in code list
    messages = [{"role": "user", "content": "def hello():"}]
    model = route_message(messages, "test_session")
    print(f"  Code message routed to: {model}")
    expected_model = MODEL_MAPPINGS["code"][0]
    assert model == expected_model, f"Expected '{expected_model}', got '{model}'"
    print(f"[OK] Routing code -> {model}")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTS PHASE 2 - LLM ROUTER")
    print("=" * 50)
    
    try:
        test_category_detection()
        test_continuation()
        test_model_mappings()
        test_routing()
        print("=" * 50)
        print("[OK] TOUS LES TESTS PASSENT!")
        print("Phase 2 complete a 100%")
        sys.exit(0)
    except AssertionError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)