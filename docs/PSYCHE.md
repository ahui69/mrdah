# Psychika + Pamięć

- Endpoint: `/api/psyche` – analizuje wiadomość (PL), aktualizuje stan i zapisuje do bazy (SQLite + FTS).
- Stan: `/api/psyche/state` (GET/POST), reset: `/api/psyche/reset`, historia: `/api/psyche/history`.
- Pamięć: `core/memory_store.py` – tabele: `conversations`, `conversations_fts`, `psyche_state`, `psyche_journal`.

**Algorytm**: prosta regułowa analiza PL (listy słów pozytywnych/negatywnych) → delty (`mood/energy/stress/focus`) → zapis stanu.
