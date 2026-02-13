"""
UX module for DSAPrep.

Provides visual enhancements: banner, celebrations, milestones, tips, and daily summary.
"""

import random

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from dsaprep.database import get_stats, get_streak, get_milestone_stats


console = Console()


# ─── Banner ──────────────────────────────────────────────────────────────────

def print_banner():
    """Print a styled ASCII banner."""
    banner = Text()
    banner.append("  ╔══════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("  ║", style="bold cyan")
    banner.append("   🧠  D S A P R E P                     ", style="bold white")
    banner.append("║\n", style="bold cyan")
    banner.append("  ║", style="bold cyan")
    banner.append("   Spaced Repetition Engine              ", style="dim white")
    banner.append("║\n", style="bold cyan")
    banner.append("  ╚══════════════════════════════════════════╝", style="bold cyan")
    console.print(banner)
    console.print()


# ─── Daily Summary Bar ──────────────────────────────────────────────────────

def print_daily_summary(source_list=None):
    """Print a compact daily summary bar with streak."""
    stats = get_stats(source_list=source_list)
    streak = get_streak()

    # Build summary parts
    parts = []
    parts.append(f"[bold]{stats['problems_started']}[/bold]/{stats['total_problems']} solved")

    if stats['due_today'] > 0:
        parts.append(f"[bold red]{stats['due_today']} due[/bold red]")
    else:
        parts.append("[bold green]0 due[/bold green]")

    parts.append(f"[bold]{stats['total_reviews']}[/bold] reviews")

    # Streak
    if streak > 0:
        if streak >= 30:
            streak_str = f"[bold magenta]🏆 {streak}-day streak[/bold magenta]"
        elif streak >= 7:
            streak_str = f"[bold green]🔥🔥 {streak}-day streak[/bold green]"
        else:
            streak_str = f"[green]🔥 {streak}-day streak[/green]"
        parts.append(streak_str)
    else:
        parts.append("[dim]No streak — solve one today![/dim]")

    summary_text = "  │  ".join(parts)
    console.print(Panel(
        summary_text,
        border_style="dim cyan",
        padding=(0, 1),
    ))
    console.print()


# ─── Celebrations ────────────────────────────────────────────────────────────

CELEBRATIONS_PERFECT = [
    "🏆 PERFECT! Flawless recall — you own this one!",
    "🏆 NAILED IT! That's muscle memory right there!",
    "🏆 PERFECT SCORE! This problem fears you now.",
]

CELEBRATIONS_GOOD = [
    "✨ Great job! Solid recall — keep it up!",
    "✨ Nice work! You're getting sharper every day.",
    "✨ Well done! That one's becoming second nature.",
]

CELEBRATIONS_OK = [
    "💪 Good fight! You pushed through — that's what matters.",
    "💪 Battled through it! Next time will be smoother.",
    "💪 Got it done! Persistence is the key.",
]

CELEBRATIONS_FAIL = [
    "📖 No worries — it'll stick next time. Review is the whole point!",
    "📖 This is how learning works. You'll crush it tomorrow.",
    "📖 Not yet — but your brain is wiring it. Come back stronger!",
]


def print_celebration(score: int, problem_name: str):
    """Print a score-dependent celebration message."""
    if score == 5:
        msg = random.choice(CELEBRATIONS_PERFECT)
        style = "bold magenta"
    elif score == 4:
        msg = random.choice(CELEBRATIONS_GOOD)
        style = "bold green"
    elif score == 3:
        msg = random.choice(CELEBRATIONS_OK)
        style = "bold yellow"
    else:
        msg = random.choice(CELEBRATIONS_FAIL)
        style = "bold cyan"

    console.print(f"\n[{style}]{msg}[/{style}]")


# ─── Milestones ──────────────────────────────────────────────────────────────

def check_milestones():
    """Check and display any newly hit milestones."""
    ms = get_milestone_stats()
    solved = ms['total_solved']
    reviews = ms['total_reviews']
    completed = ms['completed_patterns']

    milestones_hit = []

    # Solve count milestones
    for threshold in [1, 10, 25, 50, 75]:
        if solved == threshold:
            if threshold == 1:
                milestones_hit.append("🌱 First Problem Solved! The journey begins!")
            elif threshold == 10:
                milestones_hit.append("⭐ 10 Problems Solved! You're building momentum!")
            elif threshold == 25:
                milestones_hit.append("🌟 25 Problems Solved! Quarter century — impressive!")
            elif threshold == 50:
                milestones_hit.append("💎 50 Problems Solved! Halfway to mastery!")
            elif threshold == 75:
                milestones_hit.append("🏆 ALL 75 PROBLEMS SOLVED! You're interview-ready!")

    # Review milestones
    for threshold in [50, 100, 200, 500]:
        if reviews == threshold:
            milestones_hit.append(f"📊 {threshold} Total Reviews! Consistency is your superpower!")

    # Pattern completion
    if completed:
        for pattern in completed:
            # We show this every time, but it's fine — it only triggers on exact completion
            milestones_hit.append(f"✅ Pattern Complete: {pattern}! 100% mastery!")

    if milestones_hit:
        console.print()
        for milestone in milestones_hit:
            console.print(Panel(
                f"[bold]{milestone}[/bold]",
                border_style="bold yellow",
                title="[bold yellow]🎯 MILESTONE[/bold yellow]",
                padding=(0, 2),
            ))


# ─── Tips ────────────────────────────────────────────────────────────────────

TIPS = [
    "💡 Tip: Problems rated 0-2 reset to tomorrow — don't fear low scores, they help!",
    "💡 Tip: Use 'dsaprep log' to quickly rate problems without opening the browser.",
    "💡 Tip: Filter by pattern with -p to focus on weak areas.",
    "💡 Tip: The SM-2 algorithm gets smarter the more honest your ratings are.",
    "💡 Tip: Consistency > intensity. 3 problems daily beats 20 on weekends.",
    "💡 Tip: Score 3 (correct with difficulty) is the sweet spot for learning.",
    "💡 Tip: Use 'dsaprep stats -p Trees' to see all problems in a pattern.",
    "💡 Tip: Can't remember a solution? Score it 0 — it'll come back tomorrow.",
    "💡 Tip: Review overdue problems first — they decay the fastest.",
    "💡 Tip: Use 'dsaprep reset' if you want a completely fresh start.",
]


def print_tip():
    """Print a random study tip (30% chance to keep it from being noisy)."""
    if random.random() < 0.30:
        console.print(f"\n[dim]{random.choice(TIPS)}[/dim]")
