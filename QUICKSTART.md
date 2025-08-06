# Quick Start Guide

## Installation

```bash
# Clone/navigate to the project directory
cd qBank

# Install with uv (recommended)
uv sync --all-extras

# Or install with pip
pip install -e .
```

## Basic Usage

### 1. Run the Demo
```bash
uv run qbank-demo
```
This creates sample questions and runs a complete study session.

### 2. Use the Command Line Interface

```bash
# Show help
uv run qbank-cli --help

# List questions
uv run qbank-cli list

# Start a study session
uv run qbank-cli study

# Show statistics
uv run qbank-cli stats

# Add questions interactively
uv run qbank-cli add
```

### 3. Use the Python API

```python
from qbank import QuestionBankManager

# Create manager
manager = QuestionBankManager("My Bank", "user123")

# Add a question
question = manager.create_multiple_choice_question(
    "What is 2 + 2?",
    "4",
    ["3", "5", "6"],
    ["math", "basic"]
)

# Start study session
questions = manager.start_study_session()

# Answer questions and get feedback
for q in questions:
    result = manager.answer_question(q.id, q.correct_answer.id)
    print(f"Correct: {result['correct']}")

# End session
session = manager.end_study_session()
print(f"Accuracy: {session.accuracy:.1f}%")
```

## Advanced Features

### Spaced Repetition
- Questions are automatically scheduled for review
- Interval increases when answered correctly
- Resets to 1 day when answered incorrectly
- Based on the proven SM-2 algorithm

### ELO Rating System
- Questions and users have skill ratings (like chess)
- Ratings adjust based on performance
- System recommends appropriate difficulty questions

### Study Session Filtering
```python
# Study specific topics
questions = manager.start_study_session(
    max_questions=10,
    tags_filter={"python", "programming"},
    difficulty_range=(1000, 1400)
)
```

### Analytics & Statistics
```python
# Get comprehensive statistics
stats = manager.get_user_statistics()
print(f"User level: {stats['user_level']}")
print(f"Recent accuracy: {stats['recent_accuracy']:.1f}%")

# Get review forecast
forecast = manager.get_review_forecast(7)
for date, count in forecast.items():
    if count > 0:
        print(f"{date}: {count} questions due")
```

### Import/Export
```python
# Export question bank
manager.export_bank("my_questions.json")

# Import question bank
manager.import_bank("my_questions.json")
```

## Files

- `main.py` - Basic demo with sample questions
- `examples/advanced_demo.py` - Comprehensive feature demonstration  
- `cli.py` - Command-line interface
- `tests/test_qbank.py` - Unit tests
- `qbank/` - Main module source code

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=qbank
```

## Development

```bash
# Install development dependencies
uv sync --dev

# Run linting
uv run ruff check qbank/
uv run black --check qbank/

# Format code
uv run black qbank/
uv run isort qbank/
```

## Data Format

Questions are stored in JSON format with complete learning history:

```json
{
  "question_text": "What is 2 + 2?",
  "answers": [...],
  "tags": ["math", "arithmetic"],
  "elo_rating": 1200.0,
  "times_answered": 5,
  "times_correct": 4,
  "next_review": "2024-01-15T10:00:00",
  "interval_days": 3.5,
  "ease_factor": 2.6
}
```

This preserves all learning progress and allows for detailed analytics.
