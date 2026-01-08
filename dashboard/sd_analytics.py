#!/usr/bin/env python3
"""
SD Studio Analytics - SQLite tracking for image generation metrics.

Tracks:
- Sessions (VM runtime, total images, cost)
- Individual generations (model, resolution, steps, duration)
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

DB_PATH = Path.home() / ".config" / "sd-studio" / "analytics.db"
COST_PER_HOUR = 0.45  # GCP T4 GPU cost


def get_db() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        total_images INTEGER DEFAULT 0,
        total_pixels BIGINT DEFAULT 0,
        total_steps BIGINT DEFAULT 0,
        total_duration_ms BIGINT DEFAULT 0,
        runtime_seconds INTEGER DEFAULT 0,
        estimated_cost_usd REAL DEFAULT 0,
        vm_name TEXT,
        gpu_type TEXT DEFAULT 'NVIDIA T4',
        note TEXT
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS generations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        created_at TEXT NOT NULL,
        model TEXT,
        width INTEGER,
        height INTEGER,
        steps INTEGER,
        cfg_scale REAL,
        sampler TEXT,
        batch_size INTEGER DEFAULT 1,
        duration_ms INTEGER,
        seed INTEGER,
        prompt TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_generations_session 
    ON generations(session_id)
    """)
    
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_generations_created 
    ON generations(created_at)
    """)
    
    conn.commit()
    conn.close()


def start_session(vm_name: str = "sd-server", gpu_type: str = "NVIDIA T4") -> int:
    """Start a new session, returns session ID."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO sessions (started_at, vm_name, gpu_type)
    VALUES (?, ?, ?)
    """, (datetime.now().isoformat(), vm_name, gpu_type))
    
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def end_session(session_id: int, runtime_seconds: int = 0):
    """End a session and calculate cost."""
    conn = get_db()
    cur = conn.cursor()
    
    runtime_hours = runtime_seconds / 3600
    estimated_cost = runtime_hours * COST_PER_HOUR
    
    cur.execute("""
    UPDATE sessions 
    SET ended_at = ?, runtime_seconds = ?, estimated_cost_usd = ?
    WHERE id = ?
    """, (datetime.now().isoformat(), runtime_seconds, estimated_cost, session_id))
    
    conn.commit()
    conn.close()


def get_current_session() -> Optional[Dict[str, Any]]:
    """Get the current open session (no ended_at)."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM sessions 
    WHERE ended_at IS NULL 
    ORDER BY id DESC LIMIT 1
    """)
    
    row = cur.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def track_generation(
    session_id: int,
    model: str,
    width: int,
    height: int,
    steps: int,
    batch_size: int = 1,
    duration_ms: int = 0,
    seed: int = -1,
    cfg_scale: float = 7.0,
    sampler: str = "",
    prompt: str = ""
):
    """Track a single generation event."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO generations 
    (session_id, created_at, model, width, height, steps, cfg_scale, sampler, batch_size, duration_ms, seed, prompt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        datetime.now().isoformat(),
        model,
        width,
        height,
        steps,
        cfg_scale,
        sampler,
        batch_size,
        duration_ms,
        seed,
        prompt[:500] if prompt else ""
    ))
    
    pixels = width * height * batch_size
    step_count = steps * batch_size
    
    cur.execute("""
    UPDATE sessions SET
        total_images = total_images + ?,
        total_pixels = total_pixels + ?,
        total_steps = total_steps + ?,
        total_duration_ms = total_duration_ms + ?
    WHERE id = ?
    """, (batch_size, pixels, step_count, duration_ms, session_id))
    
    conn.commit()
    conn.close()


def get_session_stats(session_id: int) -> Dict[str, Any]:
    """Get stats for a specific session."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = cur.fetchone()
    
    if not session:
        conn.close()
        return {}
    
    session_dict = dict(session)
    
    total_images = session_dict.get("total_images", 0)
    total_duration_ms = session_dict.get("total_duration_ms", 0)
    
    if total_images > 0:
        session_dict["avg_duration_ms"] = total_duration_ms / total_images
        session_dict["avg_seconds_per_image"] = (total_duration_ms / 1000) / total_images
    else:
        session_dict["avg_duration_ms"] = 0
        session_dict["avg_seconds_per_image"] = 0
    
    conn.close()
    return session_dict


def get_all_time_stats() -> Dict[str, Any]:
    """Get aggregate stats across all sessions."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT 
        COUNT(*) as total_sessions,
        COALESCE(SUM(total_images), 0) as total_images,
        COALESCE(SUM(total_pixels), 0) as total_pixels,
        COALESCE(SUM(total_steps), 0) as total_steps,
        COALESCE(SUM(total_duration_ms), 0) as total_duration_ms,
        COALESCE(SUM(runtime_seconds), 0) as total_runtime_seconds,
        COALESCE(SUM(estimated_cost_usd), 0) as total_cost_usd
    FROM sessions
    """)
    
    stats = dict(cur.fetchone())
    
    if stats["total_images"] > 0:
        stats["avg_seconds_per_image"] = (stats["total_duration_ms"] / 1000) / stats["total_images"]
    else:
        stats["avg_seconds_per_image"] = 0
    
    cur.execute("""
    SELECT model, COUNT(*) as count
    FROM generations
    WHERE model IS NOT NULL AND model != ''
    GROUP BY model
    ORDER BY count DESC
    LIMIT 5
    """)
    stats["top_models"] = [{"model": row["model"], "count": row["count"]} for row in cur.fetchall()]
    
    cur.execute("""
    SELECT sampler, COUNT(*) as count
    FROM generations
    WHERE sampler IS NOT NULL AND sampler != ''
    GROUP BY sampler
    ORDER BY count DESC
    LIMIT 5
    """)
    stats["top_samplers"] = [{"sampler": row["sampler"], "count": row["count"]} for row in cur.fetchall()]
    
    conn.close()
    return stats


def get_recent_sessions(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent sessions for history view."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM sessions
    ORDER BY started_at DESC
    LIMIT ?
    """, (limit,))
    
    sessions = [dict(row) for row in cur.fetchall()]
    conn.close()
    return sessions


def get_recent_generations(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent generations for gallery metadata."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT * FROM generations
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))
    
    generations = [dict(row) for row in cur.fetchall()]
    conn.close()
    return generations


def get_daily_stats(days: int = 7) -> List[Dict[str, Any]]:
    """Get daily aggregated stats for charts."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as generations,
        SUM(batch_size) as images,
        SUM(duration_ms) as duration_ms
    FROM generations
    WHERE created_at >= DATE('now', ?)
    GROUP BY DATE(created_at)
    ORDER BY date ASC
    """, (f'-{days} days',))
    
    stats = [dict(row) for row in cur.fetchall()]
    conn.close()
    return stats


init_db()
