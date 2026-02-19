"""Tests Phase 2 - Routing intelligent avec fallbacks"""
import pytest
from main import detect_category, is_continuation, route_message, MODEL_MAPPINGS, DEFAULT_MODEL


class TestCategoryDetection:
    """Test 2.1: Détection de catégorie"""
    
    def test_detect_code_python(self):
        """Détection code Python"""
        assert detect_category("écris une fonction python") == "code"
        assert detect_category("def fibonacci(n):") == "code"
        assert detect_category("import pandas") == "code"
    
    def test_detect_code_javascript(self):
        """Détection code JavaScript"""
        assert detect_category("function hello()") == "code"
        assert detect_category("const x =") == "code"
    
    def test_detect_reasoning(self):
        """Détection reasoning"""
        assert detect_category("pourquoi le ciel est bleu") == "reasoning"
        assert detect_category("explique comment") == "reasoning"
        assert detect_category("analyse ce problème") == "reasoning"
    
    def test_detect_conversation(self):
        """Détection conversation"""
        assert detect_category("bonjour") == "conversation"
        assert detect_category("merci") == "conversation"
        assert detect_category("ok") == "conversation"


class TestContinuationDetection:
    """Test 2.2: Détection de continuité"""
    
    def test_short_continuation_yes(self):
        """Messages courts = continuation"""
        assert is_continuation("ok") == True
        assert is_continuation("yes") == True
        assert is_continuation("merci") == True
    
    def test_short_continuation_no(self):
        """Messages longs = pas continuation"""
        assert is_continuation("écris une fonction python complète") == False
        assert is_continuation("pourquoi le ciel est bleu explique moi") == False


class TestModelMappings:
    """Test 2.3: Mappings modèles"""
    
    def test_models_defined(self):
        """Tous les modèles sont définis"""
        assert "code" in MODEL_MAPPINGS
        assert "reasoning" in MODEL_MAPPINGS
        assert "conversation" in MODEL_MAPPINGS
    
    def test_models_have_fallbacks(self):
        """Chaque catégorie a plusieurs modèles (fallbacks)"""
        assert len(MODEL_MAPPINGS["code"]) >= 2
        assert len(MODEL_MAPPINGS["reasoning"]) >= 2
        assert len(MODEL_MAPPINGS["conversation"]) >= 2
    
    def test_glm5_in_mappings(self):
        """GLM-5 est dans les mappings"""
        assert "z-ai/glm-5" in MODEL_MAPPINGS["code"]
        assert "z-ai/glm-5" in MODEL_MAPPINGS["reasoning"]


class TestRouteMessage:
    """Test routing messages"""
    
    def test_route_code_message(self):
        """Messages code → modèle code"""
        messages = [{"role": "user", "content": "def hello():"}]
        model = route_message(messages, "test_session")
        assert model in MODEL_MAPPINGS["code"]
    
    def test_route_continuity(self):
        """Continuation → même modèle"""
        # Premier message
        messages1 = [{"role": "user", "content": "écris une fonction"}]
        model1 = route_message(messages1, "session_1")
        
        # Deuxième message (continuation)
        messages2 = [{"role": "user", "content": "ok"}]
        model2 = route_message(messages2, "session_1")
        
        # Même modèle pour continuité
        assert model1 == model2


class TestFallbacks:
    """Test 2.4: Gestion des fallbacks"""
    
    def test_fallback_models_list(self):
        """Liste des modèles de fallback"""
        models = MODEL_MAPPINGS["code"]
        assert len(models) >= 2
        assert "z-ai/glm-5" in models
        assert "openai/gpt-5-nano" in models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
