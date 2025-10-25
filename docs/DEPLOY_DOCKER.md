
# Deploy (Docker)

## Lokalnie
```bash
docker compose up --build -d
# UI: http://localhost:8080/webui
```

## Produkcja (minimal)
- reverse proxy (np. Nginx/Caddy) po HTTPS,
- ustaw `CORS_ORIGINS` na swoją domenę,
- `RL_DISABLE=0` (domyślnie),
- `JWT_SECRET` ustaw jako zmienną środowiskową lub przez `/api/admin/jwt/rotate`,
- wolumeny: `data/`, `logs/`, `uploads/` trzymane na dysku hosta.
