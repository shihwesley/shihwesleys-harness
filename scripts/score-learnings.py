#!/usr/bin/env python3
"""
Score Learnings - Computes quality scores from signal stream.

Reads learning_signals, applies weights + time decay, caches result
in learnings.quality_score for fast querying.

Usage:
  score-learnings.py                    # Update all scores
  score-learnings.py --top 20           # Print top 20 by score
  score-learnings.py --threshold 4      # Print only score >= 4
  score-learnings.py --json             # Output as JSON

Location: /Users/quartershots/Source/.claude/scripts/score-learnings.py
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_DIR = Path("/Users/quartershots/Source/.claude")
DB_PATH = CLAUDE_DIR / "cache" / "learnings.db"

# Signal weights (must match extract-learnings.py)
SIGNAL_WEIGHTS = {
    "extracted": 1,
    "reinforced": 2,
    "recalled": 2,
    "corrected": 3,
    "applied": 3,
}

# Decay: -0.5 per 30 days since last signal
DECAY_PER_30_DAYS = 0.5


def compute_scores(conn):
    """Compute quality score for every learning based on its signals."""
    cursor = conn.execute("""
        SELECT l.id,
               GROUP_CONCAT(s.signal_type, ',') as signal_types,
               MAX(s.created_at) as last_signal
        FROM learnings l
        LEFT JOIN learning_signals s ON l.id = s.learning_id
        GROUP BY l.id
    """)

    now = datetime.now()
    updates = []

    for row in cursor.fetchall():
        learning_id = row[0]
        signal_types_str = row[1] or ""
        last_signal_str = row[2]

        # Sum signal weights
        raw_score = 0
        if signal_types_str:
            for sig_type in signal_types_str.split(","):
                raw_score += SIGNAL_WEIGHTS.get(sig_type.strip(), 0)

        # Time decay based on last signal
        decay = 0
        if last_signal_str:
            try:
                last_signal = datetime.fromisoformat(last_signal_str)
                days_since = (now - last_signal).days
                months_since = days_since / 30.0
                decay = DECAY_PER_30_DAYS * months_since
            except (ValueError, TypeError):
                pass

        score = max(0, raw_score - decay)
        updates.append((score, learning_id))

    # Batch update
    conn.executemany("UPDATE learnings SET quality_score = ? WHERE id = ?", updates)
    conn.commit()

    return len(updates)


def get_ranked_learnings(conn, top_n=None, threshold=None):
    """Get learnings ranked by quality_score."""
    query = """
        SELECT l.id, l.category, l.content, l.quality_score, l.primary_skill,
               l.backported, l.created_at,
               (SELECT COUNT(*) FROM learning_signals s WHERE s.learning_id = l.id) as signal_count
        FROM learnings l
    """
    params = []

    if threshold is not None:
        query += " WHERE l.quality_score >= ?"
        params.append(threshold)

    query += " ORDER BY l.quality_score DESC"

    if top_n:
        query += " LIMIT ?"
        params.append(top_n)

    cursor = conn.execute(query, params)
    return cursor.fetchall()


def main():
    if not DB_PATH.exists():
        print("No learnings database found", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Always recompute scores first
    updated = compute_scores(conn)
    print(f"Updated {updated} learning scores", file=sys.stderr)

    # Parse args
    top_n = None
    threshold = None
    as_json = "--json" in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--top" and i + 1 < len(sys.argv):
            top_n = int(sys.argv[i + 1])
        elif arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = float(sys.argv[i + 1])

    # If no display flags, just update and exit
    if top_n is None and threshold is None and not as_json:
        conn.close()
        return

    rows = get_ranked_learnings(conn, top_n=top_n, threshold=threshold)
    conn.close()

    if as_json:
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "category": row[1],
                "content": row[2],
                "score": row[3],
                "primary_skill": row[4],
                "backported": bool(row[5]),
                "created_at": row[6],
                "signal_count": row[7],
            })
        print(json.dumps(result, indent=2))
    else:
        for row in rows:
            lid, cat, content, score, skill, bp, created, signals = row
            skill_tag = f" [{skill}]" if skill else ""
            bp_tag = " (backported)" if bp else ""
            print(f"  #{lid} [{cat}] score={score:.1f} signals={signals}{skill_tag}{bp_tag}")
            print(f"    {content[:120]}")
            print()


if __name__ == "__main__":
    main()
