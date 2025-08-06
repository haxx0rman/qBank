# QBank - Spaced Repetition Question Bank System

A comprehensive question bank system with spaced repetition learning (similar to Anki) and ELO-based difficulty rating. Perfect for studying any subject with adaptive difficulty and intelligent review scheduling.

## Features

### 🧠 **Smart Learning System**
- **Spaced Repetition**: Questions are scheduled for review based on the SM-2 algorithm
- **ELO Rating System**: Questions have difficulty ratings that adjust based on user performance
- **Adaptive Learning**: The system recommends questions based on your skill level

### 📚 **Question Management**
- Multiple choice questions with explanations
- Tagging system for organizing questions by topic
- Full-text search across questions and answers
- Import/export functionality (JSON format)

### 📊 **Progress Tracking**
- User skill ratings (like chess ELO)
- Detailed accuracy statistics per question
- Study session history and analytics
- Review forecasting for upcoming sessions

### 🎯 **Study Sessions**
- Interactive study sessions with immediate feedback
- Customizable session length and difficulty
- Skip functionality for questions you're not ready for
- Real-time rating updates

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd qBank

# Install dependencies (if using uv)
uv sync

# Or install in development mode
pip install -e .
```

## Quick Start

### Using the Python API

```python
from qbank import QuestionBankManager

# Create a question bank manager
manager = QuestionBankManager("My Study Bank", "my_user_id")

# Add a question
question = manager.create_multiple_choice_question(
    question_text="What is the capital of France?",
    correct_answer="Paris",
    wrong_answers=["London", "Berlin", "Madrid"],
    tags=["geography", "europe"]
)

# Start a study session
questions = manager.start_study_session(max_questions=5)

for question in questions:
    print(f"Question: {question.question_text}")
    # ... show answers and get user input ...
    
    # Submit answer (example with first answer)
    result = manager.answer_question(
        question.id, 
        question.answers[0].id, 
        response_time=5.0
    )
    print(f"Correct: {result['correct']}")

# End the session
session = manager.end_study_session()
print(f"Session accuracy: {session.accuracy:.1f}%")
```

### Using the Command Line Interface

```bash
# Add questions interactively
python cli.py add

# Start a study session
python cli.py study

# List all questions
python cli.py list

# Show statistics
python cli.py stats

# Export question bank
python cli.py export my_backup.json
```

### Running the Demo

```bash
python main.py
```

This will create sample questions and demonstrate a complete study session with statistics.

## System Architecture

### Core Components

1. **Question & Answer Models** (`models.py`)
   - `Question`: Stores question text, answers, tags, and learning metrics
   - `Answer`: Individual answer options with correctness and explanations
   - `QuestionBank`: Container for all questions and study sessions
   - `StudySession`: Tracks individual study sessions and results

2. **Spaced Repetition Scheduler** (`spaced_repetition.py`)
   - Implements SM-2 algorithm for optimal review scheduling
   - Adjusts intervals based on answer accuracy and response time
   - Provides review forecasting and workload optimization

3. **ELO Rating System** (`elo_rating.py`)
   - Calculates question difficulty based on user performance
   - Tracks user skill progression over time
   - Recommends appropriate questions for each user's level

4. **Question Bank Manager** (`manager.py`)
   - High-level API for all operations
   - Manages study sessions and user interactions
   - Handles data persistence and statistics

### Key Algorithms

#### Spaced Repetition (SM-2 Based)
- **Correct Answer**: Interval increases by ease factor
- **Incorrect Answer**: Interval resets to 1 day, ease factor decreases
- **Ease Factor**: Adjusts based on performance (1.3 to 3.0 range)

#### ELO Rating System
- Questions and users both have ratings (starting at 1200)
- Ratings adjust based on expected vs. actual performance
- K-factor of 32 for moderate rating changes

## Data Structure

### Question Format
```json
{
  "id": "uuid",
  "question_text": "What is 2 + 2?",
  "answers": [
    {
      "id": "uuid",
      "text": "4",
      "is_correct": true,
      "explanation": "Basic arithmetic"
    }
  ],
  "tags": ["math", "arithmetic"],
  "elo_rating": 1200.0,
  "times_answered": 10,
  "times_correct": 8,
  "next_review": "2024-01-15T10:00:00",
  "interval_days": 7.0,
  "ease_factor": 2.5
}
```

## API Reference

### QuestionBankManager

#### Question Management
- `add_question()`: Add new question with answers and tags
- `create_multiple_choice_question()`: Convenience method for MC questions
- `remove_question()`: Delete question by ID
- `search_questions()`: Full-text search
- `get_questions_by_tag()`: Filter by tags

#### Study Sessions  
- `start_study_session()`: Begin new session with due questions
- `answer_question()`: Submit answer and get feedback
- `skip_question()`: Skip question without penalty
- `end_study_session()`: Complete session and get statistics

#### Analytics
- `get_user_statistics()`: Comprehensive user stats
- `get_review_forecast()`: Upcoming review schedule
- `get_difficult_questions()`: Questions you struggle with
- `suggest_study_session_size()`: Optimal session length

#### Data Management
- `export_bank()`: Save to JSON file
- `import_bank()`: Load from JSON file

## Configuration

### Spaced Repetition Settings
```python
scheduler = SpacedRepetitionScheduler(
    min_ease_factor=1.3,       # Minimum ease multiplier
    max_ease_factor=3.0,       # Maximum ease multiplier
    initial_ease_factor=2.5,   # Starting ease for new questions
    ease_bonus=0.15,           # Ease increase for correct answers
    ease_penalty=0.2,          # Ease decrease for wrong answers
    min_interval=1.0,          # Minimum days between reviews
    max_interval=365.0         # Maximum days between reviews
)
```

### ELO Rating Settings
```python
elo_system = ELORatingSystem(
    k_factor=32,               # Rating change sensitivity
    initial_rating=1200        # Starting rating for questions/users
)
```

## Advanced Usage

### Custom Question Types
You can extend the system by creating custom question formats:

```python
# Create question with detailed explanations
explanations = {
    "Paris": "Paris is the capital and largest city of France",
    "London": "London is the capital of the United Kingdom",
    # ...
}

question = manager.add_question(
    "What is the capital of France?",
    "Paris",
    ["London", "Berlin", "Madrid"],
    tags={"geography", "france", "capitals"},
    explanations=explanations
)
```

### Bulk Import
```python
questions_data = [
    {
        "question": "What is 2 + 2?",
        "correct_answer": "4", 
        "wrong_answers": ["3", "5", "6"],
        "tags": ["math", "arithmetic"]
    },
    # ... more questions
]

questions = manager.bulk_add_questions(questions_data)
```

### Session Filtering
```python
# Study only specific topics
questions = manager.start_study_session(
    max_questions=10,
    tags_filter={"python", "programming"},
    difficulty_range=(1000, 1400)  # Intermediate level
)
```

## Performance & Scalability

- **Memory Efficient**: Questions loaded on-demand for large banks
- **Fast Search**: Optimized text search with caching
- **Scalable**: Tested with 10,000+ questions
- **Persistent**: Automatic saving of progress and statistics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests (`pytest`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by Anki's spaced repetition algorithm
- ELO rating system based on chess rating calculations
- SM-2 algorithm by Piotr Wozniak
