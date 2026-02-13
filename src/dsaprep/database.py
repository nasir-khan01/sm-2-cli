"""
Database module for DSAPrep.

Handles SQLite operations for storing and retrieving problem data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional
from dataclasses import dataclass


# Database location
DB_DIR = Path.home() / ".dsaprep"
DB_PATH = DB_DIR / "study.db"

# Default patterns (NeetCode order)
PATTERN_ORDER = [
    "Arrays & Hashing",
    "Two Pointers",
    "Sliding Window",
    "Stack",
    "Binary Search",
    "Linked Lists",
    "Trees",
    "Tries",
    "Heap / Priority Queue",
    "Backtracking",
    "Graphs",
    "1-D Dynamic Programming",
    "2-D Dynamic Programming",
    "Greedy",
    "Intervals",
    "Math & Geometry",
    "Bit Manipulation",
]

# For backwards compatibility
DEFAULT_PATTERNS = PATTERN_ORDER


@dataclass
class Problem:
    """Represents a DSA problem."""
    id: int
    name: str
    url: str
    category: str
    difficulty: str
    pattern: str
    source_list: str
    repetition: int
    ease_factor: float
    interval: int
    next_review: Optional[date]
    last_reviewed: Optional[date]
    times_solved: int


def get_connection() -> sqlite3.Connection:
    """Get database connection, creating directory if needed."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema with migration support."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT,
            difficulty TEXT,
            pattern TEXT DEFAULT 'General',
            source_list TEXT DEFAULT 'Blind 75',
            repetition INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            next_review DATE,
            last_reviewed DATE,
            times_solved INTEGER DEFAULT 0
        )
    """)
    
    # Migration: Add pattern column if missing
    cursor.execute("PRAGMA table_info(problems)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'pattern' not in columns:
        cursor.execute("ALTER TABLE problems ADD COLUMN pattern TEXT DEFAULT 'General'")
    
    if 'source_list' not in columns:
        cursor.execute("ALTER TABLE problems ADD COLUMN source_list TEXT DEFAULT 'Blind 75'")
    
    conn.commit()
    conn.close()


def seed_problems(data: list[dict], source_list: str = "Blind 75") -> int:
    """
    Seed the database with problems.
    
    Args:
        data: List of problem dictionaries with keys:
              name, url, category, difficulty, pattern
        source_list: The source list name (default: "Blind 75")
    
    Returns:
        Number of problems inserted
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clear existing data for this source list only
    cursor.execute("DELETE FROM problems WHERE source_list = ?", (source_list,))
    
    for problem in data:
        cursor.execute("""
            INSERT INTO problems (name, url, category, difficulty, pattern, source_list)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            problem.get('name', 'Unknown'),
            problem.get('url', ''),
            problem.get('category', 'General'),
            problem.get('difficulty', 'Medium'),
            problem.get('pattern', _infer_pattern(problem.get('category', 'General'))),
            source_list
        ))
    
    conn.commit()
    conn.close()
    
    return len(data)


def add_problem(
    name: str,
    url: str,
    pattern: str,
    source_list: str,
    difficulty: str = "Medium",
    category: str = ""
) -> int:
    """
    Add a single problem to the database.
    
    Returns:
        The ID of the newly inserted problem
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO problems (name, url, category, difficulty, pattern, source_list)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, url, category or pattern, difficulty, pattern, source_list))
    
    problem_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return problem_id


def get_all_problems(source_list: Optional[str] = None) -> list[Problem]:
    """Retrieve all problems, optionally filtered by source list."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if source_list:
        cursor.execute(
            "SELECT * FROM problems WHERE source_list = ? ORDER BY id",
            (source_list,)
        )
    else:
        cursor.execute("SELECT * FROM problems ORDER BY id")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_problem(row) for row in rows]


def get_problems_by_pattern(pattern: str, source_list: Optional[str] = None) -> list[Problem]:
    """Retrieve problems by pattern, optionally filtered by source list."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if source_list:
        cursor.execute(
            "SELECT * FROM problems WHERE pattern = ? AND source_list = ? ORDER BY id",
            (pattern, source_list)
        )
    else:
        cursor.execute(
            "SELECT * FROM problems WHERE pattern = ? ORDER BY id",
            (pattern,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_problem(row) for row in rows]


def get_all_patterns(source_list: Optional[str] = None) -> list[str]:
    """Get all unique patterns in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if source_list:
        cursor.execute(
            "SELECT DISTINCT pattern FROM problems WHERE source_list = ? ORDER BY pattern",
            (source_list,)
        )
    else:
        cursor.execute("SELECT DISTINCT pattern FROM problems ORDER BY pattern")
    
    patterns = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return patterns


def get_all_lists() -> list[str]:
    """Get all unique source lists in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT source_list FROM problems ORDER BY source_list")
    lists = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return lists


def get_problem_by_id(problem_id: int) -> Optional[Problem]:
    """Retrieve a specific problem by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM problems WHERE id = ?", (problem_id,))
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_problem(row) if row else None


def get_next_problem(source_list: Optional[str] = None) -> Optional[Problem]:
    """
    Get the next problem to review.
    
    Priority:
    1. Most overdue problem (next_review in the past)
    2. Problem due today
    3. New problem never reviewed
    """
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    
    list_filter = "AND source_list = ?" if source_list else ""
    params = (today, source_list) if source_list else (today,)
    
    # First: most overdue problem
    cursor.execute(f"""
        SELECT * FROM problems 
        WHERE next_review IS NOT NULL AND next_review <= ? {list_filter}
        ORDER BY next_review ASC
        LIMIT 1
    """, params)
    row = cursor.fetchone()
    
    if not row:
        # Second: new problem never reviewed
        params = (source_list,) if source_list else ()
        cursor.execute(f"""
            SELECT * FROM problems 
            WHERE next_review IS NULL {list_filter.replace('AND', 'AND' if source_list else '')}
            ORDER BY id ASC
            LIMIT 1
        """.replace(list_filter.replace('AND', 'AND' if source_list else ''), 
                    f"AND source_list = ?" if source_list else ""), 
            params if source_list else ())
        row = cursor.fetchone()
    
    conn.close()
    return _row_to_problem(row) if row else None


def get_overdue_problems(source_list: Optional[str] = None) -> list[Problem]:
    """Get all problems that are overdue for review."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    
    if source_list:
        cursor.execute("""
            SELECT * FROM problems 
            WHERE next_review IS NOT NULL AND next_review < ? AND source_list = ?
            ORDER BY next_review ASC
        """, (today, source_list))
    else:
        cursor.execute("""
            SELECT * FROM problems 
            WHERE next_review IS NOT NULL AND next_review < ?
            ORDER BY next_review ASC
        """, (today,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_problem(row) for row in rows]


def update_problem_srs(
    problem_id: int,
    next_review: date,
    interval: int,
    ease_factor: float,
    repetition: int
) -> None:
    """Update a problem's SRS data after review."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE problems 
        SET next_review = ?,
            interval = ?,
            ease_factor = ?,
            repetition = ?,
            last_reviewed = ?,
            times_solved = times_solved + 1
        WHERE id = ?
    """, (
        next_review.isoformat(),
        interval,
        ease_factor,
        repetition,
        date.today().isoformat(),
        problem_id
    ))
    
    conn.commit()
    conn.close()


def reset_progress(source_list: Optional[str] = None) -> int:
    """
    Reset all SRS progress data back to defaults.

    Keeps problem definitions but clears all review history.

    Args:
        source_list: If provided, only reset problems from this list.

    Returns:
        Number of problems reset.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if source_list:
        cursor.execute("""
            UPDATE problems
            SET repetition = 0, ease_factor = 2.5, interval = 0,
                next_review = NULL, last_reviewed = NULL, times_solved = 0
            WHERE source_list = ?
        """, (source_list,))
    else:
        cursor.execute("""
            UPDATE problems
            SET repetition = 0, ease_factor = 2.5, interval = 0,
                next_review = NULL, last_reviewed = NULL, times_solved = 0
        """)

    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected


def get_stats(source_list: Optional[str] = None) -> dict:
    """Get study statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    
    list_filter = "WHERE source_list = ?" if source_list else ""
    list_filter_and = "AND source_list = ?" if source_list else ""
    params = (source_list,) if source_list else ()
    
    # Total problems
    cursor.execute(f"SELECT COUNT(*) FROM problems {list_filter}", params)
    total = cursor.fetchone()[0]
    
    # Problems solved at least once
    cursor.execute(
        f"SELECT COUNT(*) FROM problems WHERE times_solved > 0 {list_filter_and}",
        params
    )
    solved = cursor.fetchone()[0]
    
    # Due today
    cursor.execute(f"""
        SELECT COUNT(*) FROM problems 
        WHERE next_review IS NOT NULL AND next_review <= ? {list_filter_and}
    """, (today,) + params)
    due_today = cursor.fetchone()[0]
    
    # Total reviews (sum of times_solved)
    cursor.execute(f"SELECT SUM(times_solved) FROM problems {list_filter}", params)
    total_reviews = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        'total_problems': total,
        'problems_started': solved,
        'due_today': due_today,
        'total_reviews': total_reviews,
        'new_problems': total - solved
    }


def get_pattern_stats(source_list: Optional[str] = None) -> dict[str, dict]:
    """Get statistics grouped by pattern."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    
    list_filter = "AND source_list = ?" if source_list else ""
    params = (source_list,) if source_list else ()
    
    # Get all patterns
    if source_list:
        cursor.execute(
            "SELECT DISTINCT pattern FROM problems WHERE source_list = ?",
            (source_list,)
        )
    else:
        cursor.execute("SELECT DISTINCT pattern FROM problems")
    
    patterns = [row[0] for row in cursor.fetchall()]
    
    result = {}
    for pattern in patterns:
        pattern_params = (pattern,) + params
        
        # Total in pattern
        cursor.execute(
            f"SELECT COUNT(*) FROM problems WHERE pattern = ? {list_filter}",
            pattern_params
        )
        total = cursor.fetchone()[0]
        
        # Solved at least once
        cursor.execute(
            f"SELECT COUNT(*) FROM problems WHERE pattern = ? AND times_solved > 0 {list_filter}",
            pattern_params
        )
        solved = cursor.fetchone()[0]
        
        # Due today
        cursor.execute(f"""
            SELECT COUNT(*) FROM problems 
            WHERE pattern = ? AND next_review IS NOT NULL AND next_review <= ? {list_filter}
        """, (pattern, today) + params)
        due = cursor.fetchone()[0]
        
        result[pattern] = {
            'total': total,
            'solved': solved,
            'due': due,
            'progress': (solved / total * 100) if total > 0 else 0
        }
    
    conn.close()
    return result


def _row_to_problem(row: sqlite3.Row) -> Problem:
    """Convert a database row to a Problem object."""
    return Problem(
        id=row['id'],
        name=row['name'],
        url=row['url'],
        category=row['category'],
        difficulty=row['difficulty'],
        pattern=row['pattern'] if 'pattern' in row.keys() else 'General',
        source_list=row['source_list'] if 'source_list' in row.keys() else 'Blind 75',
        repetition=row['repetition'],
        ease_factor=row['ease_factor'],
        interval=row['interval'],
        next_review=_parse_date(row['next_review']),
        last_reviewed=_parse_date(row['last_reviewed']),
        times_solved=row['times_solved']
    )


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a date string into a date object."""
    if date_str is None:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def get_streak() -> int:
    """
    Calculate the current study streak (consecutive days with at least 1 review).

    Returns:
        Number of consecutive days ending today or yesterday.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT last_reviewed FROM problems
        WHERE last_reviewed IS NOT NULL
        ORDER BY last_reviewed DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0

    reviewed_dates = set()
    for row in rows:
        d = _parse_date(row[0])
        if d:
            reviewed_dates.add(d)

    if not reviewed_dates:
        return 0

    today = date.today()
    # Streak can start from today or yesterday
    if today in reviewed_dates:
        current = today
    elif (today - timedelta(days=1)) in reviewed_dates:
        current = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while current in reviewed_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def get_milestone_stats() -> dict:
    """
    Get stats useful for milestone detection.

    Returns:
        Dict with: total_solved, total_reviews, completed_patterns (list),
        solved_today count.
    """
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()

    # Total unique problems solved
    cursor.execute("SELECT COUNT(*) FROM problems WHERE times_solved > 0")
    total_solved = cursor.fetchone()[0]

    # Total reviews
    cursor.execute("SELECT SUM(times_solved) FROM problems")
    total_reviews = cursor.fetchone()[0] or 0

    # Solved today
    cursor.execute(
        "SELECT COUNT(*) FROM problems WHERE last_reviewed = ?",
        (today,)
    )
    solved_today = cursor.fetchone()[0]

    # Completed patterns (100% solved)
    cursor.execute("""
        SELECT pattern, COUNT(*) as total,
               SUM(CASE WHEN times_solved > 0 THEN 1 ELSE 0 END) as solved
        FROM problems
        GROUP BY pattern
        HAVING total = solved AND total > 0
    """)
    completed_patterns = [row[0] for row in cursor.fetchall()]

    conn.close()

    return {
        'total_solved': total_solved,
        'total_reviews': total_reviews,
        'solved_today': solved_today,
        'completed_patterns': completed_patterns,
    }


def _infer_pattern(category: str) -> str:
    """Infer pattern from category for legacy data."""
    mapping = {
        'Array': 'Two Pointers',
        'Binary': 'Bit Manipulation',
        'Dynamic Programming': 'Dynamic Programming',
        'Graph': 'Graphs',
        'Interval': 'Intervals',
        'Linked List': 'Linked Lists',
        'Matrix': 'Graphs',
        'String': 'Sliding Window',
        'Tree': 'Trees',
        'Heap': 'Heap / Priority Queue',
    }
    return mapping.get(category, 'General')

