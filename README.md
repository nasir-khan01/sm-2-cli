# 🧠 SM-2 CLI

A **Spaced Repetition CLI** built on the SM-2 algorithm — the same system behind Anki.

Use it to master anything: coding problems, flashcards, study material, or any skill that benefits from scheduled review.

---

## ✨ Features

- **SM-2 Algorithm** – Scientifically-proven spaced repetition for optimal retention
- **Pattern-based Organization** – Group items by topic/pattern for structured learning
- **Multi-list Support** – Manage separate lists (e.g., "Blind 75", "System Design", "Custom")
- **Progress Dashboard** – Visual progress bars by pattern
- **Custom Items** – Add your own problems/topics to track
- **Browser Integration** – Opens URLs directly for web-based learning

---

## 🚀 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/sm2-cli.git
cd sm2-cli

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

---

## 📖 Usage

### Initialize
```bash
dsaprep init
```

### View Progress Dashboard
```bash
dsaprep dashboard
```

```
📊 Dashboard

██████████  100.0% Two Pointers (9/9)
████░░░░░░   40.0% Dynamic Programming (6/14)
░░░░░░░░░░    0.0% Graphs (0/11)
```

### Get Next Item to Review
```bash
dsaprep next

# Filter by list
dsaprep next --list "Custom"
```

### Mark Item as Reviewed
```bash
dsaprep solve 1
```
Opens the URL (if any), then prompts you to rate your recall (0-5).

### Add Custom Item
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

### Detailed Statistics
```bash
dsaprep stats
dsaprep stats --list "Custom"
```

---

## 🧮 SM-2 Algorithm

| Score | Meaning | Next Interval |
|-------|---------|---------------|
| 0 | Complete blackout | 1 day |
| 1 | Incorrect, knew after reveal | 1 day |
| 2 | Incorrect, seemed easy | 1 day |
| 3 | Correct with difficulty | Previous × EF |
| 4 | Correct after hesitation | Previous × EF |
| 5 | Perfect recall | Previous × EF |

The Ease Factor (EF) adjusts based on performance — harder items appear more frequently.

---

## 📁 Project Structure

```
sm2-cli/
├── src/dsaprep/
│   ├── cli.py          # CLI commands
│   ├── database.py     # SQLite operations
│   ├── srs.py          # SM-2 algorithm
│   └── data/
│       └── blind75.json
└── tests/
    └── test_srs.py
```

---

## 🧪 Testing

```bash
pytest tests/ -v
```

---

## 📜 License

MIT

---

## 🤝 Contributing

PRs welcome! Add new datasets or improve the SRS engine.
