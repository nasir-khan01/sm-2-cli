# 🧠 SM-2 CLI

A **Spaced Repetition CLI** built on the SM-2 algorithm — the same system behind Anki.

Use it to master anything: coding problems, flashcards, study material, or any skill that benefits from scheduled review.

---

## ✨ Features

- **SM-2 Algorithm** – Scientifically-proven spaced repetition for optimal retention
- **Pattern-based Organization** – Group items by topic/pattern (NeetCode order)
- **Multi-list Support** – Manage separate lists (e.g., "Blind 75", "Custom")
- **Progress Dashboard** – Visual progress bars by pattern
- **Flexible Filtering** – Filter by pattern or list
- **Quick Logging** – Log problems by name without opening browser

---

## 🚀 Installation

```bash
git clone https://github.com/yourusername/sm2-cli.git
cd sm2-cli
uv pip install -e .
```

### Running

```bash
# Using uv run
uv run dsaprep <command>

# Or activate venv first
source .venv/bin/activate
dsaprep <command>
```

---

## 📖 Commands

### Initialize Database
```bash
dsaprep init
```

### View Dashboard
```bash
dsaprep dashboard
dsaprep dashboard --list "Blind 75"
```

### Get Next Problem
```bash
dsaprep next
dsaprep next --pattern "Two Pointers"
dsaprep next -p "Dynamic" -l "Blind 75"
```

### Solve (opens browser)
```bash
dsaprep solve 1
```

### Log (rate without opening browser)
```bash
dsaprep log "Two Sum"
dsaprep log "Two Sum" --score 4
dsaprep log 5 -s 3
```

### View Problems by Pattern
```bash
dsaprep stats --pattern "Trees"
dsaprep stats -p "Dynamic" -l "Blind 75"
```

### Add Custom Problem
```bash
dsaprep add-problem \
  --title "LRU Cache" \
  --url "https://leetcode.com/problems/lru-cache/" \
  --pattern "Linked Lists" \
  --list "Custom"
```

### View All Lists
```bash
dsaprep lists
```

### Reset Progress
```bash
dsaprep reset              # interactive confirmation
dsaprep reset --yes        # skip confirmation
dsaprep reset -l "Blind 75" -y  # reset only a specific list
```

---

## 🧮 SM-2 Algorithm

| Score | Meaning | Next Interval |
|-------|---------|---------------|
| 0-2 | Incorrect/Forgot | 1 day |
| 3 | Correct with difficulty | Previous × EF |
| 4 | Correct after hesitation | Previous × EF |
| 5 | Perfect recall | Previous × EF |

---

## 📁 Patterns (NeetCode Order)

1. Arrays & Hashing
2. Two Pointers
3. Sliding Window
4. Stack
5. Binary Search
6. Linked Lists
7. Trees
8. Tries
9. Heap / Priority Queue
10. Backtracking
11. Graphs
12. 1-D Dynamic Programming
13. 2-D Dynamic Programming
14. Greedy
15. Intervals
16. Math & Geometry
17. Bit Manipulation

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 📜 License

MIT
