"""Tests Phase 2 - Routing intelligent (sans pytest)"""
import sys
from main import detect_category, is_continuation, route_message, MODEL_MAPPINGS


def test_category_detection():
    """Test 2.1: Détection de catégorie"""
    # Code
    assert detect_category("écris une fonction python") == "code"
    assert detect_category("def fibonacci(n):") == "code"
    assert detect_category("import pandas") == "code"
    print("✅ Détéction code: OK")
    
    # Reasoning
    assert detect_category("pourquoi le ciel est bleu") == "reasoning"
    assert detect_category("explique comment") == "reasoning"
    print("✅ Détection reasoning: OK")
    
    # Conversation
    assert detect_category("bonjour") == "conversation"
    assert detect_category("merci") == "conversation"
    print("✅ Détection conversation: OK")


def test_continuation():
    """Test 2.2: Détection de continuité"""
    assert is_continuation("ok") == True
    assert is_continuation("yes") == True
    assert is_continuation("merci") == True
    assert is_continuation("écris une fonction complète") == False
    print("✅ Détection continuation: OK")


def test_model_mappings():
    """Test 2.3 & 2.4: Mappings et fallbacks"""
    assert "code" in MODEL_MAPPINGS
    assert "reasoning" in MODEL_MAPPINGS
    assert "conversation" in MODEL_MAPPINGS
    print("✅ Catégories définies: OK")
    
    # Fallbacks exist
    assert len(MODEL_MAPPINGS["code"]) >= 2
    assert len(MODEL_MAPPINGS["reasoning"]) >= 2
    assert len(MODEL_MAPPINGS["conversation"]) >= 2
    print("✅ Fallbacks disponibles: OK")
    
    # GLM-5 présent
    assert "z-ai/glm-5" in MODEL_MAPPINGS["code"]
    assert "z-ai/glm-5" in MODEL_MAPPINGS["reasoning"]
    print("✅ GLM-5 dans mappings: OK")


def test_routing():
    """Test routing"""
    # Code → GLM-5
    messages = [{"role": "user", "content": "def hello():"}]
    model = route_message(messages, "test_session")
    assert model == "z-ai/glm-5"  # Premier modèle code
    print("✅ Routing code → GLM-5: OK")
    
    # Continuity
    messages = [{"role": "user", "content": "ok"}]
    model2 = route_message(messages, "test_session")
    assert model == model2  # Même modèle
    print("✅ Continuité OK")


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
        print("✅ TOUS LES TESTS PASSENT!")
        print("Phase 2 complète à 100%")
        sys.exit(0)
    except AssertionError as e:
        print(f"❌ ÉCHEC: {e}")
        sys.exit(1)
