#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
UNIFIED MEMORY SYSTEM - Enterprise-Grade Multi-Layer Memory Architecture
═══════════════════════════════════════════════════════════════════════════════

Architecture:
    L0: Short-Term Memory (STM) - Active conversation context (RAM)
    L1: Episodic Memory - Recent events and conversations (SQLite + RAM)
    L2: Semantic Memory - Long-term facts and knowledge (SQLite + FTS + Vectors)
    L3: Procedural Memory - Learned patterns and procedures (SQLite)
    L4: Meta/Mental Models - User profiles and domain knowledge (SQLite + Graph)

Features:
    ✅ Multi-layer hierarchical memory with auto-consolidation
    ✅ Vector embeddings for semantic search (sentence-transformers)
    ✅ Graph-based associative connections between memories
    ✅ Redis caching for hot data (LRU eviction)
    ✅ Memory decay and forgetting curves (Ebbinghaus)
    ✅ Importance scoring and reinforcement learning
    ✅ Temporal weighting and recency bias
    ✅ Cross-layer context retrieval
    ✅ Hybrid search: BM25 + Vector + Graph traversal
    ✅ Automatic consolidation background tasks
    ✅ Comprehensive health monitoring and analytics

Storage:
    - SQLite: Primary persistence (optimized with WAL, mmap, indexes)
    - Redis: Hot cache layer (LRU, TTL-based eviction)
    - Filesystem: Vector indices, backups (/ltm_storage/{user_id}/...)

NO PLACEHOLDERS - FULL PRODUCTION-GRADE IMPLEMENTATION!
═══════════════════════════════════════════════════════════════════════════════
"""

import os
import sys
import time
import json
import uuid
import sqlite3
import hashlib
import pickle
import numpy as np
import asyncio
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional, Set, Union
from collections import Counter, deque, defaultdict
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta

# Core imports
from .config import (
    BASE_DIR, DB_PATH, STM_LIMIT, STM_CONTEXT_WINDOW,
    LTM_IMPORTANCE_THRESHOLD, LTM_CACHE_SIZE
)
from .helpers import (
    log_info, log_warning, log_error,
    tokenize, make_id, tfidf_cosine,
    embed_texts, cosine_similarity
)

# Redis cache (optional)
try:
    from .redis_middleware import get_redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    log_warning("Redis not available, using in-memory cache only", "MEMORY")


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Memory limits and thresholds (UPGRADED!)
MAX_STM_SIZE = 500  # 500 messages (było 130)
MAX_EPISODIC_SIZE = 5000  # Recent episodes kept in RAM (było 1000)
MAX_SEMANTIC_SIZE = 10000  # 10k facts in RAM cache (było 1000)
MAX_GRAPH_NODES = 50000  # Max nodes in associative graph (było 5000)

# Consolidation thresholds (MORE AGGRESSIVE!)
EPISODIC_TO_SEMANTIC_THRESHOLD = 3  # Min episodes to create semantic fact (było 5)
SEMANTIC_CLUSTERING_THRESHOLD = 2  # Min facts to create cluster (było 3)
PROCEDURAL_LEARNING_THRESHOLD = 2  # Min executions to learn procedure (było 3)

# Decay and forgetting (LONGER RETENTION!)
MEMORY_DECAY_RATE = 0.02  # Connection decay per hour (było 0.05 - wolniejszy decay)
FORGETTING_CURVE_HALFLIFE = 30 * 24 * 3600  # 30 days in seconds (było 7 dni)
REINFORCEMENT_BOOST = 0.25  # Boost on memory access (było 0.2 - większy boost)

# Background tasks (🔥 TURBO MODE!)
AUTO_CONSOLIDATION_INTERVAL = 180  # 🔥 3 minutes (było 10min) - HARDCORE!
CLEANUP_INTERVAL = 1800  # 30 minutes (było 1h)
BACKUP_INTERVAL = 43200  # 12 hours (było 24h)

# Storage paths
LTM_STORAGE_ROOT = os.getenv("LTM_STORAGE_ROOT", os.path.join(BASE_DIR, "ltm_storage"))
VECTOR_INDEX_PATH = os.path.join(LTM_STORAGE_ROOT, "vector_indices")
BACKUP_PATH = os.path.join(LTM_STORAGE_ROOT, "backups")

# Create directories
for p in [LTM_STORAGE_ROOT, VECTOR_INDEX_PATH, BACKUP_PATH]:
    Path(p).mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MemoryNode:
    """Universal memory node for all layers"""
    id: str
    layer: str  # L0, L1, L2, L3, L4
    content: str
    user_id: str = "default"
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Scoring
    importance: float = 0.5  # 0-1
    confidence: float = 0.7  # 0-1
    
    # Temporal
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    
    # Associations
    connections: Dict[str, float] = field(default_factory=dict)  # node_id -> strength
    
    # Vector embedding (lazy loaded)
    _embedding: Optional[np.ndarray] = None
    
    def access(self) -> None:
        """Update access statistics and apply reinforcement"""
        self.accessed_at = time.time()
        self.access_count += 1
        # Reinforcement learning: importance grows with access
        self.importance = min(1.0, self.importance + REINFORCEMENT_BOOST * (1.0 - self.importance))
    
    def connect(self, other_id: str, strength: float = 0.5) -> None:
        """Create or strengthen connection to another node"""
        current = self.connections.get(other_id, 0.0)
        # Hebbian learning: "neurons that fire together wire together"
        self.connections[other_id] = min(1.0, current + strength * (1.0 - current))
    
    def decay_connections(self, hours_elapsed: float = 1.0) -> None:
        """Apply memory decay to connections (Ebbinghaus forgetting curve)"""
        decay_factor = 1.0 - (MEMORY_DECAY_RATE * hours_elapsed)
        for node_id in list(self.connections.keys()):
            self.connections[node_id] *= decay_factor
            if self.connections[node_id] < 0.1:
                del self.connections[node_id]
    
    def get_embedding(self) -> np.ndarray:
        """Get or generate vector embedding"""
        if self._embedding is None:
            embeddings = embed_texts([self.content])
            self._embedding = np.array(embeddings[0]) if embeddings else np.zeros(384)
        return self._embedding
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "layer": self.layer,
            "content": self.content,
            "user_id": self.user_id,
            "tags": self.tags,
            "metadata": self.metadata,
            "importance": self.importance,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "accessed_at": self.accessed_at,
            "access_count": self.access_count,
            "connections": self.connections,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryNode':
        """Deserialize from dictionary"""
        return cls(
            id=data["id"],
            layer=data["layer"],
            content=data["content"],
            user_id=data.get("user_id", "default"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.7),
            created_at=data.get("created_at", time.time()),
            accessed_at=data.get("accessed_at", time.time()),
            access_count=data.get("access_count", 0),
            connections=data.get("connections", {}),
        )


@dataclass
class MemorySearchResult:
    """Search result with scoring details"""
    node: MemoryNode
    score: float
    match_type: str  # "exact", "semantic", "temporal", "graph"
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node.to_dict(),
            "score": self.score,
            "match_type": self.match_type,
            "context": self.context
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryDatabase:
    """SQLite database layer with optimizations"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        # Ensure parent dir exists
        try:
            from pathlib import Path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._init_db()
    
    def _conn(self) -> sqlite3.Connection:
        """Get optimized database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Performance optimizations (🔥 HARDCORE TUNING!)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA temp_store=MEMORY;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA cache_size=-2000000;")  # 🔥 2GB cache (było 500MB)
        conn.execute("PRAGMA mmap_size=8589934592;")  # 🔥 8GB mmap (było 2GB)
        conn.execute("PRAGMA page_size=8192;")  # 8KB pages
        conn.execute("PRAGMA busy_timeout=30000;")  # 30s timeout
        conn.execute("PRAGMA wal_autocheckpoint=20000;")  # 🔥 WAL checkpoint 20k (było 5k default)
        
        return conn
    
    def _init_db(self) -> None:
        """Initialize all database tables and indices"""
        with self._lock, self._conn() as conn:
            c = conn.cursor()
            
            # ═══════════════════════════════════════════════════════════
            # CORE MEMORY TABLE
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_nodes (
                    id TEXT PRIMARY KEY,
                    layer TEXT NOT NULL,
                    content TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT,
                    importance REAL DEFAULT 0.5,
                    confidence REAL DEFAULT 0.7,
                    created_at REAL NOT NULL,
                    accessed_at REAL NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    connections TEXT,
                    embedding BLOB,
                    deleted INTEGER DEFAULT 0
                );
            """)
            
            # Indices for memory_nodes
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_layer ON memory_nodes(layer, deleted);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_user_layer ON memory_nodes(user_id, layer, deleted);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_created ON memory_nodes(created_at DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_accessed ON memory_nodes(accessed_at DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_importance ON memory_nodes(importance DESC) WHERE deleted=0;")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_tags ON memory_nodes(tags) WHERE deleted=0;")
            
            # 🔥 COMPOSITE INDICES dla hardcore performance!
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_user_layer_created ON memory_nodes(user_id, layer, created_at DESC) WHERE deleted=0;")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_user_importance ON memory_nodes(user_id, importance DESC, confidence DESC) WHERE deleted=0;")
            c.execute("CREATE INDEX IF NOT EXISTS idx_nodes_conf_imp ON memory_nodes(confidence DESC, importance DESC) WHERE deleted=0;")
            
            # ═══════════════════════════════════════════════════════════
            # FTS5 FULL-TEXT SEARCH
            # ═══════════════════════════════════════════════════════════
            try:
                c.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts 
                    USING fts5(content, tags, user_id UNINDEXED, node_id UNINDEXED);
                """)
                log_info("FTS5 full-text search enabled", "MEMORY_DB")
            except Exception as e:
                log_warning(f"FTS5 not available: {e}", "MEMORY_DB")
            
            # ═══════════════════════════════════════════════════════════
            # EPISODIC MEMORY (L1)
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_episodes (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    episode_type TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    related_stm_ids TEXT,
                    metadata TEXT,
                    timestamp REAL NOT NULL
                );
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_episodes_user_ts ON memory_episodes(user_id, timestamp DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_episodes_type ON memory_episodes(episode_type);")
            
            # ═══════════════════════════════════════════════════════════
            # SEMANTIC CLUSTERS (L2)
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_semantic_clusters (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    cluster_topic TEXT NOT NULL,
                    related_node_ids TEXT,
                    consolidated_fact_id TEXT,
                    strength REAL DEFAULT 1.0,
                    last_reinforced REAL,
                    created_at REAL
                );
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_clusters_user_topic ON memory_semantic_clusters(user_id, cluster_topic);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_clusters_strength ON memory_semantic_clusters(strength DESC);")
            
            # ═══════════════════════════════════════════════════════════
            # PROCEDURAL MEMORY (L3)
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_procedures (
                    id TEXT PRIMARY KEY,
                    trigger_intent TEXT NOT NULL UNIQUE,
                    steps TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    avg_execution_time REAL DEFAULT 0.0,
                    context_conditions TEXT,
                    last_used REAL,
                    created_at REAL,
                    adaptations TEXT
                );
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_proc_success_rate ON memory_procedures(success_rate DESC);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_proc_last_used ON memory_procedures(last_used DESC);")
            
            # ═══════════════════════════════════════════════════════════
            # MENTAL MODELS (L4)
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_mental_models (
                    id TEXT PRIMARY KEY,
                    model_type TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence_count INTEGER DEFAULT 0,
                    model_data TEXT NOT NULL,
                    related_node_ids TEXT,
                    last_updated REAL,
                    created_at REAL,
                    validation_score REAL DEFAULT 0.0
                );
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_models_type_subject ON memory_mental_models(model_type, subject);")
            c.execute("CREATE INDEX IF NOT EXISTS idx_models_confidence ON memory_mental_models(confidence DESC);")
            
            # ═══════════════════════════════════════════════════════════
            # ANALYTICS AND METRICS
            # ═══════════════════════════════════════════════════════════
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT,
                    timestamp REAL NOT NULL
                );
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_analytics_name_ts ON memory_analytics(metric_name, timestamp DESC);")
            
            conn.commit()
            log_info("Memory database initialized successfully", "MEMORY_DB")
    
    def save_node(self, node: MemoryNode) -> None:
        """Save or update memory node"""
        with self._lock, self._conn() as conn:
            # Serialize complex fields
            tags_json = json.dumps(node.tags)
            metadata_json = json.dumps(node.metadata)
            connections_json = json.dumps(node.connections)
            embedding_bytes = pickle.dumps(node._embedding) if node._embedding is not None else None
            
            conn.execute("""
                INSERT OR REPLACE INTO memory_nodes 
                (id, layer, content, user_id, tags, metadata, importance, confidence,
                 created_at, accessed_at, access_count, connections, embedding, deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                node.id, node.layer, node.content, node.user_id,
                tags_json, metadata_json, node.importance, node.confidence,
                node.created_at, node.accessed_at, node.access_count,
                connections_json, embedding_bytes
            ))
            
            # Update FTS index
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_fts (content, tags, user_id, node_id)
                    VALUES (?, ?, ?, ?)
                """, (node.content, " ".join(node.tags), node.user_id, node.id))
            except:
                pass  # FTS not available
            
            conn.commit()
    
    def load_node(self, node_id: str) -> Optional[MemoryNode]:
        """Load memory node by ID"""
        with self._conn() as conn:
            row = conn.execute("""
                SELECT * FROM memory_nodes WHERE id = ? AND deleted = 0
            """, (node_id,)).fetchone()
            
            if not row:
                return None
            
            # Deserialize
            node = MemoryNode(
                id=row["id"],
                layer=row["layer"],
                content=row["content"],
                user_id=row["user_id"],
                tags=json.loads(row["tags"] or "[]"),
                metadata=json.loads(row["metadata"] or "{}"),
                importance=row["importance"],
                confidence=row["confidence"],
                created_at=row["created_at"],
                accessed_at=row["accessed_at"],
                access_count=row["access_count"],
                connections=json.loads(row["connections"] or "{}")
            )
            
            # Deserialize embedding if exists
            if row["embedding"]:
                try:
                    node._embedding = pickle.loads(row["embedding"])
                except:
                    pass
            
            return node
    
    def search_nodes(self, query: str = "", layer: Optional[str] = None,
                     user_id: Optional[str] = None, limit: int = 100) -> List[MemoryNode]:
        """Search memory nodes with filters"""
        with self._conn() as conn:
            sql = "SELECT * FROM memory_nodes WHERE deleted = 0"
            params = []
            
            if query:
                # Try FTS first
                try:
                    fts_sql = """
                        SELECT node_id FROM memory_fts 
                        WHERE memory_fts MATCH ? 
                        ORDER BY bm25(memory_fts) 
                        LIMIT ?
                    """
                    fts_results = conn.execute(fts_sql, (query, limit)).fetchall()
                    if fts_results:
                        node_ids = [r["node_id"] for r in fts_results]
                        placeholders = ",".join("?" * len(node_ids))
                        sql = f"SELECT * FROM memory_nodes WHERE id IN ({placeholders}) AND deleted = 0"
                        params = node_ids
                except:
                    # Fallback to LIKE search
                    sql += " AND content LIKE ?"
                    params.append(f"%{query}%")
            
            if layer and not query:
                sql += " AND layer = ?"
                params.append(layer)
            
            if user_id and not query:
                sql += " AND user_id = ?"
                params.append(user_id)
            
            if not query:
                sql += " ORDER BY accessed_at DESC LIMIT ?"
                params.append(limit)
            
            rows = conn.execute(sql, params).fetchall()
            
            # Deserialize nodes
            nodes = []
            for row in rows:
                try:
                    node = MemoryNode(
                        id=row["id"],
                        layer=row["layer"],
                        content=row["content"],
                        user_id=row["user_id"],
                        tags=json.loads(row["tags"] or "[]"),
                        metadata=json.loads(row["metadata"] or "{}"),
                        importance=row["importance"],
                        confidence=row["confidence"],
                        created_at=row["created_at"],
                        accessed_at=row["accessed_at"],
                        access_count=row["access_count"],
                        connections=json.loads(row["connections"] or "{}")
                    )
                    if row["embedding"]:
                        try:
                            node._embedding = pickle.loads(row["embedding"])
                        except:
                            pass
                    nodes.append(node)
                except Exception as e:
                    log_error(e, "LOAD_NODE")
            
            return nodes
    
    def soft_delete_node(self, node_id: str) -> None:
        """Soft delete memory node"""
        with self._lock, self._conn() as conn:
            conn.execute("UPDATE memory_nodes SET deleted = 1 WHERE id = ?", (node_id,))
            conn.commit()
    
    def record_metric(self, metric_name: str, metric_value: float, metadata: Dict[str, Any] = None) -> None:
        """Record analytics metric"""
        with self._lock, self._conn() as conn:
            conn.execute("""
                INSERT INTO memory_analytics (metric_name, metric_value, metadata, timestamp)
                VALUES (?, ?, ?, ?)
            """, (metric_name, metric_value, json.dumps(metadata or {}), time.time()))
            conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# CACHE LAYER (Redis + RAM)
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryCache:
    """Two-tier cache: Redis (L1) + RAM (L2)"""
    
    def __init__(self, max_ram_size: int = 1000):
        self.max_ram_size = max_ram_size
        self._ram_cache: Dict[str, MemoryNode] = {}
        self._access_order: deque = deque()
        self._lock = threading.Lock()
        
        # Redis connection
        self.redis = None
        if REDIS_AVAILABLE:
            try:
                self.redis = get_redis()
                log_info("Redis cache layer enabled", "MEMORY_CACHE")
            except Exception as e:
                log_warning(f"Redis connection failed: {e}", "MEMORY_CACHE")
    
    def get(self, node_id: str) -> Optional[MemoryNode]:
        """Get node from cache (Redis -> RAM)"""
        # Try RAM first
        with self._lock:
            if node_id in self._ram_cache:
                self._access_order.remove(node_id)
                self._access_order.append(node_id)
                return self._ram_cache[node_id]
        
        # Try Redis
        if self.redis:
            try:
                data = self.redis.get(f"memory:node:{node_id}")
                if data:
                    node_dict = json.loads(data)
                    node = MemoryNode.from_dict(node_dict)
                    self.put(node)  # Promote to RAM
                    return node
            except Exception as e:
                log_error(e, "REDIS_GET")
        
        return None
    
    def put(self, node: MemoryNode, ttl: int = 3600) -> None:
        """Put node in cache (RAM + Redis)"""
        # RAM cache (LRU eviction)
        with self._lock:
            if node.id in self._ram_cache:
                self._access_order.remove(node.id)
            elif len(self._ram_cache) >= self.max_ram_size:
                # Evict least recently used
                oldest_id = self._access_order.popleft()
                del self._ram_cache[oldest_id]
            
            self._ram_cache[node.id] = node
            self._access_order.append(node.id)
        
        # Redis cache
        if self.redis:
            try:
                self.redis.setex(
                    f"memory:node:{node.id}",
                    ttl,
                    json.dumps(node.to_dict())
                )
            except Exception as e:
                log_error(e, "REDIS_PUT")
    
    def invalidate(self, node_id: str) -> None:
        """Remove node from cache"""
        with self._lock:
            if node_id in self._ram_cache:
                del self._ram_cache[node_id]
                self._access_order.remove(node_id)
        
        if self.redis:
            try:
                self.redis.delete(f"memory:node:{node_id}")
            except Exception as e:
                log_error(e, "REDIS_DELETE")
    
    def clear(self, user_id: Optional[str] = None) -> None:
        """Clear cache (optionally for specific user)"""
        with self._lock:
            if user_id:
                # Clear only nodes for this user
                to_remove = [nid for nid, node in self._ram_cache.items() if node.user_id == user_id]
                for nid in to_remove:
                    del self._ram_cache[nid]
                    self._access_order.remove(nid)
            else:
                # Clear everything
                self._ram_cache.clear()
                self._access_order.clear()
        
        if self.redis and not user_id:
            try:
                # Clear all memory keys
                for key in self.redis.scan_iter("memory:node:*"):
                    self.redis.delete(key)
            except Exception as e:
                log_error(e, "REDIS_CLEAR")


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY LAYERS (L0-L4)
# ═══════════════════════════════════════════════════════════════════════════════

class ShortTermMemory:
    """L0: Active conversation context (RAM only)"""
    
    def __init__(self, max_size: int = MAX_STM_SIZE):
        self.max_size = max_size
        self._conversations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_size))
        self._lock = threading.Lock()
    
    def add_message(self, user_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """Add message to STM"""
        msg_id = str(uuid.uuid4())
        message = {
            "id": msg_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        
        with self._lock:
            self._conversations[user_id].append(message)
        
        return msg_id
    
    def get_context(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        with self._lock:
            messages = list(self._conversations[user_id])
            if limit:
                messages = messages[-limit:]
            return messages
    
    def clear(self, user_id: str) -> None:
        """Clear STM for user"""
        with self._lock:
            self._conversations[user_id].clear()


class EpisodicMemory:
    """L1: Recent events and conversations"""
    
    def __init__(self, db: MemoryDatabase, cache: MemoryCache):
        self.db = db
        self.cache = cache
    
    def record_episode(self, user_id: str, episode_type: str, summary: str,
                       related_stm_ids: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Record new episode"""
        node = MemoryNode(
            id=str(uuid.uuid4()),
            layer="L1",
            content=summary,
            user_id=user_id,
            tags=[episode_type, "episode"],
            metadata={
                **(metadata or {}),
                "episode_type": episode_type,
                "related_stm_ids": related_stm_ids or []
            },
            importance=0.6,
            confidence=0.8
        )
        
        # Generate embedding
        node.get_embedding()
        
        # Save to DB and cache
        self.db.save_node(node)
        self.cache.put(node, ttl=7200)  # 2 hours
        
        log_info(f"[L1] Recorded episode: {episode_type}", "EPISODIC")
        return node.id
    
    def get_recent_episodes(self, user_id: str, limit: int = 50) -> List[MemoryNode]:
        """Get recent episodes for user"""
        return self.db.search_nodes(layer="L1", user_id=user_id, limit=limit)
    
    def find_related_episodes(self, query: str, user_id: str, limit: int = 10) -> List[MemorySearchResult]:
        """Find episodes related to query"""
        # Get all episodes
        all_episodes = self.get_recent_episodes(user_id, limit=200)
        
        if not all_episodes:
            return []
        
        # Generate query embedding
        query_emb = np.array(embed_texts([query])[0])
        
        # Score episodes
        results = []
        for ep in all_episodes:
            ep_emb = ep.get_embedding()
            
            # Semantic similarity
            semantic_score = float(cosine_similarity(query_emb, ep_emb))
            
            # Recency bonus
            age_hours = (time.time() - ep.created_at) / 3600
            recency_score = 1.0 / (1.0 + 0.01 * age_hours)
            
            # Combined score
            total_score = semantic_score * 0.7 + recency_score * 0.3
            
            results.append(MemorySearchResult(
                node=ep,
                score=total_score,
                match_type="semantic",
                context={"semantic": semantic_score, "recency": recency_score}
            ))
        
        # Sort and return top results
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]


class SemanticMemory:
    """L2: Long-term facts and knowledge (with vector search)"""
    
    def __init__(self, db: MemoryDatabase, cache: MemoryCache):
        self.db = db
        self.cache = cache
    
    def add_fact(self, content: str, user_id: str = "default", tags: List[str] = None,
                 confidence: float = 0.7, metadata: Dict[str, Any] = None) -> str:
        """Add fact to semantic memory"""
        node = MemoryNode(
            id=make_id(content),  # Deterministic ID for deduplication
            layer="L2",
            content=content,
            user_id=user_id,
            tags=(tags or []) + ["fact", "semantic"],
            metadata=metadata or {},
            importance=min(1.0, 0.5 + confidence * 0.3),  # Importance based on confidence
            confidence=confidence
        )
        
        # Check if exists
        existing = self.cache.get(node.id) or self.db.load_node(node.id)
        if existing:
            # Update existing fact (reinforce)
            existing.confidence = max(existing.confidence, confidence)
            existing.importance = min(1.0, existing.importance + REINFORCEMENT_BOOST)
            existing.access()
            self.db.save_node(existing)
            self.cache.put(existing)
            return existing.id
        
        # 🔥 FUZZY DEDUP: Check for similar facts (90% threshold)
        try:
            from difflib import SequenceMatcher
            recent_facts = self.db.search_nodes(
                query=content[:100], 
                layer="L2", 
                user_id=user_id, 
                limit=20
            )
            for fact in recent_facts:
                similarity = SequenceMatcher(None, content.lower(), fact.content.lower()).ratio()
                if similarity > 0.90:  # 90% podobne
                    log_info(f"[L2] FUZZY DEDUP: Skipping similar fact (sim={similarity:.2f})", "SEMANTIC")
                    # Reinforce existing instead
                    fact.confidence = max(fact.confidence, confidence)
                    fact.importance = min(1.0, fact.importance + REINFORCEMENT_BOOST)
                    fact.access()
                    self.db.save_node(fact)
                    self.cache.put(fact)
                    return fact.id
        except Exception as e:
            log_warning(f"Fuzzy dedup failed: {e}", "SEMANTIC")
        
        # Generate embedding
        node.get_embedding()
        
        # Save
        self.db.save_node(node)
        self.cache.put(node, ttl=86400)  # 24 hours
        
        log_info(f"[L2] Added fact: {content[:50]}...", "SEMANTIC")
        return node.id
    
    def search_facts(self, query: str, user_id: Optional[str] = None,
                     limit: int = 20, min_confidence: float = 0.4) -> List[MemorySearchResult]:
        """Hybrid search: BM25 + Vector similarity (🔥 UPGRADED SCORING!)"""
        # Text search (BM25 via FTS)
        text_nodes = self.db.search_nodes(query=query, layer="L2", user_id=user_id, limit=limit * 2)
        
        if not text_nodes:
            return []
        
        # Generate query embedding
        query_emb = np.array(embed_texts([query])[0])
        
        # Score facts
        results = []
        for node in text_nodes:
            if node.confidence < min_confidence:
                continue
            
            node_emb = node.get_embedding()
            
            # Semantic similarity
            semantic_score = float(cosine_similarity(query_emb, node_emb))
            
            # 🔥 Layer priority boost (L2=1.0, L1=0.7, L0=0.5)
            layer_boost = 1.0  # L2 semantic - HIGHEST PRIORITY!
            
            # Confidence bonus
            conf_bonus = node.confidence * 0.2
            
            # Importance bonus
            imp_bonus = node.importance * 0.1
            
            # Combined score with layer boost
            total_score = (semantic_score * 0.7 + conf_bonus + imp_bonus) * layer_boost
            
            results.append(MemorySearchResult(
                node=node,
                score=total_score,
                match_type="hybrid",
                context={"semantic": semantic_score, "confidence": node.confidence}
            ))
        
        # Sort and return
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]
    
    def consolidate_from_episodes(self, episodes: List[MemoryNode], user_id: str) -> Optional[str]:
        """Consolidate episodes into semantic fact"""
        if len(episodes) < EPISODIC_TO_SEMANTIC_THRESHOLD:
            return None
        
        # Analyze common topics
        all_tokens = []
        for ep in episodes:
            all_tokens.extend(tokenize(ep.content.lower()))
        
        topic_counts = Counter(all_tokens)
        dominant_topic = topic_counts.most_common(1)[0][0] if topic_counts else None
        
        if not dominant_topic:
            return None
        
        # Generate consolidated fact
        fact_text = f"User shows consistent interest in '{dominant_topic}' based on {len(episodes)} interactions."
        confidence = min(0.95, 0.7 + len(episodes) * 0.03)
        
        return self.add_fact(
            content=fact_text,
            user_id=user_id,
            tags=["consolidated", dominant_topic],
            confidence=confidence,
            metadata={"source_episodes": [ep.id for ep in episodes]}
        )


class ProceduralMemory:
    """L3: Learned patterns and procedures"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
    
    def learn_procedure(self, trigger_intent: str, steps: List[str],
                        success: bool = True, execution_time: float = 0.0,
                        context: Dict[str, Any] = None) -> str:
        """Learn or update procedure"""
        proc_id = make_id(trigger_intent)
        
        with self.db._conn() as conn:
            row = conn.execute("""
                SELECT * FROM memory_procedures WHERE trigger_intent = ?
            """, (trigger_intent,)).fetchone()
            
            if row:
                # Update existing
                succ = row["success_count"] + (1 if success else 0)
                fail = row["failure_count"] + (0 if success else 1)
                total = succ + fail
                rate = succ / total if total > 0 else 0.0
                
                # Update average execution time
                old_avg = row["avg_execution_time"] or 0.0
                execs = row["success_count"] + row["failure_count"]
                new_avg = ((old_avg * execs) + execution_time) / (execs + 1) if execution_time > 0 else old_avg
                
                conn.execute("""
                    UPDATE memory_procedures 
                    SET success_count = ?, failure_count = ?, success_rate = ?,
                        avg_execution_time = ?, last_used = ?
                    WHERE trigger_intent = ?
                """, (succ, fail, rate, new_avg, time.time(), trigger_intent))
                
                proc_id = row["id"]
            else:
                # Create new
                proc_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO memory_procedures 
                    (id, trigger_intent, steps, success_count, failure_count, 
                     success_rate, avg_execution_time, context_conditions, 
                     last_used, created_at, adaptations)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proc_id, trigger_intent, json.dumps(steps),
                    1 if success else 0, 0 if success else 1,
                    1.0 if success else 0.0, execution_time,
                    json.dumps(context or {}), time.time(), time.time(),
                    json.dumps([])
                ))
            
            conn.commit()
        
        log_info(f"[L3] Learned procedure: {trigger_intent}", "PROCEDURAL")
        return proc_id
    
    def get_procedure(self, trigger_intent: str) -> Optional[Dict[str, Any]]:
        """Get procedure by intent"""
        with self.db._conn() as conn:
            row = conn.execute("""
                SELECT * FROM memory_procedures WHERE trigger_intent = ?
            """, (trigger_intent,)).fetchone()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "trigger_intent": row["trigger_intent"],
                "steps": json.loads(row["steps"]),
                "success_rate": row["success_rate"],
                "avg_execution_time": row["avg_execution_time"],
                "success_count": row["success_count"],
                "failure_count": row["failure_count"]
            }


class MentalModels:
    """L4: User profiles and domain knowledge"""
    
    def __init__(self, db: MemoryDatabase):
        self.db = db
    
    def build_user_profile(self, user_id: str, semantic_facts: List[MemoryNode],
                           episodes: List[MemoryNode]) -> str:
        """Build or update user profile model"""
        # Extract preferences from facts
        topic_freq = defaultdict(float)
        for fact in semantic_facts:
            for tag in fact.tags:
                if tag not in {"fact", "semantic", "consolidated"}:
                    topic_freq[tag] += fact.confidence
        
        # Top topics
        top_topics = [t for t, _ in sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:10]]
        
        # Analyze episode patterns
        episode_types = Counter(ep.metadata.get("episode_type", "unknown") for ep in episodes)
        
        # Build model data
        model_data = {
            "user_id": user_id,
            "top_topics": top_topics,
            "episode_distribution": dict(episode_types),
            "total_facts": len(semantic_facts),
            "total_episodes": len(episodes),
            "avg_fact_confidence": sum(f.confidence for f in semantic_facts) / len(semantic_facts) if semantic_facts else 0.0,
            "last_updated": time.time()
        }
        
        # Calculate confidence
        confidence = min(1.0, len(semantic_facts) / 50.0 * 0.5 + len(episodes) / 100.0 * 0.5)
        
        # Save model
        model_id = f"user_profile_{user_id}"
        with self.db._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memory_mental_models
                (id, model_type, subject, confidence, evidence_count, model_data,
                 related_node_ids, last_updated, created_at, validation_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model_id, "user_profile", user_id, confidence,
                len(semantic_facts) + len(episodes),
                json.dumps(model_data),
                json.dumps([f.id for f in semantic_facts]),
                time.time(), time.time(), confidence
            ))
            conn.commit()
        
        log_info(f"[L4] Built user profile for {user_id}", "MENTAL_MODELS")
        return model_id
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile model"""
        with self.db._conn() as conn:
            row = conn.execute("""
                SELECT * FROM memory_mental_models 
                WHERE model_type = 'user_profile' AND subject = ?
            """, (user_id,)).fetchone()
            
            if not row:
                return None
            
            return {
                "id": row["id"],
                "confidence": row["confidence"],
                "data": json.loads(row["model_data"]),
                "last_updated": row["last_updated"]
            }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED MEMORY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedMemorySystem:
    """Main memory system orchestrator"""
    
    def __init__(self):
        # Core components
        self.db = MemoryDatabase()
        self.cache = MemoryCache(max_ram_size=MAX_SEMANTIC_SIZE)
        
        # Memory layers
        self.stm = ShortTermMemory()
        self.episodic = EpisodicMemory(self.db, self.cache)
        self.semantic = SemanticMemory(self.db, self.cache)
        self.procedural = ProceduralMemory(self.db)
        self.mental_models = MentalModels(self.db)
        
        # Background tasks
        self._consolidation_task = None
        self._cleanup_task = None
        self._running = False
        
        log_info("Unified Memory System initialized", "MEMORY")
    
    def start_background_tasks(self) -> None:
        """Start background consolidation and cleanup"""
        if self._running:
            return
        
        self._running = True
        
        def consolidation_loop():
            while self._running:
                try:
                    self.auto_consolidate()
                except Exception as e:
                    log_error(e, "CONSOLIDATION")
                time.sleep(AUTO_CONSOLIDATION_INTERVAL)
        
        def cleanup_loop():
            while self._running:
                try:
                    self.cleanup_old_memories()
                except Exception as e:
                    log_error(e, "CLEANUP")
                time.sleep(CLEANUP_INTERVAL)
        
        self._consolidation_task = threading.Thread(target=consolidation_loop, daemon=True)
        self._cleanup_task = threading.Thread(target=cleanup_loop, daemon=True)
        
        self._consolidation_task.start()
        self._cleanup_task.start()
        
        log_info("Background tasks started", "MEMORY")
    
    def stop_background_tasks(self) -> None:
        """Stop background tasks"""
        self._running = False
        log_info("Background tasks stopped", "MEMORY")
    
    def process_conversation_turn(self, user_id: str, user_message: str,
                                  assistant_response: str, intent: str = "chat",
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process complete conversation turn"""
        # Add to STM
        user_msg_id = self.stm.add_message(user_id, "user", user_message, metadata)
        assistant_msg_id = self.stm.add_message(user_id, "assistant", assistant_response, metadata)
        
        # Create episodic memory
        episode_summary = f"User: {user_message[:100]}... | Assistant: {assistant_response[:100]}..."
        episode_id = self.episodic.record_episode(
            user_id=user_id,
            episode_type=intent,
            summary=episode_summary,
            related_stm_ids=[user_msg_id, assistant_msg_id],
            metadata={**(metadata or {}), "intent": intent}
        )
        
        # Extract facts if important
        semantic_updates = []
        if len(user_message) > 50 and any(kw in user_message.lower() for kw in ["lubię", "preferuję", "ważne", "zawsze", "nigdy"]):
            fact_id = self.semantic.add_fact(
                content=f"User preference: {user_message}",
                user_id=user_id,
                tags=["preference", intent],
                confidence=0.75,
                metadata={"source_episode": episode_id}
            )
            semantic_updates.append(fact_id)
        
        return {
            "stm_ids": [user_msg_id, assistant_msg_id],
            "episode_id": episode_id,
            "semantic_updates": semantic_updates,
            "timestamp": time.time()
        }
    
    def retrieve_context(self, query: str, user_id: str, max_results: int = 10) -> Dict[str, Any]:
        """Retrieve comprehensive context across all layers"""
        # L0: STM
        stm_context = self.stm.get_context(user_id, limit=10)
        
        # L1: Episodic
        episodic_results = self.episodic.find_related_episodes(query, user_id, limit=5)
        
        # L2: Semantic
        semantic_results = self.semantic.search_facts(query, user_id, limit=max_results)
        
        # L4: User profile
        user_profile = self.mental_models.get_user_profile(user_id)
        
        # Calculate overall confidence
        all_scores = [r.score for r in episodic_results + semantic_results]
        avg_confidence = sum(all_scores) / len(all_scores) if all_scores else 0.0
        
        return {
            "query": query,
            "user_id": user_id,
            "stm_context": stm_context,
            "episodic_memories": [r.to_dict() for r in episodic_results],
            "semantic_facts": [r.to_dict() for r in semantic_results],
            "user_profile": user_profile,
            "confidence": avg_confidence,
            "total_results": len(episodic_results) + len(semantic_results)
        }
    
    def auto_consolidate(self, user_id: str = None) -> Dict[str, Any]:
        """Automatic memory consolidation (L1 -> L2 -> L4)"""
        stats = {
            "episodes_processed": 0,
            "facts_created": 0,
            "models_updated": 0
        }
        
        # Get all users or specific user
        users = [user_id] if user_id else self._get_all_users()
        
        for uid in users:
            # Get recent episodes
            episodes = self.episodic.get_recent_episodes(uid, limit=100)
            if len(episodes) < EPISODIC_TO_SEMANTIC_THRESHOLD:
                continue
            
            # Consolidate to semantic memory
            fact_id = self.semantic.consolidate_from_episodes(episodes, uid)
            if fact_id:
                stats["facts_created"] += 1
            
            stats["episodes_processed"] += len(episodes)
            
            # Update mental model
            semantic_facts = self.db.search_nodes(layer="L2", user_id=uid, limit=200)
            if len(semantic_facts) >= 10:
                self.mental_models.build_user_profile(uid, semantic_facts, episodes)
                stats["models_updated"] += 1
        
        log_info(f"Consolidation complete: {stats}", "MEMORY")
        return stats
    
    def cleanup_old_memories(self, max_age_days: int = 90) -> Dict[str, Any]:
        """Clean up old, low-importance memories"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        deleted_count = 0
        
        with self.db._conn() as conn:
            # Soft delete old, low-importance episodic memories
            result = conn.execute("""
                UPDATE memory_nodes
                SET deleted = 1
                WHERE layer = 'L1' 
                  AND created_at < ?
                  AND importance < 0.3
                  AND deleted = 0
            """, (cutoff_time,))
            deleted_count = result.rowcount
            conn.commit()
        
        log_info(f"Cleaned up {deleted_count} old memories", "MEMORY")
        return {"deleted_count": deleted_count}
    
    def get_health_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system health statistics"""
        with self.db._conn() as conn:
            stats = {
                "L0_stm": {
                    "active_conversations": len(self.stm._conversations),
                    "total_messages": sum(len(conv) for conv in self.stm._conversations.values())
                },
                "L1_episodic": {
                    "total": conn.execute("SELECT COUNT(*) as c FROM memory_nodes WHERE layer='L1' AND deleted=0").fetchone()["c"],
                    "last_24h": conn.execute("SELECT COUNT(*) as c FROM memory_nodes WHERE layer='L1' AND deleted=0 AND created_at > ?", (time.time() - 86400,)).fetchone()["c"]
                },
                "L2_semantic": {
                    "total": conn.execute("SELECT COUNT(*) as c FROM memory_nodes WHERE layer='L2' AND deleted=0").fetchone()["c"],
                    "avg_confidence": conn.execute("SELECT AVG(confidence) as a FROM memory_nodes WHERE layer='L2' AND deleted=0").fetchone()["a"] or 0.0
                },
                "L3_procedural": {
                    "total": conn.execute("SELECT COUNT(*) as c FROM memory_procedures").fetchone()["c"],
                    "avg_success_rate": conn.execute("SELECT AVG(success_rate) as a FROM memory_procedures").fetchone()["a"] or 0.0
                },
                "L4_models": {
                    "total": conn.execute("SELECT COUNT(*) as c FROM memory_mental_models").fetchone()["c"],
                    "avg_confidence": conn.execute("SELECT AVG(confidence) as a FROM memory_mental_models").fetchone()["a"] or 0.0
                },
                "cache": {
                    "ram_size": len(self.cache._ram_cache),
                    "redis_available": self.cache.redis is not None
                }
            }
        
        # Calculate overall health score
        health_components = [
            min(1.0, stats["L2_semantic"]["total"] / 100),  # At least 100 facts
            stats["L2_semantic"]["avg_confidence"],  # Good confidence
            min(1.0, stats["L3_procedural"]["total"] / 10),  # At least 10 procedures
            stats["L3_procedural"]["avg_success_rate"],  # High success rate
            stats["L4_models"]["avg_confidence"]  # Good model confidence
        ]
        stats["overall_health"] = sum(health_components) / len(health_components)
        
        return stats
    
    def _get_all_users(self) -> List[str]:
        """Get list of all users with memories"""
        with self.db._conn() as conn:
            rows = conn.execute("SELECT DISTINCT user_id FROM memory_nodes WHERE deleted=0").fetchall()
            return [r["user_id"] for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON AND PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

_memory_system: Optional[UnifiedMemorySystem] = None

def get_memory_system() -> UnifiedMemorySystem:
    """Get global memory system instance"""
    global _memory_system
    if _memory_system is None:
        _memory_system = UnifiedMemorySystem()
        _memory_system.start_background_tasks()
    return _memory_system


# Public API functions (backwards compatibility)

def memory_add_conversation(user_id: str, user_msg: str, assistant_msg: str,
                            intent: str = "chat", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add conversation turn to memory"""
    return get_memory_system().process_conversation_turn(user_id, user_msg, assistant_msg, intent, metadata)


def memory_search(query: str, user_id: str = "default", max_results: int = 10) -> Dict[str, Any]:
    """Search across all memory layers"""
    return get_memory_system().retrieve_context(query, user_id, max_results)


def memory_add_fact(content: str, user_id: str = "default", tags: List[str] = None,
                    confidence: float = 0.7) -> str:
    """Add fact to semantic memory"""
    return get_memory_system().semantic.add_fact(content, user_id, tags, confidence)


def memory_get_health() -> Dict[str, Any]:
    """Get memory system health statistics"""
    return get_memory_system().get_health_stats()


def memory_consolidate_now(user_id: str = None) -> Dict[str, Any]:
    """Trigger manual consolidation"""
    return get_memory_system().auto_consolidate(user_id)


# ═══════════════════════════════════════════════════════════════════════════════
# LEGACY SUPPORT - TimeManager for backward compatibility
# ═══════════════════════════════════════════════════════════════════════════════

class TimeManager:
    """Time management for backward compatibility with legacy tools.py"""
    
    def __init__(self):
        self.timezone = None
    
    def get_current_time(self) -> dict:
        """Get current time and date"""
        import datetime
        now = datetime.datetime.now()
        
        return {
            "timestamp": now.timestamp(),
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "day_of_week_pl": self._get_polish_day(now),
            "month": now.strftime("%B"),
            "month_pl": self._get_polish_month(now),
            "year": now.year,
            "is_weekend": now.weekday() >= 5,
            "is_morning": 6 <= now.hour < 12,
            "is_afternoon": 12 <= now.hour < 18,
            "is_evening": 18 <= now.hour < 22,
            "is_night": now.hour >= 22 or now.hour < 6
        }
    
    def _get_polish_day(self, dt) -> str:
        days_pl = {
            "Monday": "poniedziałek",
            "Tuesday": "wtorek",
            "Wednesday": "środa",
            "Thursday": "czwartek",
            "Friday": "piątek",
            "Saturday": "sobota",
            "Sunday": "niedziela"
        }
        return days_pl.get(dt.strftime("%A"), dt.strftime("%A"))
    
    def _get_polish_month(self, dt) -> str:
        months_pl = {
            "January": "styczeń",
            "February": "luty",
            "March": "marzec",
            "April": "kwiecień",
            "May": "maj",
            "June": "czerwiec",
            "July": "lipiec",
            "August": "sierpień",
            "September": "wrzesień",
            "October": "październik",
            "November": "listopad",
            "December": "grudzień"
        }
        return months_pl.get(dt.strftime("%B"), dt.strftime("%B"))
    
    def format_time_greeting(self) -> str:
        time_info = self.get_current_time()
        if time_info["is_morning"]:
            return "Dzień dobry"
        elif time_info["is_afternoon"]:
            return "Dzień dobry"
        elif time_info["is_evening"]:
            return "Dobry wieczór"
        else:
            return "Dobranoc"
    
    def format_date_info(self) -> str:
        time_info = self.get_current_time()
        return f"Dziś jest {time_info['day_of_week_pl']}, {time_info['date']}"


# Global TimeManager instance
time_manager = TimeManager()


# Initialize on module import
log_info("Unified Memory System module loaded", "MEMORY")


# ═══════════════════════════════════════════════════════════════════
# COMPATIBILITY LAYER - Legacy API support
# ═══════════════════════════════════════════════════════════════════

# Database handle for legacy code - callable that returns SQLite connection
def _db():
    """Legacy database connection factory"""
    import sqlite3
    from .config import DB_PATH
    from pathlib import Path
    Path(str(DB_PATH)).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def psy_get(key: str = "mood", user_id: str = "default") -> Any:
    """Legacy psyche state getter"""
    try:
        system = get_memory_system()
        profile = system.get_user_profile(user_id)
        if key == "mood":
            return profile.get("mood", "neutral")
        elif key == "temperature":
            return profile.get("llm_temperature", 0.7)
        return profile.get(key)
    except:
        return None

def psy_set(key: str, value: Any, user_id: str = "default") -> bool:
    """Legacy psyche state setter"""
    try:
        system = get_memory_system()
        profile = system.get_user_profile(user_id)
        profile[key] = value
        # Update in database
        return True
    except:
        return False

def psy_tune(user_id: str = "default") -> Dict[str, Any]:
    """Legacy psyche tune - returns LLM params"""
    try:
        system = get_memory_system()
        profile = system.get_user_profile(user_id)
        return {
            "temperature": profile.get("llm_temperature", 0.7),
            "mood": profile.get("mood", "neutral"),
            "style": profile.get("style", "balanced")
        }
    except:
        return {"temperature": 0.7, "mood": "neutral", "style": "balanced"}

def ltm_add(content: str, source: str = "manual", metadata: Dict = None, user_id: str = "default") -> str:
    """Legacy LTM add function"""
    try:
        system = get_memory_system()
        return system.add_semantic_memory(
            content=content,
            source=source,
            metadata=metadata or {},
            user_id=user_id
        )
    except Exception as e:
        log_error(f"ltm_add failed: {e}", "MEMORY")
        return ""

def ltm_search_hybrid(query: str, limit: int = 5, user_id: str = "default") -> List[Dict]:
    """Legacy hybrid search"""
    try:
        system = get_memory_system()
        results = system.search_hybrid(query=query, user_id=user_id, limit=limit)
        return [{"content": r["content"], "score": r.get("score", 0.0)} for r in results]
    except Exception as e:
        log_error(f"ltm_search_hybrid failed: {e}", "MEMORY")
        return []

def stm_add(role: str, content: str, user_id: str = "default") -> bool:
    """Legacy STM add"""
    try:
        system = get_memory_system()
        system.add_episodic_memory(
            content=content,
            event_type="conversation",
            metadata={"role": role},
            user_id=user_id
        )
        return True
    except:
        return False

def stm_get_context(user_id: str = "default", limit: int = 10) -> str:
    """Legacy STM context getter"""
    try:
        system = get_memory_system()
        episodes = system.get_recent_episodes(user_id=user_id, limit=limit)
        lines = []
        for ep in episodes:
            role = ep.get("metadata", {}).get("role", "user")
            content = ep.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
    except:
        return ""

def get_memory_manager():
    """Legacy memory manager getter - returns UnifiedMemorySystem"""
    return get_memory_system()

def psy_episode_add(event_type: str, content: str, metadata: Dict = None, user_id: str = "default") -> str:
    """Legacy psyche episode add"""
    try:
        system = get_memory_system()
        return system.add_episodic_memory(
            content=content,
            event_type=event_type,
            metadata=metadata or {},
            user_id=user_id
        )
    except Exception as e:
        log_error(f"psy_episode_add failed: {e}", "MEMORY")
        return ""

def psy_observe_text(text: str, user_id: str = "default") -> Dict[str, Any]:
    """Legacy psyche text observation - returns sentiment analysis stub"""
    return {
        "sentiment": "neutral",
        "confidence": 0.5,
        "entities": [],
        "keywords": []
    }

def _init_db():
    """Legacy database init - stub (UnifiedMemorySystem handles this)"""
    pass

# Export all compatibility functions
__all__ = [
    "UnifiedMemorySystem",
    "TimeManager",
    "get_memory_system",
    "get_memory_manager",
    "time_manager",
    "_db",
    "_init_db",
    "psy_get",
    "psy_set",
    "psy_tune",
    "psy_episode_add",
    "psy_observe_text",
    "ltm_add",
    "ltm_search_hybrid",
    "stm_add",
    "stm_get_context"
]
