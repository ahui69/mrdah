-- Redis Cache Analytics Tables
-- Stores cache statistics and hit/miss tracking

CREATE TABLE IF NOT EXISTS cache_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(255) NOT NULL,
    cache_key VARCHAR(512) NOT NULL,
    hit_or_miss VARCHAR(10) NOT NULL,  -- 'HIT' or 'MISS'
    ttl_seconds INTEGER,
    response_size INTEGER,  -- Size in bytes
    user_id VARCHAR(255),
    model_name VARCHAR(100),
    UNIQUE(timestamp, cache_key) ON CONFLICT IGNORE
);

CREATE INDEX IF NOT EXISTS idx_cache_stats_timestamp ON cache_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_cache_stats_endpoint ON cache_stats(endpoint);
CREATE INDEX IF NOT EXISTS idx_cache_stats_hit_miss ON cache_stats(hit_or_miss);

CREATE TABLE IF NOT EXISTS cache_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_requests INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    hit_rate REAL DEFAULT 0.0,
    avg_response_size INTEGER DEFAULT 0,
    total_bandwidth_saved INTEGER DEFAULT 0,  -- Bytes saved by cache hits
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_summary_date ON cache_summary(date);

-- View for daily cache performance
CREATE VIEW IF NOT EXISTS v_cache_performance AS
SELECT 
    DATE(timestamp) as date,
    endpoint,
    COUNT(*) as total_requests,
    SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) as hits,
    SUM(CASE WHEN hit_or_miss = 'MISS' THEN 1 ELSE 0 END) as misses,
    ROUND(
        CAST(SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) AS REAL) / 
        COUNT(*) * 100, 
        2
    ) as hit_rate_percent,
    AVG(response_size) as avg_response_size,
    SUM(CASE WHEN hit_or_miss = 'HIT' THEN response_size ELSE 0 END) as bandwidth_saved
FROM cache_stats
GROUP BY DATE(timestamp), endpoint
ORDER BY date DESC, total_requests DESC;

-- View for top cached endpoints
CREATE VIEW IF NOT EXISTS v_top_cached_endpoints AS
SELECT 
    endpoint,
    COUNT(*) as total_requests,
    SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) as cache_hits,
    ROUND(
        CAST(SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) AS REAL) / 
        COUNT(*) * 100, 
        2
    ) as hit_rate_percent
FROM cache_stats
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY endpoint
ORDER BY cache_hits DESC
LIMIT 20;

-- View for cache efficiency by model
CREATE VIEW IF NOT EXISTS v_cache_by_model AS
SELECT 
    model_name,
    COUNT(*) as total_requests,
    SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) as cache_hits,
    ROUND(
        CAST(SUM(CASE WHEN hit_or_miss = 'HIT' THEN 1 ELSE 0 END) AS REAL) / 
        COUNT(*) * 100, 
        2
    ) as hit_rate_percent,
    AVG(response_size) as avg_response_size
FROM cache_stats
WHERE model_name IS NOT NULL
  AND timestamp >= datetime('now', '-7 days')
GROUP BY model_name
ORDER BY total_requests DESC;
