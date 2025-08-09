"""
Enhanced command-line interface for the Question Bank system.
"""

import argparse
import sys
import csv
import time
from pathlib import Path
from qbank import QuestionBankManager


def create_question_interactive(manager: QuestionBankManager):
    """Interactively create a new question."""
    print("\nCreating a new question...")
    
    question_text = input("Enter the question: ").strip()
    if not question_text:
        print("Question text cannot be empty!")
        return
    
    correct_answer = input("Enter the correct answer: ").strip()
    if not correct_answer:
        print("Correct answer cannot be empty!")
        return
    
    wrong_answers = []
    print("\nEnter incorrect answers (press Enter with empty line to finish):")
    while True:
        wrong_answer = input(f"Wrong answer {len(wrong_answers) + 1}: ").strip()
        if not wrong_answer:
            break
        wrong_answers.append(wrong_answer)
    
    if len(wrong_answers) < 1:
        print("At least one wrong answer is required!")
        return
    
    tags_input = input("\nEnter tags (comma-separated, optional): ").strip()
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else []
    
    objective = input("\nEnter learning objective (what this question tests, optional): ").strip()
    objective = objective if objective else None
    
    # Create the question
    question = manager.create_multiple_choice_question(
        question_text, correct_answer, wrong_answers, tags, objective
    )
    
    print(f"\n✓ Question created successfully! ID: {question.id}")
    print(f"Tags: {', '.join(question.tags) if question.tags else 'None'}")


def bulk_import_questions(manager: QuestionBankManager, file_path: str):
    """Import questions from a CSV file."""
    print(f"\n=== Bulk Import from {file_path} ===")
    
    try:
        questions_added = 0
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            expected_headers = ['question', 'correct_answer', 'wrong_answer1', 'wrong_answer2', 'tags', 'objective']
            
            if not all(header in reader.fieldnames for header in expected_headers[:3]):
                print("CSV must have at least: question, correct_answer, wrong_answer1, wrong_answer2")
                print(f"Expected headers: {', '.join(expected_headers)}")
                print(f"Found headers: {', '.join(reader.fieldnames)}")
                return
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    wrong_answers = []
                    
                    # Add wrong answers
                    for i in range(1, 6):  # Support up to 5 wrong answers
                        wrong_key = f'wrong_answer{i}'
                        if wrong_key in row and row[wrong_key].strip():
                            wrong_answers.append(row[wrong_key].strip())
                    
                    if not wrong_answers:
                        print(f"Warning: Row {row_num} has no wrong answers, skipping")
                        continue
                    
                    # Parse tags
                    tags = []
                    if 'tags' in row and row['tags'].strip():
                        tags = [tag.strip() for tag in row['tags'].split(',')]
                    
                    # Get objective
                    objective = row.get('objective', '').strip() or None
                    
                    # Create question
                    manager.create_multiple_choice_question(
                        question_text=row['question'].strip(),
                        correct_answer=row['correct_answer'].strip(),
                        wrong_answers=wrong_answers,
                        tags=tags,
                        objective=objective
                    )
                    questions_added += 1
                    
                except Exception as e:
                    print(f"Error on row {row_num}: {e}")
                    continue
        
        print(f"\n✓ Successfully imported {questions_added} questions!")
        
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")


def search_questions(manager: QuestionBankManager, query: str):
    """Search for questions."""
    print(f"\n=== Search Results for '{query}' ===")
    
    results = manager.search_questions(query)
    
    if not results:
        print("No questions found matching your search.")
        return
    
    print(f"Found {len(results)} question(s):")
    for i, question in enumerate(results, 1):
        print(f"\n{i}. {question.question_text}")
        print(f"   Tags: {', '.join(question.tags) if question.tags else 'None'}")
        print(f"   Difficulty: {manager.elo_system.get_difficulty_category(question.elo_rating)}")
        print(f"   Accuracy: {question.accuracy:.1f}% ({question.times_correct}/{question.times_answered})")


def practice_by_subject(manager: QuestionBankManager, subject: str = None):
    """Start a focused practice session by subject/tag."""
    print("\n=== Practice Session ===")
    
    # Get available tags if no subject specified
    if not subject:
        all_tags = set()
        for question in manager.question_bank.questions.values():
            all_tags.update(question.tags)
        
        if not all_tags:
            print("No tags found in question bank.")
            return
        
        print("Available subjects:")
        tags_list = sorted(all_tags)
        for i, tag in enumerate(tags_list, 1):
            count = len(manager.get_questions_by_tag(tag))
            print(f"  {i}. {tag} ({count} questions)")
        
        print(f"  {len(tags_list) + 1}. All subjects (mixed practice)")
        
        while True:
            try:
                choice = input(f"\nSelect subject (1-{len(tags_list) + 1}): ").strip()
                choice_idx = int(choice) - 1
                
                if choice_idx == len(tags_list):
                    selected_tags = None
                    break
                elif 0 <= choice_idx < len(tags_list):
                    selected_tags = {tags_list[choice_idx]}
                    break
                else:
                    print(f"Please enter a number between 1 and {len(tags_list) + 1}")
            except ValueError:
                print("Please enter a valid number")
    else:
        selected_tags = {subject}
    
    # Get number of questions
    while True:
        try:
            max_questions = input("Number of questions (default 10): ").strip()
            max_questions = int(max_questions) if max_questions else 10
            if max_questions > 0:
                break
            else:
                print("Please enter a positive number")
        except ValueError:
            print("Please enter a valid number")
    
    # Start study session
    questions = manager.start_study_session(
        max_questions=max_questions,
        tags_filter=selected_tags
    )
    
    if not questions:
        if selected_tags:
            print(f"No questions available for subject: {', '.join(selected_tags)}")
        else:
            print("No questions available for practice!")
        return
    
    # Practice session
    correct_count = 0
    start_time = time.time()
    
    print(f"\nStarting practice session with {len(questions)} questions...")
    if selected_tags:
        print(f"Subject: {', '.join(selected_tags)}")
    print("Enter 'q' to quit early\n")
    
    for i, question in enumerate(questions, 1):
        print(f"Question {i}/{len(questions)}")
        print(f"Tags: {', '.join(question.tags)}")
        print(f"Difficulty: {manager.elo_system.get_difficulty_category(question.elo_rating)}")
        print(f"\n{question.question_text}")
        
        # Show answers in random order
        import random
        answers = question.answers.copy()
        random.shuffle(answers)
        
        print("\nOptions:")
        for j, answer in enumerate(answers, 1):
            print(f"  {j}. {answer.text}")
        
        # Get user response
        while True:
            response = input(f"\nYour answer (1-{len(answers)}) or 'q' to quit: ").strip().lower()
            
            if response == 'q':
                print("Session ended early.")
                manager.end_study_session()
                return
            
            try:
                answer_idx = int(response) - 1
                if 0 <= answer_idx < len(answers):
                    selected_answer = answers[answer_idx]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(answers)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
        
        # Submit answer with timing
        question_start = time.time()
        result = manager.answer_question(question.id, selected_answer.id, time.time() - question_start)
        
        # Show result
        if result['correct']:
            correct_count += 1
            print("✓ Correct!")
        else:
            print("✗ Incorrect!")
            print(f"The correct answer was: {result['correct_answer'].text}")
        
        if selected_answer.explanation:
            print(f"Explanation: {selected_answer.explanation}")
        
        print(f"Your rating: {result['user_rating']:.1f}")
        print()
    
    # End session and show results
    session = manager.end_study_session()
    
    print("=" * 50)
    print("SESSION COMPLETE!")
    print("=" * 50)
    print(f"Score: {correct_count}/{len(questions)} ({session.accuracy:.1f}%)")
    print(f"Duration: {session.duration}")
    print(f"Your rating: {manager.user_tracker.get_user_rating(manager.current_user_id):.1f}")


def reset_progress(manager: QuestionBankManager):
    """Reset user progress (with confirmation)."""
    print("\n⚠️  WARNING: This will reset ALL your progress!")
    print("This includes:")
    print("  - All study session history")
    print("  - Question ratings and statistics")
    print("  - Your user rating")
    print("  - Spaced repetition schedules")
    
    confirm = input("\nType 'RESET' to confirm: ").strip()
    
    if confirm == 'RESET':
        # Reset user progress
        manager.user_tracker.users[manager.current_user_id] = type(manager.user_tracker.users[manager.current_user_id])()
        
        # Reset question statistics
        for question in manager.question_bank.questions.values():
            question.elo_rating = 1200.0
            question.times_answered = 0
            question.times_correct = 0
            question.last_studied = None
            question.next_review = None
            question.interval_days = 1.0
            question.ease_factor = 2.5
            question.repetition_count = 0
        
        print("✓ Progress reset successfully!")
    else:
        print("Reset cancelled.")


def list_questions(manager: QuestionBankManager):
    """List all questions in the bank."""
    questions = list(manager.question_bank.questions.values())
    
    if not questions:
        print("No questions in the bank.")
        return
    
    print(f"\nFound {len(questions)} questions:")
    print("-" * 80)
    
    for i, question in enumerate(questions, 1):
        print(f"{i}. {question.question_text}")
        print(f"   Correct: {question.correct_answer.text if question.correct_answer else 'N/A'}")
        if question.objective:
            print(f"   Objective: {question.objective}")
        print(f"   Tags: {', '.join(question.tags) if question.tags else 'None'}")
        print(f"   Difficulty: {manager.elo_system.get_difficulty_category(question.elo_rating)}")
        print(f"   Accuracy: {question.accuracy:.1f}% ({question.times_correct}/{question.times_answered})")
        print()


def start_study_session_interactive(manager: QuestionBankManager):
    """Start an interactive study session."""
    
    # Check if there are questions due
    due_questions = manager.question_bank.get_questions_due_for_review()
    if not due_questions:
        print("No questions are due for review!")
        return
    
    print(f"\n{len(due_questions)} questions are due for review.")
    
    # Ask for session size
    max_questions = input(f"How many questions? (max {len(due_questions)}, Enter for all): ").strip()
    if max_questions:
        try:
            max_questions = int(max_questions)
            max_questions = min(max_questions, len(due_questions))
        except ValueError:
            max_questions = None
    else:
        max_questions = None
    
    # Start session
    questions = manager.start_study_session(max_questions=max_questions)
    
    if not questions:
        print("No questions available for study session.")
        return
    
    print(f"\nStarting study session with {len(questions)} questions...")
    print("=" * 50)
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}/{len(questions)}: {question.question_text}")
        
        # Show answers in random order
        import random
        answers = question.answers.copy()
        random.shuffle(answers)
        
        print("Options:")
        for j, answer in enumerate(answers, 1):
            print(f"  {j}. {answer.text}")
        
        # Get user choice
        while True:
            try:
                choice = input(f"\nYour answer (1-{len(answers)}): ").strip()
                if choice.lower() in ['q', 'quit', 'exit']:
                    print("Exiting study session...")
                    return
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(answers):
                    selected_answer = answers[choice_num - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(answers)}")
            except ValueError:
                print("Please enter a valid number or 'q' to quit")
        
        # Submit answer
        result = manager.answer_question(question.id, selected_answer.id)
        
        # Show result
        if result['correct']:
            print("✓ Correct!")
        else:
            print("✗ Incorrect!")
            print(f"The correct answer was: {result['correct_answer'].text}")
        
        if selected_answer.explanation:
            print(f"Explanation: {selected_answer.explanation}")
        
        print(f"Question difficulty: {manager.elo_system.get_difficulty_category(result['question_rating'])}")
        print(f"Your rating: {result['user_rating']:.1f}")
    
    # End session and show results
    session = manager.end_study_session()
    
    print("\n" + "=" * 50)
    print("SESSION COMPLETE!")
    print("=" * 50)
    print(f"Questions answered: {session.questions_count}")
    print(f"Correct: {session.correct_count}")
    print(f"Incorrect: {session.incorrect_count}")
    print(f"Accuracy: {session.accuracy:.1f}%")
    print(f"Duration: {session.duration}")
    
    # Show updated user stats
    stats = manager.get_user_statistics()
    print(f"\nYour current level: {stats['user_level']}")
    print(f"Your rating: {stats['user_rating']:.1f}")


def show_statistics(manager: QuestionBankManager):
    """Show system statistics."""
    
    print("\n" + "=" * 50)
    print("QUESTION BANK STATISTICS")
    print("=" * 50)
    
    # User stats
    user_stats = manager.get_user_statistics()
    print("Your Statistics:")
    print(f"  Level: {user_stats['user_level']}")
    print(f"  Rating: {user_stats['user_rating']:.1f}")
    print(f"  Recent Accuracy: {user_stats['recent_accuracy']:.1f}%")
    print(f"  Total Sessions: {user_stats['total_sessions']}")
    print(f"  Questions Due: {user_stats['questions_due']}")
    
    # Bank stats
    bank_stats = manager.question_bank.get_statistics()
    print(f"\nBank Statistics:")
    print(f"  Total Questions: {bank_stats['total_questions']}")
    print(f"  Average Accuracy: {bank_stats['average_accuracy']:.1f}%")
    
    # Review forecast
    forecast = manager.get_review_forecast(7)
    print(f"\n7-Day Review Forecast:")
    for date, count in forecast.items():
        if count > 0:
            print(f"  {date}: {count} questions")


def show_detailed_stats(manager: QuestionBankManager):
    """Show detailed statistics with charts and insights."""
    stats = manager.get_user_statistics()
    
    print("\n" + "="*60)
    print("DETAILED STATISTICS")
    print("="*60)
    
    # User overview
    print(f"User Level: {stats['user_level']} (Rating: {stats['user_rating']:.1f})")
    print(f"Total Questions: {stats['total_questions']}")
    print(f"Questions Due: {stats['questions_due']}")
    print(f"Total Sessions: {stats['total_sessions']}")
    print(f"Recent Accuracy: {stats['recent_accuracy']:.1f}%")
    
    # Subject breakdown
    print(f"\nSubject Performance:")
    subjects = {}
    for question in manager.question_bank.questions.values():
        if question.times_answered > 0:
            for tag in question.tags:
                if tag not in subjects:
                    subjects[tag] = {'correct': 0, 'total': 0}
                subjects[tag]['correct'] += question.times_correct
                subjects[tag]['total'] += question.times_answered
    
    for subject, data in sorted(subjects.items()):
        accuracy = (data['correct'] / data['total']) * 100 if data['total'] > 0 else 0
        print(f"  {subject}: {accuracy:.1f}% ({data['correct']}/{data['total']})")
    
    # Difficulty distribution
    print(f"\nDifficulty Distribution:")
    difficulties = {"Beginner": 0, "Easy": 0, "Medium": 0, "Hard": 0, "Expert": 0}
    for question in manager.question_bank.questions.values():
        difficulty = manager.elo_system.get_difficulty_category(question.elo_rating)
        difficulties[difficulty] += 1
    
    for difficulty, count in difficulties.items():
        if count > 0:
            percentage = (count / len(manager.question_bank.questions)) * 100
            print(f"  {difficulty}: {count} questions ({percentage:.1f}%)")
    
    # Review forecast
    forecast = manager.get_review_forecast(14)
    print(f"\nUpcoming Reviews (next 14 days):")
    for date, count in forecast.items():
        if count > 0:
            print(f"  {date}: {count} questions")


def main():
    """Main CLI function."""
    
    parser = argparse.ArgumentParser(description="Question Bank - Spaced Repetition Learning System")
    parser.add_argument("--bank", "-b", default="questions.json", 
                       help="Question bank file (default: questions.json)")
    parser.add_argument("--user", "-u", default="default_user",
                       help="User ID (default: default_user)")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add question command
    subparsers.add_parser("add", help="Add a new question interactively")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import questions from CSV file")
    import_parser.add_argument("file", help="CSV file path")
    
    # List questions command
    subparsers.add_parser("list", help="List all questions")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search questions")
    search_parser.add_argument("query", help="Search query")
    
    # Study command
    subparsers.add_parser("study", help="Start a study session")
    
    # Practice command
    practice_parser = subparsers.add_parser("practice", help="Practice by subject")
    practice_parser.add_argument("--subject", "-s", help="Subject/tag to practice")
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
    # Detailed stats command
    subparsers.add_parser("detailed-stats", help="Show detailed statistics")
    
    # Reset command
    subparsers.add_parser("reset", help="Reset user progress")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export question bank")
    export_parser.add_argument("file", help="Output file path")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create manager
    manager = QuestionBankManager("Question Bank", args.user)
    
    # Load existing bank if it exists
    bank_file = Path(args.bank)
    if bank_file.exists():
        try:
            manager.import_bank(str(bank_file))
            print(f"Loaded question bank from {bank_file}")
        except Exception as e:
            print(f"Error loading bank file: {e}")
            return
    else:
        print(f"Creating new question bank: {bank_file}")
    
    # Execute command
    try:
        if args.command == "add":
            create_question_interactive(manager)
            
        elif args.command == "import":
            bulk_import_questions(manager, args.file)
            
        elif args.command == "list":
            list_questions(manager)
            
        elif args.command == "search":
            search_questions(manager, args.query)
            
        elif args.command == "study":
            start_study_session_interactive(manager)
            
        elif args.command == "practice":
            practice_by_subject(manager, args.subject)
            
        elif args.command == "stats":
            show_statistics(manager)
            
        elif args.command == "detailed-stats":
            show_detailed_stats(manager)
            
        elif args.command == "reset":
            reset_progress(manager)
            
        elif args.command == "export":
            manager.export_bank(args.file)
            print(f"Exported question bank to {args.file}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Save the bank
    try:
        manager.export_bank(str(bank_file))
        print(f"\nQuestion bank saved to {bank_file}")
    except Exception as e:
        print(f"Error saving bank: {e}")


if __name__ == "__main__":
    main()
