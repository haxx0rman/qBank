"""
Unit tests for the Question Bank system.
"""

import pytest
from datetime import datetime, timedelta
import tempfile
import os

from qbank import QuestionBankManager, Question, Answer, AnswerResult


class TestQuestionBankManager:
    """Test the main QuestionBankManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh manager for each test."""
        return QuestionBankManager("Test Bank", "test_user")
    
    def test_create_question(self, manager):
        """Test creating a basic question."""
        question = manager.create_multiple_choice_question(
            "What is 2 + 2?",
            "4",
            ["3", "5", "6"],
            ["math", "arithmetic"]
        )
        
        assert question.question_text == "What is 2 + 2?"
        assert len(question.answers) == 4
        assert question.correct_answer.text == "4"
        assert len(question.incorrect_answers) == 3
        assert "math" in question.tags
        assert "arithmetic" in question.tags
        assert question.elo_rating == 1200.0  # Starting rating
    
    def test_add_multiple_questions(self, manager):
        """Test adding multiple questions."""
        questions_data = [
            {
                "question": "What is the capital of France?",
                "correct_answer": "Paris",
                "wrong_answers": ["London", "Berlin", "Madrid"],
                "tags": ["geography"]
            },
            {
                "question": "Who wrote Hamlet?",
                "correct_answer": "Shakespeare",
                "wrong_answers": ["Dickens", "Austen", "Twain"],
                "tags": ["literature"]
            }
        ]
        
        created_questions = manager.bulk_add_questions(questions_data)
        
        assert len(created_questions) == 2
        assert len(manager.question_bank.questions) == 2
        
        # Test search functionality
        paris_questions = manager.search_questions("Paris")
        assert len(paris_questions) == 1
        assert paris_questions[0].question_text == "What is the capital of France?"
    
    def test_study_session(self, manager):
        """Test a complete study session."""
        # Add some questions
        manager.create_multiple_choice_question(
            "What is 2 + 2?",
            "4", 
            ["3", "5", "6"],
            ["math"]
        )
        manager.create_multiple_choice_question(
            "What is 3 + 3?",
            "6",
            ["5", "7", "8"], 
            ["math"]
        )
        
        # Start session
        questions = manager.start_study_session()
        assert len(questions) == 2
        assert manager.current_session is not None
        
        # Answer first question correctly
        first_question = questions[0]
        correct_answer = first_question.correct_answer
        result = manager.answer_question(first_question.id, correct_answer.id, 5.0)
        
        assert result['correct'] is True
        assert first_question.times_answered == 1
        assert first_question.times_correct == 1
        assert first_question.next_review is not None
        
        # Answer second question incorrectly
        second_question = questions[1]
        wrong_answer = second_question.incorrect_answers[0]
        result = manager.answer_question(second_question.id, wrong_answer.id, 10.0)
        
        assert result['correct'] is False
        assert second_question.times_answered == 1
        assert second_question.times_correct == 0
        
        # End session
        session = manager.end_study_session()
        assert session.accuracy == 50.0  # 1 correct out of 2
        assert session.correct_count == 1
        assert session.incorrect_count == 1
        assert manager.current_session is None
    
    def test_elo_rating_system(self, manager):
        """Test that ELO ratings change appropriately."""
        question = manager.create_multiple_choice_question(
            "Test question?",
            "Correct",
            ["Wrong1", "Wrong2", "Wrong3"],
            ["test"]
        )
        
        initial_rating = question.elo_rating
        initial_user_rating = manager.user_tracker.get_user_rating("test_user")
        
        # Start session and answer correctly
        questions = manager.start_study_session()
        correct_answer = question.correct_answer
        manager.answer_question(question.id, correct_answer.id, 3.0)
        
        # Question should get easier (lower rating) when answered correctly
        assert question.elo_rating < initial_rating
        
        # User rating should increase
        new_user_rating = manager.user_tracker.get_user_rating("test_user")
        assert new_user_rating > initial_user_rating
    
    def test_spaced_repetition(self, manager):
        """Test spaced repetition scheduling."""
        question = manager.create_multiple_choice_question(
            "Test question?",
            "Correct",
            ["Wrong"],
            ["test"]
        )
        
        # Initially, no next review scheduled
        assert question.next_review is None
        assert question.repetition_count == 0
        assert question.interval_days == 1.0
        
        # Answer correctly
        manager.start_study_session()
        correct_answer = question.correct_answer
        manager.answer_question(question.id, correct_answer.id, 2.0)
        
        # Should now have a scheduled review
        assert question.next_review is not None
        assert question.repetition_count == 1
        assert question.last_studied is not None
        
        # Check that the next review is scheduled in the future
        assert question.next_review > question.last_studied
        
        # For SM-2 algorithm, first correct answer should give 1 day interval
        interval_hours = (question.next_review - question.last_studied).total_seconds() / 3600
        assert 20 <= interval_hours <= 28  # Between 20-28 hours (allowing for some variation)
    
    def test_tags_and_filtering(self, manager):
        """Test tag-based filtering."""
        # Add questions with different tags
        manager.create_multiple_choice_question(
            "Math question 1", "Answer", ["Wrong"], ["math", "easy"]
        )
        manager.create_multiple_choice_question(
            "Math question 2", "Answer", ["Wrong"], ["math", "hard"] 
        )
        manager.create_multiple_choice_question(
            "History question", "Answer", ["Wrong"], ["history"]
        )
        
        # Test filtering by tags
        math_questions = manager.get_questions_by_tag("math")
        assert len(math_questions) == 2
        
        history_questions = manager.get_questions_by_tag("history")
        assert len(history_questions) == 1
        
        # Test getting all tags
        all_tags = manager.get_all_tags()
        expected_tags = {"math", "easy", "hard", "history"}
        assert all_tags == expected_tags
    
    def test_statistics(self, manager):
        """Test statistics gathering."""
        # Add questions and simulate study session
        manager.create_multiple_choice_question(
            "Q1", "Correct", ["Wrong"], ["test"]
        )
        manager.create_multiple_choice_question(
            "Q2", "Correct", ["Wrong"], ["test"]
        )
        
        # Get initial stats
        stats = manager.get_user_statistics()
        assert stats['total_questions'] == 2
        assert stats['total_sessions'] == 0
        assert stats['questions_due'] == 2
        
        # Do a study session
        questions = manager.start_study_session()
        for question in questions:
            manager.answer_question(question.id, question.correct_answer.id, 5.0)
        manager.end_study_session()
        
        # Check updated stats
        stats = manager.get_user_statistics()
        assert stats['total_sessions'] == 1
        assert stats['recent_accuracy'] == 100.0
        assert stats['questions_due'] == 0  # All scheduled for tomorrow
    
    def test_export_import(self, manager):
        """Test exporting and importing question banks."""
        # Add some questions
        manager.create_multiple_choice_question(
            "Export test", "Answer", ["Wrong"], ["export"]
        )
        
        # Do a mini study session
        questions = manager.start_study_session()
        manager.answer_question(questions[0].id, questions[0].correct_answer.id, 3.0)
        manager.end_study_session()
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
            tmp_path = tmp.name
        
        try:
            manager.export_bank(tmp_path)
            
            # Create new manager and import
            new_manager = QuestionBankManager("Imported Bank", "test_user")
            new_manager.import_bank(tmp_path)
            
            # Check that data was imported correctly
            assert len(new_manager.question_bank.questions) == 1
            assert len(new_manager.question_bank.study_sessions) == 1
            
            imported_question = list(new_manager.question_bank.questions.values())[0]
            assert imported_question.question_text == "Export test"
            assert imported_question.times_answered == 1
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestSpacedRepetitionScheduler:
    """Test the spaced repetition scheduler."""
    
    def test_first_correct_answer(self):
        """Test scheduling after first correct answer."""
        from qbank.spaced_repetition import SpacedRepetitionScheduler
        
        scheduler = SpacedRepetitionScheduler()
        
        # Create a question
        question = Question(
            question_text="Test",
            answers=[Answer(text="Answer", is_correct=True)]
        )
        
        # Schedule after first correct answer
        next_review = scheduler.schedule_next_review(question, AnswerResult.CORRECT)
        
        assert question.repetition_count == 1
        assert question.interval_days == 1.0  # First correct answer = 1 day
        assert next_review is not None
    
    def test_incorrect_answer_resets(self):
        """Test that incorrect answers reset the interval."""
        from qbank.spaced_repetition import SpacedRepetitionScheduler
        
        scheduler = SpacedRepetitionScheduler()
        
        # Create a question that's been answered correctly multiple times
        question = Question(
            question_text="Test",
            answers=[Answer(text="Answer", is_correct=True)],
            repetition_count=3,
            interval_days=10.0,
            ease_factor=2.8
        )
        
        # Answer incorrectly
        scheduler.schedule_next_review(question, AnswerResult.INCORRECT)
        
        assert question.repetition_count == 0  # Reset
        assert question.interval_days == 1.0   # Back to 1 day
        assert question.ease_factor < 2.8      # Reduced ease factor


class TestELORatingSystem:
    """Test the ELO rating system."""
    
    def test_rating_changes(self):
        """Test that ratings change appropriately."""
        from qbank.elo_rating import ELORatingSystem
        
        elo = ELORatingSystem()
        
        # User beats an equally-rated question
        user_rating = 1200.0
        question_rating = 1200.0
        
        new_question_rating, new_user_rating = elo.update_ratings(
            question_rating, user_rating, AnswerResult.CORRECT
        )
        
        # User rating should increase, question rating should decrease
        assert new_user_rating > user_rating
        assert new_question_rating < question_rating
    
    def test_difficulty_categories(self):
        """Test difficulty category mapping."""
        from qbank.elo_rating import ELORatingSystem
        
        elo = ELORatingSystem()
        
        assert elo.get_difficulty_category(900) == "Very Easy"
        assert elo.get_difficulty_category(1100) == "Easy"
        assert elo.get_difficulty_category(1300) == "Medium"
        assert elo.get_difficulty_category(1500) == "Hard"
        assert elo.get_difficulty_category(1700) == "Very Hard"
        assert elo.get_difficulty_category(1900) == "Expert"


if __name__ == "__main__":
    pytest.main([__file__])
