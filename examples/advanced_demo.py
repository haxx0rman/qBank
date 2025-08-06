"""
Example script showing advanced usage of the Question Bank system.
"""

from qbank import QuestionBankManager
import random


def create_comprehensive_question_bank():
    """Create a comprehensive question bank with various subjects."""
    
    manager = QuestionBankManager("Comprehensive Study Bank", "student_001")
    
    # Math questions
    math_questions = [
        {
            "question": "What is the derivative of x²?",
            "correct_answer": "2x",
            "wrong_answers": ["x²", "x", "2x²"],
            "tags": ["math", "calculus", "derivatives"]
        },
        {
            "question": "What is the integral of 2x?",
            "correct_answer": "x² + C",
            "wrong_answers": ["2x² + C", "x + C", "2"],
            "tags": ["math", "calculus", "integrals"]
        },
        {
            "question": "What is the quadratic formula?",
            "correct_answer": "x = (-b ± √(b²-4ac)) / 2a",
            "wrong_answers": ["x = (-b ± √(b²+4ac)) / 2a", "x = (b ± √(b²-4ac)) / 2a", "x = (-b ± √(b²-4ac)) / a"],
            "tags": ["math", "algebra", "quadratic"]
        }
    ]
    
    # Science questions
    science_questions = [
        {
            "question": "What is the speed of light in vacuum?",
            "correct_answer": "299,792,458 m/s",
            "wrong_answers": ["300,000,000 m/s", "299,792,458 km/s", "186,000 m/s"],
            "tags": ["physics", "constants", "light"]
        },
        {
            "question": "What is the chemical formula for water?",
            "correct_answer": "H₂O",
            "wrong_answers": ["H₂O₂", "HO", "H₃O"],
            "tags": ["chemistry", "compounds", "basic"]
        },
        {
            "question": "What is the powerhouse of the cell?",
            "correct_answer": "Mitochondria",
            "wrong_answers": ["Nucleus", "Ribosome", "Endoplasmic reticulum"],
            "tags": ["biology", "cell", "organelles"]
        }
    ]
    
    # Programming questions
    programming_questions = [
        {
            "question": "Which data structure uses LIFO (Last In, First Out)?",
            "correct_answer": "Stack",
            "wrong_answers": ["Queue", "Array", "Linked List"],
            "tags": ["programming", "data-structures", "stack"]
        },
        {
            "question": "What does 'Big O' notation describe?",
            "correct_answer": "Time or space complexity",
            "wrong_answers": ["Code readability", "Memory usage only", "Execution speed only"],
            "tags": ["programming", "algorithms", "complexity"]
        },
        {
            "question": "In Python, what does the 'len()' function return?",
            "correct_answer": "The number of items in an object",
            "wrong_answers": ["The memory size of an object", "The type of an object", "The ID of an object"],
            "tags": ["programming", "python", "built-ins"]
        }
    ]
    
    # History questions
    history_questions = [
        {
            "question": "In which year did World War II end?",
            "correct_answer": "1945",
            "wrong_answers": ["1944", "1946", "1943"],
            "tags": ["history", "world-war", "20th-century"]
        },
        {
            "question": "Who was the first President of the United States?",
            "correct_answer": "George Washington",
            "wrong_answers": ["Thomas Jefferson", "John Adams", "Benjamin Franklin"],
            "tags": ["history", "usa", "presidents"]
        }
    ]
    
    # Add all questions
    all_questions = math_questions + science_questions + programming_questions + history_questions
    manager.bulk_add_questions(all_questions)
    
    print(f"Created question bank with {len(all_questions)} questions across multiple subjects.")
    return manager


def simulate_learning_progress(manager: QuestionBankManager, sessions: int = 10):
    """Simulate a student's learning progress over multiple sessions."""
    
    print(f"\nSimulating {sessions} study sessions...")
    
    for session_num in range(1, sessions + 1):
        print(f"\n--- Session {session_num} ---")
        
        # Start session
        questions = manager.start_study_session(max_questions=5)
        
        if not questions:
            print("No questions due for review!")
            # End empty session if one was started
            if manager.current_session:
                manager.end_study_session()
            continue
        
        session_correct = 0
        
        for question in questions:
            # Simulate getting progressively better (learning effect)
            learning_factor = min(0.9, 0.4 + (session_num * 0.05))
            is_correct = random.random() < learning_factor
            
            if is_correct:
                selected_answer = question.correct_answer
                session_correct += 1
            else:
                incorrect_answers = question.incorrect_answers
                selected_answer = random.choice(incorrect_answers)
            
            # Submit answer with random response time
            response_time = random.uniform(3.0, 15.0)
            manager.answer_question(question.id, selected_answer.id, response_time)
        
        # End session and show results
        session = manager.end_study_session()
        print(f"Completed: {session_correct}/{len(questions)} correct ({session.accuracy:.1f}%)")
        
        # Show user progress
        stats = manager.get_user_statistics()
        print(f"User rating: {stats['user_rating']:.1f} ({stats['user_level']})")
    
    return manager


def analyze_performance(manager: QuestionBankManager):
    """Analyze the user's performance and provide insights."""
    
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS")
    print("="*60)
    
    # Overall statistics
    stats = manager.get_user_statistics()
    print(f"Overall Performance:")
    print(f"  User Level: {stats['user_level']}")
    print(f"  User Rating: {stats['user_rating']:.1f}")
    print(f"  Recent Accuracy: {stats['recent_accuracy']:.1f}%")
    print(f"  Total Sessions: {stats['total_sessions']}")
    print(f"  Questions Due: {stats['questions_due']}")
    
    # Subject analysis
    print(f"\nSubject Performance:")
    subjects = {"math": [], "science": [], "programming": [], "history": []}
    
    for question in manager.question_bank.questions.values():
        if question.times_answered > 0:
            for subject in subjects.keys():
                if subject in question.tags:
                    subjects[subject].append(question.accuracy)
                    break
    
    for subject, accuracies in subjects.items():
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)
            print(f"  {subject.capitalize()}: {avg_accuracy:.1f}% (from {len(accuracies)} questions)")
    
    # Difficult questions
    difficult_questions = manager.get_difficult_questions(5)
    if difficult_questions:
        print(f"\nMost Challenging Questions:")
        for i, q in enumerate(difficult_questions, 1):
            print(f"  {i}. {q.question_text[:50]}...")
            print(f"     Accuracy: {q.accuracy:.1f}% | Difficulty: {manager.elo_system.get_difficulty_category(q.elo_rating)}")
    
    # Review forecast
    forecast = manager.get_review_forecast(7)
    print(f"\nUpcoming Reviews (next 7 days):")
    total_upcoming = 0
    for date, count in forecast.items():
        if count > 0:
            print(f"  {date}: {count} questions")
            total_upcoming += count
    
    if total_upcoming == 0:
        print("  No reviews scheduled - great job staying on top of your studies!")
    
    # Study recommendations
    print(f"\nRecommendations:")
    if stats['recent_accuracy'] < 70:
        print("  • Focus on reviewing incorrect answers and their explanations")
        print("  • Consider shorter, more frequent study sessions")
    elif stats['recent_accuracy'] > 85:
        print("  • Great job! Consider adding more challenging questions")
        print("  • Try studying different subjects to broaden knowledge")
    else:
        print("  • Good progress! Maintain consistent study schedule")
    
    if stats['questions_due'] > 10:
        print(f"  • You have {stats['questions_due']} questions due - consider a longer session")


def demonstrate_advanced_features(manager: QuestionBankManager):
    """Demonstrate advanced features like filtering and search."""
    
    print("\n" + "="*60)
    print("ADVANCED FEATURES DEMO")
    print("="*60)
    
    # Search functionality
    print("Search Results for 'derivative':")
    search_results = manager.search_questions("derivative")
    for result in search_results:
        print(f"  • {result.question_text}")
    
    print(f"\nQuestions tagged with 'programming':")
    programming_questions = manager.get_questions_by_tag("programming")
    for q in programming_questions[:3]:  # Show first 3
        print(f"  • {q.question_text}")
    
    # Filtered study session
    print(f"\nStarting focused study session on 'math' topics...")
    math_session = manager.start_study_session(
        max_questions=3,
        tags_filter={"math"}
    )
    
    if math_session:
        print(f"Found {len(math_session)} math questions for review:")
        for q in math_session:
            print(f"  • {q.question_text}")
        
        # End the session without answering
        manager.end_study_session()
    
    # ELO-based recommendations
    user_rating = manager.user_tracker.get_user_rating(manager.current_user_id)
    all_questions = list(manager.question_bank.questions.values())
    recommended = manager.user_tracker.get_recommended_questions(
        manager.current_user_id, all_questions
    )
    
    print(f"\nTop 3 questions recommended for your skill level ({user_rating:.0f}):")
    for i, q in enumerate(recommended[:3], 1):
        success_prob = manager.elo_system.predict_success_probability(user_rating, q.elo_rating)
        print(f"  {i}. {q.question_text[:50]}...")
        print(f"     Predicted success rate: {success_prob:.1%}")


def main():
    """Main demonstration function."""
    
    print("Advanced Question Bank Features Demo")
    print("="*60)
    
    # Create comprehensive question bank
    manager = create_comprehensive_question_bank()
    
    # Simulate learning progress
    manager = simulate_learning_progress(manager, sessions=8)
    
    # Analyze performance
    analyze_performance(manager)
    
    # Demonstrate advanced features
    demonstrate_advanced_features(manager)
    
    # Export the results
    manager.export_bank("advanced_demo_bank.json")
    print(f"\nDemo completed! Question bank exported to 'advanced_demo_bank.json'")
    print("This file contains all questions, study history, and progress data.")


if __name__ == "__main__":
    main()
