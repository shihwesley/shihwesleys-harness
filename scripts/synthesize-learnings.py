#!/usr/bin/env python3
"""
Synthesize Learnings - Aggregates data from learnings.db for LLM synthesis.

Uses quality scores (from score-learnings.py) to rank learnings by importance
rather than just recency. Emits 'recalled' signals for learnings cited in output.

Location: /Users/quartershots/Source/.claude/scripts/synthesize-learnings.py
"""

import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

CLAUDE_DIR = Path("/Users/quartershots/Source/.claude")
CACHE_DIR = CLAUDE_DIR / "cache"
DB_PATH = CACHE_DIR / "learnings.db"
LAST_SYNTHESIS_FILE = CACHE_DIR / "last-synthesis"
MEMORY_FILE = CLAUDE_DIR / "projects" / "-Users-quartershots-Source" / "memory" / "MEMORY.md"
SCRIPTS_DIR = CLAUDE_DIR / "scripts"

# Minimum threshold to trigger synthesis
MIN_NEW_LEARNINGS = 5


def get_last_synthesis_time():
    """Get timestamp of last synthesis run."""
    if LAST_SYNTHESIS_FILE.exists():
        try:
            return int(LAST_SYNTHESIS_FILE.read_text().strip())
        except (ValueError, IOError):
            pass
    return 0


def count_new_learnings(conn, since_timestamp):
    """Count learnings since last synthesis."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM learnings WHERE strftime('%s', created_at) > ?",
        (since_timestamp,)
    )
    return cursor.fetchone()[0]


def should_synthesize(conn):
    """Check if we have enough new data to warrant synthesis."""
    last_time = get_last_synthesis_time()
    new_count = count_new_learnings(conn, last_time)
    return new_count >= MIN_NEW_LEARNINGS, new_count


def refresh_scores():
    """Run score-learnings.py to recompute all quality scores."""
    score_script = SCRIPTS_DIR / "score-learnings.py"
    if score_script.exists():
        try:
            subprocess.run(
                [sys.executable, str(score_script)],
                capture_output=True, timeout=30
            )
        except (subprocess.TimeoutExpired, Exception):
            pass


def get_top_learnings(conn, limit=20):
    """Get top learnings ranked by quality_score (not just recency)."""
    cursor = conn.execute(
        """
        SELECT id, category, content, quality_score, primary_skill
        FROM learnings
        ORDER BY quality_score DESC, created_at DESC
        LIMIT ?
        """,
        (limit,)
    )
    return [
        {
            "id": row[0],
            "category": row[1],
            "content": row[2],
            "score": row[3],
            "skill": row[4],
        }
        for row in cursor.fetchall()
    ]


def aggregate_tool_stats(conn):
    """Aggregate tool usage and failure patterns."""
    cursor = conn.execute(
        """
        SELECT tool_name, COUNT(*) as count
        FROM tool_failures
        GROUP BY tool_name
        ORDER BY count DESC
        LIMIT 10
        """
    )
    tool_failures = {row[0]: row[1] for row in cursor.fetchall()}

    cursor = conn.execute(
        """
        SELECT
            COUNT(*) as sessions,
            SUM(tool_calls) as total_tool_calls,
            SUM(tool_errors) as total_tool_errors,
            AVG(assistant_messages) as avg_assistant_msgs
        FROM session_stats
        """
    )
    row = cursor.fetchone()
    session_stats = {
        "sessions": row[0] or 0,
        "total_tool_calls": row[1] or 0,
        "total_tool_errors": row[2] or 0,
        "avg_assistant_msgs": round(row[3] or 0, 1),
    }

    return {"tool_failures": tool_failures, "session_stats": session_stats}


def format_synthesis_prompt(top_learnings, tool_stats):
    """Format the prompt for Claude to synthesize insights. Includes scores for prioritization."""
    prompt = """You are a helpful assistant generating a markdown document. Your task is to analyze the following data and output ONLY a markdown document in the exact format specified below. Do not include any conversational text, explanations, or meta-commentary - ONLY output the markdown.

Prioritize high-scoring learnings. Score reflects how often this learning has been reinforced and applied across sessions.

# Input Data: Top Learnings (ranked by quality score)
"""

    # Group by category, include score
    by_category = {}
    for item in top_learnings:
        cat = item["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for cat, items in by_category.items():
        prompt += f"\n### {cat.upper()}S\n"
        for item in items[:7]:  # Limit per category
            score = item["score"]
            skill_tag = f" [{item['skill']}]" if item.get("skill") else ""
            prompt += f"- (score:{score:.1f}{skill_tag}) {item['content'][:150]}\n"

    # Add tool stats
    prompt += f"""
## Tool Statistics
- Sessions analyzed: {tool_stats['session_stats']['sessions']}
- Total tool calls: {tool_stats['session_stats']['total_tool_calls']}
- Total tool errors: {tool_stats['session_stats']['total_tool_errors']}
"""

    if tool_stats["tool_failures"]:
        prompt += "\n### Tool Failures by Type\n"
        for tool, count in list(tool_stats["tool_failures"].items())[:5]:
            prompt += f"- {tool}: {count} failures\n"

    prompt += f"""
## Instructions

Analyze the data above and output ONLY the following markdown document. Replace bracketed placeholders with specific, actionable insights based on the data. Output nothing else - no explanations, no conversation.

# Self-Learning Insights

Last updated: {datetime.now().strftime('%Y-%m-%d')}

## Top Patterns
- [3-5 specific patterns from the learnings above, favoring high-score items]

## Common Pitfalls
- [3-5 specific mistakes to avoid, based on gotchas and errors above]

## Workflow Recommendations
- [2-3 specific process improvements based on the pivots and decisions]

## Tool Notes
- [2-3 notes about tool performance based on the tool statistics]
"""

    return prompt


def emit_recalled_signals(conn, top_learnings, synthesis_output):
    """Emit 'recalled' signal for learnings whose content appears in the synthesis output."""
    if not synthesis_output:
        return 0

    output_lower = synthesis_output.lower()
    recalled = 0

    for item in top_learnings:
        # Check if a meaningful substring of the learning appears in the output
        content = item["content"]
        # Use first 40 chars as a fingerprint (long enough to be unique, short enough to match)
        fingerprint = content[:40].lower().strip()
        # Also check for key phrases (words longer than 5 chars)
        key_words = [w for w in content.lower().split() if len(w) > 5]

        matched = False
        if fingerprint in output_lower:
            matched = True
        elif len(key_words) >= 2:
            # If at least 2 key words appear near each other in output
            matches = sum(1 for w in key_words[:4] if w in output_lower)
            if matches >= 2:
                matched = True

        if matched:
            try:
                conn.execute(
                    "INSERT INTO learning_signals (learning_id, signal_type, session_id, context) VALUES (?, ?, ?, ?)",
                    (item["id"], "recalled", "synthesis", json.dumps({"source": "synthesis"})),
                )
                recalled += 1
            except Exception:
                pass

    conn.commit()
    return recalled


def main():
    """Main entry point."""
    if not DB_PATH.exists():
        print("No learnings database found", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)

    # Check if we should run
    should_run, new_count = should_synthesize(conn)

    if "--force" not in sys.argv and not should_run:
        print(f"Only {new_count} new learnings (threshold: {MIN_NEW_LEARNINGS}). Skipping.", file=sys.stderr)
        sys.exit(0)

    # Refresh quality scores before synthesis
    refresh_scores()

    # Get top learnings by score (not just recency)
    top_learnings = get_top_learnings(conn, limit=20)
    tool_stats = aggregate_tool_stats(conn)

    conn.close()

    if not top_learnings:
        print("No learnings to synthesize", file=sys.stderr)
        sys.exit(0)

    # Generate prompt
    prompt = format_synthesis_prompt(top_learnings, tool_stats)

    # Output mode
    if "--prompt-only" in sys.argv:
        print(prompt)
    elif "--stats" in sys.argv:
        print(json.dumps({
            "new_learnings": new_count,
            "total_top": len(top_learnings),
            "categories": list(set(l["category"] for l in top_learnings)),
            "tool_failures": tool_stats["tool_failures"],
            "session_stats": tool_stats["session_stats"],
            "top_scores": [l["score"] for l in top_learnings[:5]],
        }, indent=2))
    elif "--emit-recalled" in sys.argv:
        # Called by self-learn.sh after synthesis to emit recalled signals
        # Reads synthesis output from stdin
        synthesis_output = sys.stdin.read()
        conn2 = sqlite3.connect(DB_PATH)
        recalled = emit_recalled_signals(conn2, top_learnings, synthesis_output)
        conn2.close()
        print(f"Emitted {recalled} recalled signals", file=sys.stderr)
    else:
        print(prompt)


if __name__ == "__main__":
    main()
