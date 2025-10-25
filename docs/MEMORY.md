# Memory engine (LTM)

## Co doszło
- FTS5 (unicode61, diakrytyki PL) z triggerami sync
- Dedup (SHA1 po normalized text)
- Skoring łączony: BM25 (odwrócony) × konf. × świeżość (połowiczny rozpad 180 dni)
- API: add / search / export / import / optimize
- UI: podpowiedzi pamięci przy pisaniu (nie blokują wysyłki)

## API
POST /api/memory/add
{ "text":"...", "meta":{}, "conf":0.7, "lang":"pl", "source":"manual|auto" }

POST /api/memory/search
{ "q":"twoje zapytanie", "topk":8 }

GET /api/memory/export
POST /api/memory/import { "items":[ ... z exportu ... ] }
POST /api/memory/optimize

## Tipy
- Używaj `conf` (0..1) wyżej dla faktów sprawdzonych.
- Regularny `optimize` po większych importach.
- Możesz wrzucać skróty rozmów do LTM (np. co 20 tur) jako wysokokonf. fakty.
