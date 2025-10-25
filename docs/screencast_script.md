# Screencast – 120 sekund (plan nagrania)

**Cel:** Pokazać działający produkt: chat, pamięć, upload plików, voice-in, panel admin.

0–10 s: Intro
- Terminal: `docker-compose up -d` (krótki zrzut logów)
- Przeglądarka: otwarcie `http://localhost:8080/docs` (health)

10–40 s: Chat + pamięć
- Frontend: wpisz pytanie, potem kontynuuj – pokaż pamiętanie kontekstu (STM→LTM)
- W tle pokaż w devtools krótkie SSE/stream

40–70 s: Upload pliku + analiza
- Przeciągnij PDF/obraz do `DragDropUpload` → zademonstruj odpowiedź API

70–95 s: Voice-in
- Kliknij mikrofon, powiedz 1 zdanie, pokaż transkrypcję i odpowiedź

95–120 s: Admin + metryki
- `/api/admin/*` (JWT w nagłówku) – pokaż czyszczenie cache
- `/metrics` w przeglądarce (Prometheus)
- Zakończenie: 1 zdanie – co kupujący dostaje

**Wskazówki:**
- Rozdzielczość 1920×1080, dark theme, brak danych wrażliwych na ekranie.
- Krótkie podpisy tekstowe (callouts): „Memory on”, „JWT admin”, „Dockerized”.
