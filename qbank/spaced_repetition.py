"""
Spaced repetition scheduler based on the SM-2 algorithm (similar to Anki).
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from .models import Question, AnswerResult


class SpacedRepetitionScheduler:
    """
    Spaced repetition scheduler implementing a modified SM-2 algorithm.
    This determines when questions should be reviewed again based on how well
    the user performed on previous attempts.
    """
    
    def __init__(self, 
                 min_ease_factor: float = 1.3,
                 max_ease_factor: float = 3.0,
                 initial_ease_factor: float = 2.5,
                 ease_bonus: float = 0.15,
                 ease_penalty: float = 0.2,
                 hard_penalty: float = 0.15,
                 min_interval: float = 1.0,
                 max_interval: float = 365.0):
        """
        Initialize the spaced repetition scheduler.
        
        Args:
            min_ease_factor: Minimum allowed ease factor
            max_ease_factor: Maximum allowed ease factor  
            initial_ease_factor: Starting ease factor for new questions
            ease_bonus: Ease factor increase for correct answers
            ease_penalty: Ease factor decrease for incorrect answers
            hard_penalty: Additional penalty for very difficult questions
            min_interval: Minimum interval between reviews (days)
            max_interval: Maximum interval between reviews (days)
        """
        self.min_ease_factor = min_ease_factor
        self.max_ease_factor = max_ease_factor
        self.initial_ease_factor = initial_ease_factor
        self.ease_bonus = ease_bonus
        self.ease_penalty = ease_penalty
        self.hard_penalty = hard_penalty
        self.min_interval = min_interval
        self.max_interval = max_interval
    
    def calculate_next_interval(self, question: Question, performance: AnswerResult,
                               response_time: Optional[float] = None) -> Tuple[float, float]:
        """
        Calculate the next review interval and updated ease factor for a question.
        
        Args:
            question: The question being reviewed
            performance: How the user performed (CORRECT, INCORRECT, SKIPPED)
            response_time: Time taken to answer in seconds (optional)
            
        Returns:
            Tuple of (new_interval_days, new_ease_factor)
        """
        if performance == AnswerResult.SKIPPED:
            # For skipped questions, use a short interval
            return max(1.0, question.interval_days * 0.5), question.ease_factor
        
        current_ease = question.ease_factor
        current_interval = question.interval_days
        repetition_count = question.repetition_count
        
        if performance == AnswerResult.CORRECT:
            # Correct answer - increase interval
            if repetition_count == 0:
                # First time correct
                new_interval = 1.0
            elif repetition_count == 1:
                # Second time correct
                new_interval = 6.0
            else:
                # Subsequent correct answers
                new_interval = current_interval * current_ease
            
            # Increase ease factor for correct answers
            new_ease = min(self.max_ease_factor, current_ease + self.ease_bonus)
            
            # Bonus for quick responses (if response_time provided)
            if response_time and response_time < 5.0:  # Quick response (< 5 seconds)
                new_ease = min(self.max_ease_factor, new_ease + 0.05)
                new_interval *= 1.1  # Small interval bonus
                
        else:  # AnswerResult.INCORRECT
            # Incorrect answer - reset to short interval and reduce ease
            new_interval = 1.0
            new_ease = max(self.min_ease_factor, current_ease - self.ease_penalty)
            
            # Additional penalty for questions that were previously known
            if repetition_count > 2:
                new_ease = max(self.min_ease_factor, new_ease - self.hard_penalty)
        
        # Apply bounds
        new_interval = max(self.min_interval, min(self.max_interval, new_interval))
        new_ease = max(self.min_ease_factor, min(self.max_ease_factor, new_ease))
        
        return new_interval, new_ease
    
    def schedule_next_review(self, question: Question, performance: AnswerResult,
                           response_time: Optional[float] = None, 
                           current_time: Optional[datetime] = None) -> datetime:
        """
        Schedule the next review time for a question.
        
        Args:
            question: The question being reviewed
            performance: How the user performed
            response_time: Time taken to answer in seconds (optional)
            current_time: Current time (defaults to now)
            
        Returns:
            The datetime when this question should be reviewed next
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Calculate new interval and ease factor
        new_interval, new_ease = self.calculate_next_interval(
            question, performance, response_time
        )
        
        # Update question properties
        question.interval_days = new_interval
        question.ease_factor = new_ease
        question.last_studied = current_time
        
        if performance == AnswerResult.CORRECT:
            question.repetition_count += 1
        else:
            # Reset repetition count for incorrect answers
            question.repetition_count = 0
        
        # Calculate next review time
        next_review = current_time + timedelta(days=new_interval)
        question.next_review = next_review
        
        return next_review
    
    def get_questions_due_for_review(self, questions: List[Question], 
                                   current_time: Optional[datetime] = None) -> List[Question]:
        """
        Get all questions that are due for review.
        
        Args:
            questions: List of questions to check
            current_time: Current time (defaults to now)
            
        Returns:
            List of questions due for review, sorted by priority
        """
        if current_time is None:
            current_time = datetime.now()
        
        due_questions = []
        for question in questions:
            if question.next_review is None or question.next_review <= current_time:
                due_questions.append(question)
        
        # Sort by priority (overdue questions first, then by ease factor)
        def priority_key(q):
            if q.next_review is None:
                # New questions get high priority
                return (0, -q.ease_factor)
            
            overdue_hours = (current_time - q.next_review).total_seconds() / 3600
            return (-overdue_hours, -q.ease_factor)
        
        due_questions.sort(key=priority_key)
        return due_questions
    
    def get_review_forecast(self, questions: List[Question], days: int = 30) -> dict:
        """
        Get a forecast of how many questions will be due for review in the coming days.
        
        Args:
            questions: List of questions to analyze
            days: Number of days to forecast
            
        Returns:
            Dictionary with dates as keys and question counts as values
        """
        current_time = datetime.now()
        forecast = {}
        
        for i in range(days):
            date = current_time + timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            
            count = 0
            for question in questions:
                if (question.next_review and 
                    question.next_review.date() == date.date()):
                    count += 1
            
            forecast[date_key] = count
        
        return forecast
    
    def calculate_retention_rate(self, question: Question) -> float:
        """
        Calculate the estimated retention rate for a question based on its scheduling history.
        
        Args:
            question: The question to analyze
            
        Returns:
            Estimated retention rate (0.0 to 1.0)
        """
        if question.times_answered == 0:
            return 0.5  # Unknown retention
        
        # Base retention rate on accuracy and ease factor
        accuracy_rate = question.times_correct / question.times_answered
        
        # Ease factor indicates how well the question is retained
        ease_contribution = (question.ease_factor - self.min_ease_factor) / (
            self.max_ease_factor - self.min_ease_factor
        )
        
        # Combine accuracy and ease factor with weights
        retention_rate = (accuracy_rate * 0.7) + (ease_contribution * 0.3)
        
        return max(0.0, min(1.0, retention_rate))
    
    def suggest_study_session_size(self, due_questions: List[Question], 
                                 target_minutes: int = 30,
                                 avg_time_per_question: float = 45.0) -> int:
        """
        Suggest how many questions to include in a study session.
        
        Args:
            due_questions: Questions available for study
            target_minutes: Target session length in minutes
            avg_time_per_question: Average time per question in seconds
            
        Returns:
            Recommended number of questions for the session
        """
        target_seconds = target_minutes * 60
        max_questions = int(target_seconds / avg_time_per_question)
        
        # Don't exceed available questions
        return min(max_questions, len(due_questions))
    
    def optimize_review_schedule(self, questions: List[Question]) -> None:
        """
        Optimize the review schedule for a batch of questions to distribute workload.
        
        Args:
            questions: Questions to optimize scheduling for
        """
        # Sort questions by next review date
        scheduled_questions = [q for q in questions if q.next_review is not None]
        scheduled_questions.sort(key=lambda q: q.next_review or datetime.now())
        
        daily_limits = {}  # date -> count of questions scheduled
        max_daily_reviews = 50  # Maximum questions per day
        
        for question in scheduled_questions:
            if question.next_review is None:
                continue
                
            original_date = question.next_review.date()
            candidate_date = original_date
            
            # Find the best date that doesn't exceed daily limits
            days_offset = 0
            while days_offset < 7:  # Don't defer more than a week
                candidate_date = original_date + timedelta(days=days_offset)
                daily_count = daily_limits.get(candidate_date, 0)
                
                if daily_count < max_daily_reviews:
                    # Schedule for this date
                    daily_limits[candidate_date] = daily_count + 1
                    if days_offset > 0:
                        # Update the question's next review time
                        time_part = question.next_review.time()
                        question.next_review = datetime.combine(candidate_date, time_part)
                    break
                
                days_offset += 1
