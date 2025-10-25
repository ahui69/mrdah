# Quickstart (cURL)
### GET /cache/stats
```bash
curl -s -X GET {BASE_URL}/cache/stats \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### POST /cache/clear
```bash
curl -s -X POST {BASE_URL}/cache/clear \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### GET /ratelimit/usage/{user_id}
```bash
curl -s -X GET {BASE_URL}/ratelimit/usage/{user_id} \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### GET /ratelimit/config
```bash
curl -s -X GET {BASE_URL}/ratelimit/config \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### POST /process
```bash
curl -s -X POST {BASE_URL}/process \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### POST /submit
```bash
curl -s -X POST {BASE_URL}/submit \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### GET /metrics
```bash
curl -s -X GET {BASE_URL}/metrics \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### POST /shutdown
```bash
curl -s -X POST {BASE_URL}/shutdown \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### POST /solve
```bash
curl -s -X POST {BASE_URL}/solve \
  -H 'Authorization: Bearer {'TOKEN'}'
```

### GET /balance
```bash
curl -s -X GET {BASE_URL}/balance \
  -H 'Authorization: Bearer {'TOKEN'}'
```

