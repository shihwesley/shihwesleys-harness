#!/usr/bin/env python3
"""
Backport Learnings - Auto-route high-scoring learnings to skill files.

Selects learnings with quality_score >= threshold and primary_skill set,
appends them to the corresponding skill file with markers, and logs the action.

Usage:
  backport-learnings.py              # Run backport
  backport-learnings.py --dry-run    # Show what would be backported
  backport-learnings.py --threshold 6  # Custom score threshold (default: 6)

Location: /Users/quartershots/Source/.claude/scripts/backport-learnings.py
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_DIR = Path("/Users/quartershots/Source/.claude")
DB_PATH = CLAUDE_DIR / "cache" / "learnings.db"

# Default score threshold for backport
DEFAULT_THRESHOLD = 6.0
# Higher threshold for learnings without a primary_skill (→ CLAUDE.md)
GENERIC_THRESHOLD = 8.0

# Only backport these categories (gotcha and learning are most actionable)
BACKPORT_CATEGORIES = {"gotcha", "learning"}

# Minimum content length for backport (filter low-quality)
MIN_CONTENT_LENGTH = 50

# Section header for auto-learned notes in skill files
SECTION_HEADER = "## Auto-Learned Notes\n<!-- self-learn:section — auto-managed, do not edit above this line -->"

# CLAUDE.md section header
CLAUDE_MD_SECTION_HEADER = "## Auto-Learned\n<!-- self-learn:section — auto-managed, do not edit above this line -->"

# Project-level CLAUDE.md for generic backports
CLAUDE_MD_PATH = Path("/Users/quartershots/Source/CLAUDE.md")


def find_skill_file(skill_name):
    """Find the skill file path for a given skill name."""
    candidates = [
        CLAUDE_DIR / "skills" / f"{skill_name}.md",
        CLAUDE_DIR / "skills" / skill_name / "SKILL.md",
        CLAUDE_DIR / "commands" / f"{skill_name}.md",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def format_backport_block(learning_id, content, score):
    """Format a backport block with markers."""
    date = datetime.now().strftime("%Y-%m-%d")
    return f"""
<!-- self-learn:backport:start id=learning_{learning_id} score={score:.1f} date={date} -->
> **Learned:** {content}
<!-- self-learn:backport:end -->"""


def is_already_backported_in_file(file_path, learning_id):
    """Check if a learning has already been backported to this file."""
    if not file_path.exists():
        return False
    content = file_path.read_text()
    return f"id=learning_{learning_id}" in content


def append_to_skill_file(file_path, backport_block):
    """Append a backport block to a skill file, creating section header if needed."""
    content = file_path.read_text()

    if "<!-- self-learn:section" in content:
        # Section exists — append after last backport block or after section header
        content = content.rstrip() + "\n" + backport_block + "\n"
    else:
        # First backport — add section header at the end
        content = content.rstrip() + "\n\n" + SECTION_HEADER + "\n" + backport_block + "\n"

    file_path.write_text(content)


def append_to_claude_md(backport_block):
    """Append a backport block to the project CLAUDE.md."""
    if not CLAUDE_MD_PATH.exists():
        return False

    content = CLAUDE_MD_PATH.read_text()

    if "<!-- self-learn:section" in content:
        content = content.rstrip() + "\n" + backport_block + "\n"
    else:
        content = content.rstrip() + "\n\n" + CLAUDE_MD_SECTION_HEADER + "\n" + backport_block + "\n"

    CLAUDE_MD_PATH.write_text(content)
    return True


def get_candidates(conn, threshold):
    """Get backport candidates: high score, not yet backported, right category."""
    cursor = conn.execute(
        """
        SELECT id, category, content, quality_score, primary_skill
        FROM learnings
        WHERE quality_score >= ?
          AND backported = 0
          AND category IN (?, ?)
          AND length(content) >= ?
        ORDER BY quality_score DESC
        """,
        (threshold, "gotcha", "learning", MIN_CONTENT_LENGTH),
    )
    return cursor.fetchall()


def emit_signal(conn, learning_id, signal_type, context=None):
    """Emit a signal for a learning."""
    ctx_json = json.dumps(context) if context else None
    try:
        conn.execute(
            "INSERT INTO learning_signals (learning_id, signal_type, session_id, context) VALUES (?, ?, ?, ?)",
            (learning_id, signal_type, "backport", ctx_json),
        )
    except Exception:
        pass


def main():
    if not DB_PATH.exists():
        print("No learnings database found", file=sys.stderr)
        sys.exit(1)

    # Parse args
    dry_run = "--dry-run" in sys.argv
    threshold = DEFAULT_THRESHOLD
    for i, arg in enumerate(sys.argv):
        if arg == "--threshold" and i + 1 < len(sys.argv):
            threshold = float(sys.argv[i + 1])

    conn = sqlite3.connect(DB_PATH)

    # Get all candidates (using lower threshold to catch both skill-tagged and generic)
    candidates = get_candidates(conn, min(threshold, GENERIC_THRESHOLD))

    if not candidates:
        print("No backport candidates found", file=sys.stderr)
        conn.close()
        return

    backported = 0
    skipped = 0

    for row in candidates:
        learning_id, category, content, score, primary_skill = row

        # Determine target
        if primary_skill:
            if score < threshold:
                continue
            target_file = find_skill_file(primary_skill)
            if not target_file:
                skipped += 1
                continue
            target_label = str(target_file.relative_to(CLAUDE_DIR))
        else:
            # Generic: needs higher threshold
            if score < GENERIC_THRESHOLD:
                continue
            target_file = CLAUDE_MD_PATH
            target_label = "CLAUDE.md"

        # Check if already in file (safety check beyond DB flag)
        if is_already_backported_in_file(target_file, learning_id):
            conn.execute("UPDATE learnings SET backported = 1 WHERE id = ?", (learning_id,))
            continue

        block = format_backport_block(learning_id, content, score)

        if dry_run:
            print(f"  Would backport #{learning_id} (score={score:.1f}) → {target_label}")
            print(f"    [{category}] {content[:100]}")
            print()
            continue

        # Perform backport
        try:
            if primary_skill:
                append_to_skill_file(target_file, block)
            else:
                if not append_to_claude_md(block):
                    skipped += 1
                    continue

            # Log to backport_log
            conn.execute(
                "INSERT INTO backport_log (learning_id, target_file, content_added, score_at_backport) VALUES (?, ?, ?, ?)",
                (learning_id, str(target_file), block, score),
            )

            # Mark as backported
            conn.execute("UPDATE learnings SET backported = 1 WHERE id = ?", (learning_id,))

            # Emit applied signal
            emit_signal(conn, learning_id, "applied", {"target": str(target_file)})

            backported += 1
            print(f"  Backported #{learning_id} → {target_label}", file=sys.stderr)

        except Exception as e:
            print(f"  Error backporting #{learning_id}: {e}", file=sys.stderr)
            skipped += 1

    conn.commit()
    conn.close()

    if dry_run:
        print(f"Dry run complete: {len(candidates)} candidates evaluated")
    else:
        print(f"Backported: {backported}, Skipped: {skipped}", file=sys.stderr)


if __name__ == "__main__":
    main()
