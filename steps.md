# LLM Router - Étapes de développement

## Phase 1: Setup minimal (forward only)

- [x] **1.1** Créer le projet de service API (nom: `llm-router-service`)
- [x] **1.2** Implémenter endpoint `/v1/chat/completions` (interface OpenAI)
- [x] **1.3** Ajouter config pour provider cible (OpenRouter par défaut)
- [x] **1.4** Forward des requêtes vers OpenRouter sans modification
- [x] **1.5** Tester localement avec curl/OpenClaw
- [x] **1.6** Documenter la config OpenClaw pour utiliser le router

## Phase 2: Routing de base (keywords/rules)

- [x] **2.1** Ajouter logique de détection (code vs conversation vs reasoning)
- [x] **2.2** Implémenter détection de continuité (messages courts = même model)
- [x] **2.3** Configurer mappings modèles par catégorie
- [x] **2.4** Ajouter gestion des fallbacks (si provider down → suivant)
- [x] **2.5** Tests et validation
- [x] **2.6** Ajouter monitoring basique (latence, modèle utilisé, succès/échec)

## Phase 3: Router LLM

- [ ] **3.1** Intégrer petit modèle local (Qwen-0.5B) ou API légère
- [ ] **3.2** Implémenter le prompt de routing
- [ ] **3.3** Ajouter métriques (cost, latence, utilisation)
- [ ] **3.4** Ajouter circuit breaker
- [ ] **3.5** Tests de charge et validation

## Notes

- Tech stack: À choisir (Python FastAPI ou Node.js Express)
- Hébergement: Local
- Provider cible phase 1: OpenRouter
- Stockage clés API: Variables d'environnement sécurisées