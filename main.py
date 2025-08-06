#!/usr/bin/env python3
"""
Example usage of the Question Bank system.
"""

from qbank import QuestionBankManager


def create_sample_questions(manager: QuestionBankManager):
    """Create some sample questions for demonstration."""
    
    # Sample questions for different subjects
    sample_questions = [
        {
            "question": "What is the capital of France?",
            "correct_answer": "Paris",
            "wrong_answers": ["London", "Berlin", "Madrid"],
            "tags": ["geography", "europe", "capitals"],
            "objective": "Test knowledge of European capital cities"
        },
        {
            "question": "What is 2 + 2?",
            "correct_answer": "4",
            "wrong_answers": ["3", "5", "6"],
            "tags": ["math", "arithmetic", "basic"],
            "objective": "Assess basic arithmetic skills"
        },
        {
            "question": "Who wrote 'Romeo and Juliet'?",
            "correct_answer": "William Shakespeare",
            "wrong_answers": ["Charles Dickens", "Jane Austen", "Mark Twain"],
            "tags": ["literature", "shakespeare", "plays"],
            "objective": "Evaluate knowledge of classic English literature authors"
        },
        {
            "question": "What is the largest planet in our solar system?",
            "correct_answer": "Jupiter",
            "wrong_answers": ["Saturn", "Earth", "Mars"],
            "tags": ["science", "astronomy", "planets"],
            "objective": "Test understanding of planetary characteristics"
        },
        {
            "question": "In Python, which keyword is used to create a function?",
            "correct_answer": "def",
            "wrong_answers": ["function", "create", "make"],
            "tags": ["programming", "python", "syntax"],
            "objective": "Assess knowledge of Python function definition syntax"
        }
    ]
    
    print("Adding sample questions...")
    created_questions = manager.bulk_add_questions(sample_questions)
    print(f"Added {len(created_questions)} questions to the bank.")
    
    return created_questions


def demonstrate_study_session(manager: QuestionBankManager):
    """Demonstrate a study session."""
    
    print("\n" + "="*50)
    print("STARTING STUDY SESSION")
    print("="*50)
    
    # Get user stats before session
    stats_before = manager.get_user_statistics()
    print(f"User Level: {stats_before['user_level']}")
    print(f"User Rating: {stats_before['user_rating']:.1f}")
    print(f"Questions due for review: {stats_before['questions_due']}")
    
    # Start a study session
    questions = manager.start_study_session(max_questions=3)
    
    if not questions:
        print("No questions due for review!")
        return
    
    print(f"\nStarting session with {len(questions)} questions:")
    
    # Simulate answering questions
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question.question_text}")
        print("Options:")
        
        # Shuffle answers for display
        import random
        answers = question.answers.copy()
        random.shuffle(answers)
        
        for j, answer in enumerate(answers, 1):
            print(f"  {j}. {answer.text}")
        
        # Simulate user choice (for demo, sometimes right, sometimes wrong)
        if i % 2 == 1:  # Get odd questions right
            selected_answer = question.correct_answer or question.answers[0]
        else:  # Get even questions wrong
            incorrect_answers = question.incorrect_answers
            selected_answer = incorrect_answers[0] if incorrect_answers else question.answers[-1]
        
        print(f"\nSelected: {selected_answer.text}")
        
        # Submit answer
        result = manager.answer_question(question.id, selected_answer.id, response_time=5.0)
        
        if result['correct']:
            print("✓ Correct!")
        else:
            print("✗ Incorrect!")
            print(f"Correct answer: {result['correct_answer'].text}")
        
        if result['selected_answer'].explanation:
            print(f"Explanation: {result['selected_answer'].explanation}")
        
        print(f"Question difficulty: {manager.elo_system.get_difficulty_category(result['question_rating'])}")
        print(f"Your rating: {result['user_rating']:.1f}")
        print(f"Next review: {result['next_review'].strftime('%Y-%m-%d %H:%M')}")
    
    # End session
    session = manager.end_study_session()
    print(f"\nSession completed!")
    print(f"Duration: {session.duration}")
    print(f"Accuracy: {session.accuracy:.1f}%")
    print(f"Correct: {session.correct_count}, Incorrect: {session.incorrect_count}")
    
    # Show updated stats
    stats_after = manager.get_user_statistics()
    rating_change = stats_after['user_rating'] - stats_before['user_rating']
    print(f"\nRating change: {rating_change:+.1f}")
    print(f"New level: {stats_after['user_level']}")


def show_statistics(manager: QuestionBankManager):
    """Show various statistics."""
    
    print("\n" + "="*50)
    print("STATISTICS")
    print("="*50)
    
    # User statistics
    user_stats = manager.get_user_statistics()
    print("User Statistics:")
    for key, value in user_stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Bank statistics
    bank_stats = manager.question_bank.get_statistics()
    print(f"\nBank Statistics:")
    print(f"  Total Questions: {bank_stats['total_questions']}")
    print(f"  Total Sessions: {bank_stats['total_sessions']}")
    print(f"  Average Accuracy: {bank_stats['average_accuracy']:.1f}%")
    print(f"  Questions Due for Review: {bank_stats['questions_due_for_review']}")
    
    # Most used tags
    if bank_stats['most_studied_tags']:
        print(f"\nMost Used Tags:")
        for tag, count in bank_stats['most_studied_tags']:
            print(f"  {tag}: {count} questions")
    
    # Difficult questions
    difficult_questions = manager.get_difficult_questions(3)
    if difficult_questions:
        print(f"\nMost Difficult Questions:")
        for q in difficult_questions:
            print(f"  - {q.question_text[:50]}... (Accuracy: {q.accuracy:.1f}%)")
    
    # Review forecast
    forecast = manager.get_review_forecast(7)
    print(f"\n7-Day Review Forecast:")
    for date, count in forecast.items():
        print(f"  {date}: {count} questions")


def main():
    """Main demonstration function."""
    
    print("Question Bank System Demo")
    print("="*50)
    
    # Create manager
    manager = QuestionBankManager("Demo Question Bank", "demo_user")
    
    # Add sample questions
    create_sample_questions(manager)
    
    # Show initial statistics
    show_statistics(manager)
    
    # Demonstrate study session
    demonstrate_study_session(manager)
    
    # Show final statistics
    show_statistics(manager)
    
    # Export example
    print(f"\nExporting question bank to 'demo_bank.json'...")
    manager.export_bank("demo_bank.json")
    print("Export completed!")
    
    print(f"\nDemo completed! Check 'demo_bank.json' for the exported data.")


if __name__ == "__main__":
    main()
