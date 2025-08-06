"""
Simple command-line interface for the Question Bank system.
"""

import argparse
import sys
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
    
    # List questions command
    subparsers.add_parser("list", help="List all questions")
    
    # Study command
    subparsers.add_parser("study", help="Start a study session")
    
    # Stats command
    subparsers.add_parser("stats", help="Show statistics")
    
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
            
        elif args.command == "list":
            list_questions(manager)
            
        elif args.command == "study":
            start_study_session_interactive(manager)
            
        elif args.command == "stats":
            show_statistics(manager)
            
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
