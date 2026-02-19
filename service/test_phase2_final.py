"""Tests Phase 2 - Routing intelligent"""
import sys
from main import detect_category, is_continuation, route_message, MODEL_MAPPINGS


def test_category_detection():
    """Test 2.1: Detection de categorie"""
    # Code
    assert detect_category("ecris une fonction python") == "code"
    assert detect_category("def fibonacci(n):") == "code"
    assert detect_category("import pandas") == "code"
    print("[OK] Detection code")
    
    # Reasoning
    assert detect_category("pourquoi le ciel est bleu") == "reasoning"
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
    assert len(MODEL_MAPPINGS["reasoning"]) >= 2
    assert len(MODEL_MAPPINGS["conversation"]) >= 2
    print("[OK] Fallbacks disponibles")
    
    # GLM-5 present
    assert "z-ai/glm-5" in MODEL_MAPPINGS["code"]
    assert "z-ai/glm-5" in MODEL_MAPPINGS["reasoning"]
    print("[OK] GLM-5 dans mappings")


def test_routing():
    """Test routing"""
    # Code -> GLM-5
    messages = [{"role": "user", "content": "def hello():"}]
    model = route_message(messages, "test_session")
    assert model == "z-ai/glm-5"
    print("[OK] Routing code -> GLM-5")
    
    # Continuity
    messages = [{"role": "user", "content": "ok"}]
    model2 = route_message(messages, "test_session")
    assert model == model2
    print("[OK] Continuity OK")


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