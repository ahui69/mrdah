# 🔥 WSZYSTKIE ENDPOINTY W PROJEKCIE MORDZIX AI 🔥

## LISTA PLIKÓW Z ROUTERAMI (38 plików)

### 1. core/assistant_endpoint.py
- `/api/chat/assistant` (POST) - Główny chat z AI
- `/api/chat/assistant/stream` (POST) - Streaming chat
- `/api/chat/auto` (POST) - Automatyczne zapytania

### 2. core/psyche_endpoint.py
- `/api/psyche` (POST) - Analiza wiadomości i aktualizacja stanu
- `/api/psyche/state` (GET) - Pobierz bieżący stan
- `/api/psyche/state` (POST) - Ustaw stan
- `/api/psyche/reset` (POST) - Reset stanu
- `/api/psyche/history` (GET) - Ostatnie wiadomości

### 3. core/cognitive_endpoint.py
- `/api/cognitive/reflect` (POST) - Refleksja kognitywna
- `/api/cognitive/reflection/summary` (GET) - Podsumowanie refleksji
- `/api/cognitive/proactive/suggestions` (POST) - Proaktywne sugestie
- `/api/cognitive/psychology/analyze` (POST) - Analiza psychologiczna
- `/api/cognitive/psychology/state/{user_id}` (GET) - Stan psychologiczny użytkownika
- `/api/cognitive/process` (POST) - Przetwarzanie kognitywne
- `/api/cognitive/nlp/analyze` (POST) - Analiza NLP
- `/api/cognitive/semantic/analyze` (POST) - Analiza semantyczna
- `/api/cognitive/tools/list` (GET) - Lista narzędzi
- `/api/cognitive/status` (GET) - Status silnika kognitywnego

### 4. core/memory_endpoint.py
- `/api/memory/add` (POST) - Dodaj do pamięci
- `/api/memory/search` (POST) - Szukaj w pamięci
- `/api/memory/export` (GET) - Eksport pamięci
- `/api/memory/import` (POST) - Import pamięci
- `/api/memory/status` (GET) - Status pamięci
- `/api/memory/optimize` (POST) - Optymalizacja pamięci

### 5. core/research_endpoint.py
- `/api/research/search` (POST) - Wyszukiwanie w internecie
- `/api/research/autonauka` (POST) - Automatyczne uczenie się
- `/api/research/sources` (GET) - Lista źródeł
- `/api/research/test` (GET) - Test research

### 6. core/travel_endpoint.py
- `/api/travel/search` - Wyszukiwanie podróży (hotele, restauracje, atrakcje)

### 7. core/files_endpoint.py
- `/api/files/upload` (POST) - Upload plików
- `/api/files/{tenant}/{day}/{name}` (GET) - Pobierz plik
- `/api/files/thumb/{tenant}/{day}/{name}` (GET) - Miniatura

### 8. core/image_endpoint.py
- `/api/image/generate` (POST) - Generowanie obrazów
- `/api/image/file/{tenant}/{name}` (GET) - Pobierz obraz

### 9. core/vision_endpoint.py
- `/api/vision/*` - Analiza obrazów, OCR

### 10. core/voice_endpoint.py
- `/api/voice/*` - Przetwarzanie głosu

### 11. core/stt_endpoint.py
- `/api/stt/*` - Speech-to-Text (Whisper)

### 12. core/batch_endpoint.py
- `/api/batch/process` (POST) - Przetwarzanie wsadowe
- `/api/batch/submit` (POST) - Dodaj do kolejki
- `/api/batch/metrics` (GET) - Metryki
- `/api/batch/shutdown` (POST) - Zatrzymaj procesor

### 13. core/suggestions_endpoint.py
- `/api/suggestions/generate` (POST) - Generuj sugestie

### 14. core/frontend_autorouter.py
- `/api/autoroute/analyze` (POST) - Analiza zapytania
- `/api/autoroute/execute` (POST) - Wykonaj akcję
- `/api/autoroute/endpoints` (GET) - Lista endpointów
- `/api/autoroute/stats` (GET) - Statystyki

### 15. core/lang_endpoint.py
- `/api/lang/detect` (POST) - Detekcja języka

### 16. core/prometheus_endpoint.py
- `/api/prometheus/metrics` (GET) - Metryki Prometheus
- `/api/prometheus/health` (GET) - Health check
- `/api/prometheus/stats` (GET) - Statystyki

## GŁÓWNY KATALOG (ROOT)

### 17. programista_endpoint.py
- `/api/code/snapshot` (GET) - Snapshot workspace
- `/api/code/exec` (POST) - Wykonaj kod
- `/api/code/write` (POST) - Zapisz plik
- `/api/code/read` (GET) - Odczytaj plik
- `/api/code/tree` (GET) - Drzewo plików
- `/api/code/init` (POST) - Inicjalizuj projekt
- `/api/code/plan` (POST) - Planowanie
- `/api/code/lint` (POST) - Linting
- `/api/code/test` (POST) - Testy
- `/api/code/format` (POST) - Formatowanie
- `/api/code/git` (POST) - Operacje Git
- `/api/code/docker/build` (POST) - Build Docker
- `/api/code/docker/run` (POST) - Run Docker
- `/api/code/deps/install` (POST) - Instalacja zależności

### 18. files_endpoint.py (ROOT)
- `/api/files/upload` (POST) - Upload plików
- `/api/files/upload/base64` (POST) - Upload base64
- `/api/files/list` (GET) - Lista plików
- `/api/files/download` (GET) - Pobierz plik
- `/api/files/analyze` (POST) - Analiza pliku
- `/api/files/delete` (POST) - Usuń plik
- `/api/files/stats` (GET) - Statystyki
- `/api/files/batch/analyze` (POST) - Wsadowa analiza

### 19. admin_endpoint.py
- `/api/admin/cache/stats` (GET) - Statystyki cache
- `/api/admin/cache/clear` (POST) - Wyczyść cache
- `/api/admin/ratelimit/usage/{user_id}` (GET) - Użycie rate limit
- `/api/admin/ratelimit/config` (GET) - Konfiguracja rate limit
- `/api/admin/jwt/rotate` (POST) - Rotacja JWT

### 20. captcha_endpoint.py
- `/api/captcha/solve` (POST) - Rozwiąż captcha
- `/api/captcha/balance` (GET) - Balance API

### 21. batch_endpoint.py (ROOT)
- `/api/batch/process` (POST)
- `/api/batch/submit` (POST)
- `/api/batch/metrics` (GET)
- `/api/batch/shutdown` (POST)

### 22. cognitive_endpoint.py (ROOT - DUPLIKAT)
Identyczne jak core/cognitive_endpoint.py

### 23. research_endpoint.py (ROOT - DUPLIKAT)
Identyczne jak core/research_endpoint.py

### 24. nlp_endpoint.py
- `/api/nlp/analyze` (POST) - Analiza NLP
- `/api/nlp/batch-analyze` (POST) - Wsadowa analiza
- `/api/nlp/extract-topics` (POST) - Ekstrakcja tematów
- `/api/nlp/stats` (GET) - Statystyki NLP
- `/api/nlp/entities` (POST) - Rozpoznawanie encji
- `/api/nlp/sentiment` (POST) - Analiza sentymentu
- `/api/nlp/key-phrases` (POST) - Kluczowe frazy
- `/api/nlp/readability` (POST) - Czytelność

### 25. tts_endpoint.py
- `/api/tts/*` - Text-to-Speech (ElevenLabs)

### 26. stt_endpoint.py (ROOT - DUPLIKAT)
- `/api/stt/*` - Speech-to-Text

### 27. writing_endpoint.py
- `/api/writing/*` - Generowanie tekstów

### 28. suggestions_endpoint.py (ROOT - DUPLIKAT)
- `/api/suggestions/generate` (POST)

### 29. prometheus_endpoint.py (ROOT - DUPLIKAT)
- `/api/prometheus/metrics` (GET)
- `/api/prometheus/health` (GET)
- `/api/prometheus/stats` (GET)

### 30. psyche_endpoint.py (ROOT - DUPLIKAT)
Identyczne jak core/psyche_endpoint.py

### 31. internal_endpoint.py
- `/api/internal/ui_token` (GET) - Token UI

### 32. internal_ui.py
- `/api/internal/ui` (GET) - Interfejs wewnętrzny

### 33. hacker_endpoint.py
- `/api/hacker/scan/ports` (POST) - Skanowanie portów
- `/api/hacker/scan/vulnerabilities` (POST) - Skanowanie podatności
- `/api/hacker/exploit/sqli` (POST) - Test SQL Injection
- `/api/hacker/recon/domain` (POST) - Rekonesans domeny
- `/api/hacker/tools/status` (GET) - Status narzędzi
- `/api/hacker/exploits/list` (GET) - Lista exploitów

### 34. fashion_endpoint.py
- `/api/fashion/generate-outfit` (POST) - Generuj stylizację
- `/api/fashion/forecast-trends` (POST) - Prognoza trendów
- `/api/fashion/detect-brand` (POST) - Rozpoznaj markę
- `/api/fashion/categories` (GET) - Kategorie mody
- `/api/fashion/occasions` (GET) - Okazje
- `/api/fashion/weather-types` (GET) - Typy pogody
- `/api/fashion/stats` (GET) - Statystyki

### 35. ml_endpoint.py
- `/api/ml/predict-suggestions` (POST) - Predykcje ML (95% accuracy)
- `/api/ml/record-feedback` (POST) - Feedback do modelu
- `/api/ml/stats` (GET) - Statystyki ML
- `/api/ml/model-info` (GET) - Info o modelu
- `/api/ml/retrain` (POST) - Retrenuj model

### 36. fact_validation_endpoint.py
- `/api/facts/validate` (POST) - Waliduj fakt
- `/api/facts/validate-batch` (POST) - Wsadowa walidacja
- `/api/facts/source-reliability` (POST) - Wiarygodność źródła
- `/api/facts/reliability-weights` (GET) - Wagi wiarygodności
- `/api/facts/validation-stats` (GET) - Statystyki walidacji

### 37. reflection_endpoint.py
- `/api/reflection/*` - Self-Reflection Engine (5 poziomów)

### 38. psyche_endpoint_server_backup.py
BACKUP - nie używany

## ROUTERY W core/app.py (23 include_router)

```python
# W core/app.py są załadowane:
1. core.assistant_endpoint
2. core.psyche_endpoint
3. programista_endpoint (ROOT)
4. files_endpoint (ROOT)
5. core.travel_endpoint
6. admin_endpoint (ROOT)
7. captcha_endpoint (ROOT)
8. prometheus_endpoint (ROOT)
9. tts_endpoint (ROOT)
10. stt_endpoint (ROOT)
11. writing_endpoint (ROOT)
12. core.suggestions_endpoint
13. batch_endpoint (ROOT)
14. research_endpoint (ROOT)
15. core.cognitive_endpoint
16. core.memory_endpoint
17. fashion_endpoint (ROOT)
18. ml_endpoint (ROOT)
19. fact_validation_endpoint (ROOT)
20. core.vision_endpoint
21. core.voice_endpoint
22. reflection_endpoint (ROOT)
23. hacker_endpoint (ROOT)
```

## PROBLEM: DUPLIKATY!

**ZAUWAŻ KURWA:**
- `core/cognitive_endpoint.py` vs `cognitive_endpoint.py` (ROOT)
- `core/research_endpoint.py` vs `research_endpoint.py` (ROOT)
- `core/batch_endpoint.py` vs `batch_endpoint.py` (ROOT)
- `core/psyche_endpoint.py` vs `psyche_endpoint.py` (ROOT)
- `core/files_endpoint.py` vs `files_endpoint.py` (ROOT)
- `core/suggestions_endpoint.py` vs `suggestions_endpoint.py` (ROOT)
- `core/stt_endpoint.py` vs `stt_endpoint.py` (ROOT)
- `core/prometheus_endpoint.py` vs `prometheus_endpoint.py` (ROOT)

## ENDPOINTY BEZPOŚREDNIO W app.py

```python
@app.get("/api") - Status API
@app.get("/status") - Status API
@app.get("/health") - Health check
@app.get("/api/endpoints/list") - Lista endpointów
@app.get("/api/automation/status") - Status automatyzacji
@app.get("/") - Frontend (HTML)
@app.get("/app") - Frontend (HTML)
@app.get("/chat") - Frontend (HTML)
@app.get("/{full_path:path}") - Catch-all dla Angular SPA
@app.get("/sw.js") - Service Worker
@app.get("/ngsw-worker.js") - Service Worker
@app.get("/manifest.webmanifest") - PWA Manifest
@app.get("/favicon.ico") - Favicon
@app.get("/webui/") - WebUI Frontend
@app.get("/metrics") - Prometheus metrics
```

## CAŁKOWITA LICZBA ENDPOINTÓW

**Unique API endpoints: ~120+**

**Problem:** Wiele plików jest duplikatami - niektóre w `core/`, niektóre w ROOT!

