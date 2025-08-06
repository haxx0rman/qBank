"""
Main interface for the Question Bank system.
Provides a high-level API for managing questions, study sessions, and spaced repetition.
"""

from datetime import datetime
from typing import List, Optional, Dict, Set
import random

from .models import Question, Answer, QuestionBank, StudySession, AnswerResult
from .spaced_repetition import SpacedRepetitionScheduler
from .elo_rating import ELORatingSystem, UserRatingTracker


class QuestionBankManager:
    """
    Main interface for managing a question bank with spaced repetition and ELO ratings.
    """
    
    def __init__(self, bank_name: str = "My Question Bank", user_id: str = "default_user"):
        """
        Initialize the question bank manager.
        
        Args:
            bank_name: Name for the question bank
            user_id: Identifier for the current user
        """
        self.question_bank = QuestionBank(name=bank_name)
        self.scheduler = SpacedRepetitionScheduler()
        self.elo_system = ELORatingSystem()
        self.user_tracker = UserRatingTracker()
        self.current_user_id = user_id
        self.current_session: Optional[StudySession] = None
    
    # Question Management
    def add_question(self, question_text: str, correct_answer: str, 
                    incorrect_answers: List[str], tags: Optional[Set[str]] = None,
                    objective: Optional[str] = None,
                    explanations: Optional[Dict[str, str]] = None) -> Question:
        """
        Add a new question to the bank.
        
        Args:
            question_text: The question text
            correct_answer: The correct answer text
            incorrect_answers: List of incorrect answer texts
            tags: Set of tags for categorizing the question
            objective: What the question is testing for
            explanations: Optional explanations for answers (answer_text -> explanation)
            
        Returns:
            The created Question object
        """
        if explanations is None:
            explanations = {}
        
        # Create answer objects
        answers = []
        
        # Add correct answer
        correct_ans = Answer(
            text=correct_answer,
            is_correct=True,
            explanation=explanations.get(correct_answer)
        )
        answers.append(correct_ans)
        
        # Add incorrect answers
        for incorrect_text in incorrect_answers:
            incorrect_ans = Answer(
                text=incorrect_text,
                is_correct=False,
                explanation=explanations.get(incorrect_text)
            )
            answers.append(incorrect_ans)
        
        # Create question
        question = Question(
            question_text=question_text,
            answers=answers,
            objective=objective,
            tags=tags or set()
        )
        
        self.question_bank.add_question(question)
        return question
    
    def remove_question(self, question_id: str) -> bool:
        """Remove a question from the bank."""
        return self.question_bank.remove_question(question_id)
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID."""
        return self.question_bank.get_question(question_id)
    
    def search_questions(self, query: str) -> List[Question]:
        """Search questions by text content."""
        return self.question_bank.search_questions(query)
    
    def get_questions_by_tag(self, tag: str) -> List[Question]:
        """Get all questions with a specific tag."""
        return self.question_bank.get_questions_by_tag(tag)
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags across all questions."""
        return self.question_bank.get_all_tags()
    
    # Study Session Management
    def start_study_session(self, max_questions: Optional[int] = None,
                          tags_filter: Optional[Set[str]] = None,
                          difficulty_range: Optional[tuple] = None) -> List[Question]:
        """
        Start a new study session with questions due for review.
        
        Args:
            max_questions: Maximum number of questions to include
            tags_filter: Only include questions with these tags
            difficulty_range: Tuple of (min_elo, max_elo) to filter by difficulty
            
        Returns:
            List of questions for the study session
        """
        if self.current_session is not None:
            raise RuntimeError("A study session is already in progress. End it first.")
        
        # Get all questions due for review
        due_questions = self.question_bank.get_questions_due_for_review()
        
        # Apply filters
        if tags_filter:
            due_questions = [
                q for q in due_questions 
                if any(tag in q.tags for tag in tags_filter)
            ]
        
        if difficulty_range:
            min_elo, max_elo = difficulty_range
            due_questions = [
                q for q in due_questions 
                if min_elo <= q.elo_rating <= max_elo
            ]
        
        # Get user's skill level for better question selection
        recommended_questions = self.user_tracker.get_recommended_questions(
            self.current_user_id, due_questions
        )
        
        # Limit number of questions if specified
        if max_questions and len(recommended_questions) > max_questions:
            recommended_questions = recommended_questions[:max_questions]
        
        # Shuffle to avoid predictable order
        random.shuffle(recommended_questions)
        
        # Create study session
        self.current_session = StudySession(
            questions_studied=[q.id for q in recommended_questions],
            results={}
        )
        
        return recommended_questions
    
    def answer_question(self, question_id: str, selected_answer_id: str, 
                       response_time: Optional[float] = None) -> Dict:
        """
        Submit an answer for a question in the current study session.
        
        Args:
            question_id: ID of the question being answered
            selected_answer_id: ID of the selected answer
            response_time: Time taken to answer in seconds
            
        Returns:
            Dictionary with result information
        """
        if self.current_session is None:
            raise RuntimeError("No study session in progress.")
        
        question = self.get_question(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found.")
        
        # Find the selected answer
        selected_answer = None
        for answer in question.answers:
            if answer.id == selected_answer_id:
                selected_answer = answer
                break
        
        if not selected_answer:
            raise ValueError(f"Answer {selected_answer_id} not found.")
        
        # Determine result
        result = AnswerResult.CORRECT if selected_answer.is_correct else AnswerResult.INCORRECT
        
        # Update question statistics
        question.times_answered += 1
        if result == AnswerResult.CORRECT:
            question.times_correct += 1
        
        # Update ELO ratings
        user_rating, question_rating = self.user_tracker.update_user_rating(
            self.current_user_id, question, result
        )
        
        # Schedule next review using spaced repetition
        next_review = self.scheduler.schedule_next_review(
            question, result, response_time
        )
        
        # Record result in current session
        self.current_session.results[question_id] = result
        
        return {
            "correct": result == AnswerResult.CORRECT,
            "correct_answer": question.correct_answer,
            "selected_answer": selected_answer,
            "explanation": selected_answer.explanation,
            "user_rating": user_rating,
            "question_rating": question_rating,
            "next_review": next_review,
            "accuracy": question.accuracy
        }
    
    def skip_question(self, question_id: str) -> None:
        """Skip a question in the current study session."""
        if self.current_session is None:
            raise RuntimeError("No study session in progress.")
        
        question = self.get_question(question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found.")
        
        # Schedule next review for skipped question
        self.scheduler.schedule_next_review(question, AnswerResult.SKIPPED)
        
        # Record skip in current session
        self.current_session.results[question_id] = AnswerResult.SKIPPED
    
    def end_study_session(self) -> StudySession:
        """End the current study session and return session statistics."""
        if self.current_session is None:
            raise RuntimeError("No study session in progress.")
        
        self.current_session.end_time = datetime.now()
        completed_session = self.current_session
        
        # Add to question bank history
        self.question_bank.study_sessions.append(completed_session)
        
        # Clear current session
        self.current_session = None
        
        return completed_session
    
    # Statistics and Analysis
    def get_user_statistics(self) -> Dict:
        """Get comprehensive statistics for the current user."""
        user_rating = self.user_tracker.get_user_rating(self.current_user_id)
        user_level = self.user_tracker.get_user_level(self.current_user_id)
        
        # Calculate session statistics
        total_sessions = len(self.question_bank.study_sessions)
        if total_sessions > 0:
            recent_sessions = self.question_bank.study_sessions[-10:]  # Last 10 sessions
            avg_accuracy = sum(s.accuracy for s in recent_sessions) / len(recent_sessions)
            total_questions_answered = sum(s.questions_count for s in recent_sessions)
        else:
            avg_accuracy = 0.0
            total_questions_answered = 0
        
        # Questions due for review
        due_questions = self.question_bank.get_questions_due_for_review()
        
        return {
            "user_rating": user_rating,
            "user_level": user_level,
            "total_sessions": total_sessions,
            "recent_accuracy": avg_accuracy,
            "total_questions_answered": total_questions_answered,
            "questions_due": len(due_questions),
            "total_questions": len(self.question_bank.questions)
        }
    
    def get_review_forecast(self, days: int = 7) -> Dict:
        """Get forecast of questions due for review in the coming days."""
        all_questions = list(self.question_bank.questions.values())
        return self.scheduler.get_review_forecast(all_questions, days)
    
    def get_difficult_questions(self, limit: int = 10) -> List[Question]:
        """Get the most difficult questions based on ELO rating and accuracy."""
        questions = list(self.question_bank.questions.values())
        
        # Filter questions that have been answered at least once
        answered_questions = [q for q in questions if q.times_answered > 0]
        
        # Sort by difficulty (low accuracy and high ELO rating = difficult)
        answered_questions.sort(key=lambda q: (q.accuracy, -q.elo_rating))
        
        return answered_questions[:limit]
    
    def suggest_study_session_size(self, target_minutes: int = 30) -> int:
        """Suggest optimal number of questions for a study session."""
        due_questions = self.question_bank.get_questions_due_for_review()
        return self.scheduler.suggest_study_session_size(due_questions, target_minutes)
    
    # Import/Export
    def export_bank(self, filepath: str) -> None:
        """Export the question bank to a JSON file."""
        self.question_bank.export_to_json(filepath)
    
    def import_bank(self, filepath: str) -> None:
        """Import a question bank from a JSON file."""
        self.question_bank = QuestionBank.import_from_json(filepath)
    
    # Convenience Methods
    def create_multiple_choice_question(self, question_text: str, 
                                      correct_answer: str,
                                      wrong_answers: List[str],
                                      tags: Optional[List[str]] = None,
                                      objective: Optional[str] = None) -> Question:
        """
        Convenience method to create a multiple choice question.
        
        Args:
            question_text: The question text
            correct_answer: The correct answer
            wrong_answers: List of incorrect answers
            tags: List of tags to assign to the question
            objective: What the question is testing for
            
        Returns:
            The created Question object
        """
        tag_set = set(tags) if tags else set()
        return self.add_question(
            question_text, correct_answer, wrong_answers, tag_set, objective
        )
    
    def bulk_add_questions(self, questions_data: List[Dict]) -> List[Question]:
        """
        Add multiple questions at once.
        
        Args:
            questions_data: List of dictionaries with question data.
                          Each dict should have: question, correct_answer,
                          wrong_answers, tags (optional), objective (optional)
                          
        Returns:
            List of created Question objects
        """
        created_questions = []
        
        for q_data in questions_data:
            question = self.create_multiple_choice_question(
                question_text=q_data["question"],
                correct_answer=q_data["correct_answer"],
                wrong_answers=q_data["wrong_answers"],
                tags=q_data.get("tags", []),
                objective=q_data.get("objective")
            )
            created_questions.append(question)
        
        return created_questions
