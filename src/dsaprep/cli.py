"""
DSAPrep CLI Application.

Main entry point for the dsaprep command-line tool.
"""

import json
import webbrowser
from pathlib import Path
from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, BarColumn, TextColumn

from dsaprep.database import (
    init_db,
    seed_problems,
    add_problem as db_add_problem,
    get_all_problems,
    get_problem_by_id,
    get_next_problem,
    get_stats,
    get_pattern_stats,
    get_all_patterns,
    get_all_lists,
    update_problem_srs,
    DB_PATH,
    DEFAULT_PATTERNS,
)
from dsaprep.srs import calculate_sm2

# Optional motivation module (local-only, not in repo)
try:
    from dsaprep.motivation import check_slacking, print_encouragement
except ImportError:
    # No-op fallbacks if motivation.py doesn't exist
    def check_slacking() -> bool:
        return False
    
    def print_encouragement() -> None:
        pass


app = typer.Typer(
    name="dsaprep",
    help="🧠 DSA Interview Prep with Spaced Repetition",
    add_completion=False,
)
console = Console()


@app.command()
def init():
    """
    Initialize the database and seed with Blind 75 problems.
    """
    console.print("\n[bold cyan]🚀 Initializing DSAPrep...[/bold cyan]\n")
    
    # Initialize database
    init_db()
    console.print(f"[green]✓[/green] Database created at [dim]{DB_PATH}[/dim]")
    
    # Load and seed problems
    data_path = Path(__file__).parent / "data" / "blind75.json"
    
    if not data_path.exists():
        console.print("[red]✗ Could not find blind75.json data file[/red]")
        raise typer.Exit(1)
    
    with open(data_path, 'r') as f:
        problems = json.load(f)
    
    count = seed_problems(problems, source_list="Blind 75")
    console.print(f"[green]✓[/green] Seeded database with [bold]{count}[/bold] problems")
    
    # Show summary by pattern
    console.print("\n[bold]📊 Problems by Pattern:[/bold]")
    patterns = {}
    for p in problems:
        pat = p.get('pattern', 'General')
        patterns[pat] = patterns.get(pat, 0) + 1
    
    for pat, cnt in sorted(patterns.items()):
        console.print(f"   • {pat}: {cnt}")
    
    console.print("\n[bold green]✓ DSAPrep is ready![/bold green]")
    console.print("[dim]Run 'dsaprep dashboard' to see your progress[/dim]")
    console.print("[dim]Run 'dsaprep next' to start solving problems[/dim]\n")


@app.command()
def dashboard(
    list_filter: Optional[str] = typer.Option(None, "--list", "-l", help="Filter by source list")
):
    """
    Display pattern-wise progress dashboard.
    """
    console.print("\n[bold cyan]📊 DSAPrep Dashboard[/bold cyan]\n")
    
    # Get pattern stats
    pattern_stats = get_pattern_stats(source_list=list_filter)
    
    if not pattern_stats:
        console.print("[yellow]No problems in database. Run 'dsaprep init' first.[/yellow]\n")
        raise typer.Exit(1)
    
    # Show which list we're viewing
    if list_filter:
        console.print(f"[dim]Showing: {list_filter}[/dim]\n")
    else:
        lists = get_all_lists()
        if lists:
            console.print(f"[dim]Showing all lists: {', '.join(lists)}[/dim]\n")
    
    # Get overall stats
    overall = get_stats(source_list=list_filter)
    
    # Summary panel
    summary_text = Text()
    summary_text.append(f"Total: {overall['total_problems']} problems  |  ", style="bold")
    summary_text.append(f"Started: {overall['problems_started']}  |  ", style="green")
    summary_text.append(f"Due: {overall['due_today']}", style="red" if overall['due_today'] > 0 else "green")
    
    console.print(Panel(summary_text, border_style="cyan"))
    console.print()
    
    # Pattern-wise progress
    for pattern, stats in sorted(pattern_stats.items(), key=lambda x: -x[1]['progress']):
        # Progress bar
        progress_pct = stats['progress']
        filled = int(progress_pct / 10)
        empty = 10 - filled
        bar = "█" * filled + "░" * empty
        
        # Color based on progress
        if progress_pct >= 80:
            color = "green"
        elif progress_pct >= 40:
            color = "yellow"
        else:
            color = "red"
        
        # Status indicators
        due_str = f" [red]({stats['due']} due)[/red]" if stats['due'] > 0 else ""
        
        console.print(
            f"  [{color}]{bar}[/{color}] {progress_pct:5.1f}% "
            f"[bold]{pattern}[/bold] ({stats['solved']}/{stats['total']}){due_str}"
        )
    
    console.print()
    console.print("[dim]Run 'dsaprep stats' for detailed problem list[/dim]")
    console.print("[dim]Run 'dsaprep next' to get the next problem to solve[/dim]\n")


@app.command("add-problem")
def add_problem(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Problem title"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="Problem URL"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="Algorithm pattern"),
    list_name: Optional[str] = typer.Option(None, "--list", "-l", help="Source list name"),
    difficulty: Optional[str] = typer.Option(None, "--difficulty", "-d", help="Difficulty level"),
):
    """
    Add a custom problem to the database.
    
    Can be used with arguments or interactively.
    """
    console.print("\n[bold cyan]➕ Add New Problem[/bold cyan]\n")
    
    # Interactive mode if args not provided
    if not title:
        title = Prompt.ask("[bold]Problem title[/bold]")
    
    if not url:
        url = Prompt.ask("[bold]Problem URL[/bold]")
    
    if not pattern:
        console.print("\n[dim]Available patterns:[/dim]")
        for i, p in enumerate(DEFAULT_PATTERNS, 1):
            console.print(f"  {i:2}. {p}")
        console.print()
        
        pattern_input = Prompt.ask(
            "[bold]Pattern[/bold] (name or number)",
            default="General"
        )
        
        # Check if it's a number
        try:
            idx = int(pattern_input) - 1
            if 0 <= idx < len(DEFAULT_PATTERNS):
                pattern = DEFAULT_PATTERNS[idx]
            else:
                pattern = pattern_input
        except ValueError:
            pattern = pattern_input
    
    if not list_name:
        list_name = Prompt.ask(
            "[bold]Source list[/bold]",
            default="Custom"
        )
    
    if not difficulty:
        difficulty = Prompt.ask(
            "[bold]Difficulty[/bold]",
            choices=["Easy", "Medium", "Hard"],
            default="Medium"
        )
    
    # Add to database
    problem_id = db_add_problem(
        name=title,
        url=url,
        pattern=pattern,
        source_list=list_name,
        difficulty=difficulty
    )
    
    console.print(f"\n[green]✓[/green] Added problem [bold]#{problem_id}[/bold]: {title}")
    console.print(f"  Pattern: {pattern}")
    console.print(f"  List: {list_name}")
    console.print(f"  Difficulty: {difficulty}\n")


@app.command("next")
def next_problem(
    list_filter: Optional[str] = typer.Option(None, "--list", "-l", help="Filter by source list")
):
    """
    Get the next problem to solve.
    
    Shows the most overdue problem, or a new one if all are up to date.
    """
    console.print()
    
    # Check for slacking first
    check_slacking()
    
    problem = get_next_problem(source_list=list_filter)
    
    if not problem:
        if list_filter:
            msg = f"No problems due for review in [bold]{list_filter}[/bold]."
        else:
            msg = "No problems due for review."
        
        console.print(Panel(
            f"[bold green]🎉 All caught up![/bold green]\n\n{msg}\nGreat job staying consistent!",
            title="[bold]Status[/bold]",
            border_style="green",
        ))
        print_encouragement()
        return
    
    # Build status text
    if problem.next_review is None:
        status = "[cyan]NEW[/cyan] - Never attempted"
    elif problem.next_review <= date.today():
        days_overdue = (date.today() - problem.next_review).days
        if days_overdue == 0:
            status = "[yellow]DUE TODAY[/yellow]"
        else:
            status = f"[red]OVERDUE[/red] by {days_overdue} days"
    else:
        status = f"Due on {problem.next_review}"
    
    # Display problem
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="dim")
    table.add_column("Value", style="bold")
    
    table.add_row("ID", str(problem.id))
    table.add_row("Name", problem.name)
    table.add_row("Pattern", f"[cyan]{problem.pattern}[/cyan]")
    table.add_row("List", problem.source_list)
    table.add_row("Difficulty", _colorize_difficulty(problem.difficulty))
    table.add_row("Status", status)
    table.add_row("Times Solved", str(problem.times_solved))
    table.add_row("URL", f"[link={problem.url}]{problem.url}[/link]")
    
    console.print(Panel(
        table,
        title=f"[bold cyan]📚 Next Problem[/bold cyan]",
        border_style="cyan",
    ))
    
    console.print(f"\n[dim]Run 'dsaprep solve {problem.id}' to attempt this problem[/dim]\n")


@app.command()
def solve(problem_id: int):
    """
    Solve a problem: opens LeetCode and records your difficulty score.
    
    Args:
        problem_id: The ID of the problem to solve
    """
    problem = get_problem_by_id(problem_id)
    
    if not problem:
        console.print(f"[red]✗ Problem with ID {problem_id} not found[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]🎯 Solving: {problem.name}[/bold cyan]")
    console.print(f"[dim]Pattern: {problem.pattern} | Difficulty: {problem.difficulty}[/dim]\n")
    
    # Open in browser
    console.print("[yellow]Opening problem in browser...[/yellow]")
    webbrowser.open(problem.url)
    
    console.print("\n[bold]Take your time to solve the problem.[/bold]")
    console.print("When done, rate how it went:\n")
    
    # Show rating options
    console.print("  [bold red]0[/bold red] - Complete blackout (couldn't even start)")
    console.print("  [bold red]1[/bold red] - Incorrect, remembered after seeing solution")
    console.print("  [bold yellow]2[/bold yellow] - Incorrect, but solution seemed easy")
    console.print("  [bold green]3[/bold green] - Correct with serious difficulty")
    console.print("  [bold green]4[/bold green] - Correct after some hesitation")
    console.print("  [bold cyan]5[/bold cyan] - Perfect! Easy recall")
    console.print()
    
    # Get rating
    while True:
        try:
            score = IntPrompt.ask(
                "[bold]Your rating (0-5)[/bold]",
                default=3
            )
            if 0 <= score <= 5:
                break
            console.print("[red]Please enter a number between 0 and 5[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    # Calculate new SRS values
    result = calculate_sm2(
        quality=score,
        repetition=problem.repetition,
        ease_factor=problem.ease_factor,
        interval=problem.interval
    )
    
    # Update database
    update_problem_srs(
        problem_id=problem.id,
        next_review=result.next_review,
        interval=result.interval,
        ease_factor=result.ease_factor,
        repetition=result.repetition
    )
    
    # Show result
    console.print()
    if score < 3:
        console.print(Panel(
            f"[yellow]The problem will reappear tomorrow for reinforcement.[/yellow]\n\n"
            f"Next review: [bold]{result.next_review}[/bold]",
            title="[bold yellow]📝 Keep Practicing[/bold yellow]",
            border_style="yellow",
        ))
    else:
        console.print(Panel(
            f"[green]Great job! Problem logged successfully.[/green]\n\n"
            f"Next review: [bold]{result.next_review}[/bold] (in {result.interval} days)\n"
            f"Ease factor: {result.ease_factor}",
            title="[bold green]✅ Problem Solved[/bold green]",
            border_style="green",
        ))
    
    print_encouragement()


@app.command()
def stats(
    list_filter: Optional[str] = typer.Option(None, "--list", "-l", help="Filter by source list")
):
    """
    Display your study progress and statistics.
    """
    console.print("\n[bold cyan]📊 DSAPrep Statistics[/bold cyan]\n")
    
    # Get stats
    stat = get_stats(source_list=list_filter)
    problems = get_all_problems(source_list=list_filter)
    
    if not problems:
        if list_filter:
            console.print(f"[yellow]No problems found in list '{list_filter}'.[/yellow]\n")
        else:
            console.print("[yellow]No problems in database. Run 'dsaprep init' first.[/yellow]\n")
        raise typer.Exit(1)
    
    # Show which list we're viewing
    if list_filter:
        console.print(f"[dim]Showing: {list_filter}[/dim]\n")
    
    # Summary panel
    summary = Table(show_header=False, box=None)
    summary.add_column("Metric", style="dim")
    summary.add_column("Value", style="bold")
    
    summary.add_row("Total Problems", str(stat['total_problems']))
    summary.add_row("Problems Started", f"{stat['problems_started']} ({stat['problems_started']*100//max(stat['total_problems'],1)}%)")
    summary.add_row("New Problems", str(stat['new_problems']))
    summary.add_row("Due Today", f"[{'red' if stat['due_today'] > 0 else 'green'}]{stat['due_today']}[/]")
    summary.add_row("Total Reviews", str(stat['total_reviews']))
    
    console.print(Panel(summary, title="[bold]Summary[/bold]", border_style="cyan"))
    console.print()
    
    # Problems table
    table = Table(title="All Problems", show_lines=False)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Name", style="bold", max_width=35)
    table.add_column("Pattern", style="cyan", width=18)
    table.add_column("Diff", width=8)
    table.add_column("Next Review", width=12)
    table.add_column("Solved", width=6, justify="center")
    
    today = date.today()
    for p in problems:
        # Format next review
        if p.next_review is None:
            review_str = "[dim]New[/dim]"
        elif p.next_review <= today:
            days = (today - p.next_review).days
            if days == 0:
                review_str = "[yellow]Today[/yellow]"
            else:
                review_str = f"[red]{days}d overdue[/red]"
        else:
            days = (p.next_review - today).days
            review_str = f"[green]in {days}d[/green]"
        
        table.add_row(
            str(p.id),
            p.name[:35],
            p.pattern[:18] if p.pattern else "",
            _colorize_difficulty(p.difficulty),
            review_str,
            str(p.times_solved) if p.times_solved > 0 else "[dim]-[/dim]"
        )
    
    console.print(table)
    console.print()


@app.command()
def lists():
    """
    Show all available problem lists.
    """
    console.print("\n[bold cyan]📋 Problem Lists[/bold cyan]\n")
    
    all_lists = get_all_lists()
    
    if not all_lists:
        console.print("[yellow]No lists found. Run 'dsaprep init' first.[/yellow]\n")
        raise typer.Exit(1)
    
    for lst in all_lists:
        stats = get_stats(source_list=lst)
        console.print(
            f"  • [bold]{lst}[/bold]: {stats['total_problems']} problems "
            f"({stats['problems_started']} started, {stats['due_today']} due)"
        )
    
    console.print()


def _colorize_difficulty(difficulty: str) -> str:
    """Return colored difficulty string."""
    colors = {
        'Easy': 'green',
        'Medium': 'yellow',
        'Hard': 'red'
    }
    color = colors.get(difficulty, 'white')
    return f"[{color}]{difficulty}[/{color}]"


if __name__ == "__main__":
    app()
