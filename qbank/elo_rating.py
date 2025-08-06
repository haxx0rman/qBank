"""
ELO rating system for measuring question difficulty and user performance.
"""

import math
from typing import Tuple
from .models import Question, AnswerResult


class ELORatingSystem:
    """
    ELO rating system for questions and users.
    Questions start with a rating of 1200, and the rating changes based on how often users answer correctly.
    """
    
    def __init__(self, k_factor: float = 32, initial_rating: float = 1200):
        """
        Initialize the ELO rating system.
        
        Args:
            k_factor: The K-factor determines how much ratings change after each game
            initial_rating: Starting rating for new questions
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for player A against player B.
        
        Args:
            rating_a: Rating of player A
            rating_b: Rating of player B
            
        Returns:
            Expected score (0.0 to 1.0) for player A
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    
    def update_ratings(self, question_rating: float, user_rating: float, 
                      result: AnswerResult) -> Tuple[float, float]:
        """
        Update both question and user ratings based on the answer result.
        
        Args:
            question_rating: Current rating of the question
            user_rating: Current rating of the user  
            result: Whether the user answered correctly, incorrectly, or skipped
            
        Returns:
            Tuple of (new_question_rating, new_user_rating)
        """
        if result == AnswerResult.SKIPPED:
            # No rating change for skipped questions
            return question_rating, user_rating
        
        # Calculate expected scores
        user_expected = self.expected_score(user_rating, question_rating)
        question_expected = self.expected_score(question_rating, user_rating)
        
        # Determine actual scores based on result
        if result == AnswerResult.CORRECT:
            user_actual = 1.0  # User "beat" the question
            question_actual = 0.0  # Question "lost" to the user
        else:  # INCORRECT
            user_actual = 0.0  # User lost to the question
            question_actual = 1.0  # Question beat the user
        
        # Update ratings using ELO formula
        new_user_rating = user_rating + self.k_factor * (user_actual - user_expected)
        new_question_rating = question_rating + self.k_factor * (question_actual - question_expected)
        
        return new_question_rating, new_user_rating
    
    def update_question_rating(self, question: Question, user_rating: float, 
                             result: AnswerResult) -> float:
        """
        Update a question's ELO rating based on user performance.
        
        Args:
            question: The question that was answered
            user_rating: The user's current ELO rating
            result: The result of answering the question
            
        Returns:
            The question's new ELO rating
        """
        new_question_rating, _ = self.update_ratings(
            question.elo_rating, user_rating, result
        )
        
        # Update the question's rating
        question.elo_rating = new_question_rating
        return new_question_rating
    
    def get_difficulty_category(self, rating: float) -> str:
        """
        Get a human-readable difficulty category based on ELO rating.
        
        Args:
            rating: The ELO rating
            
        Returns:
            String describing the difficulty level
        """
        if rating < 1000:
            return "Very Easy"
        elif rating < 1200:
            return "Easy" 
        elif rating < 1400:
            return "Medium"
        elif rating < 1600:
            return "Hard"
        elif rating < 1800:
            return "Very Hard"
        else:
            return "Expert"
    
    def get_user_level(self, rating: float) -> str:
        """
        Get a human-readable skill level based on user's ELO rating.
        
        Args:
            rating: The user's ELO rating
            
        Returns:
            String describing the user's skill level
        """
        if rating < 1000:
            return "Beginner"
        elif rating < 1200:
            return "Novice"
        elif rating < 1400:
            return "Intermediate"
        elif rating < 1600:
            return "Advanced"
        elif rating < 1800:
            return "Expert"
        else:
            return "Master"
    
    def predict_success_probability(self, user_rating: float, question_rating: float) -> float:
        """
        Predict the probability that a user will answer a question correctly.
        
        Args:
            user_rating: The user's ELO rating
            question_rating: The question's ELO rating
            
        Returns:
            Probability of success (0.0 to 1.0)
        """
        return self.expected_score(user_rating, question_rating)


class UserRatingTracker:
    """
    Track and manage user ELO ratings across study sessions.
    """
    
    def __init__(self, initial_rating: float = 1200):
        """
        Initialize user rating tracker.
        
        Args:
            initial_rating: Starting rating for new users
        """
        self.ratings = {}  # user_id -> rating
        self.initial_rating = initial_rating
        self.elo_system = ELORatingSystem()
    
    def get_user_rating(self, user_id: str) -> float:
        """Get current rating for a user, creating if doesn't exist."""
        if user_id not in self.ratings:
            self.ratings[user_id] = self.initial_rating
        return self.ratings[user_id]
    
    def update_user_rating(self, user_id: str, question: Question, result: AnswerResult) -> Tuple[float, float]:
        """
        Update both user and question ratings based on answer result.
        
        Args:
            user_id: Identifier for the user
            question: The question that was answered
            result: The result of answering
            
        Returns:
            Tuple of (new_user_rating, new_question_rating)
        """
        current_user_rating = self.get_user_rating(user_id)
        
        new_question_rating, new_user_rating = self.elo_system.update_ratings(
            question.elo_rating, current_user_rating, result
        )
        
        # Update stored ratings
        self.ratings[user_id] = new_user_rating
        question.elo_rating = new_question_rating
        
        return new_user_rating, new_question_rating
    
    def get_user_level(self, user_id: str) -> str:
        """Get human-readable skill level for a user."""
        rating = self.get_user_rating(user_id)
        return self.elo_system.get_user_level(rating)
    
    def get_recommended_questions(self, user_id: str, questions: list, 
                                target_success_rate: float = 0.7) -> list:
        """
        Get questions recommended for a user based on their skill level.
        
        Args:
            user_id: The user identifier
            questions: List of available questions
            target_success_rate: Desired probability of success (0.5-0.9)
            
        Returns:
            List of questions sorted by appropriateness for the user
        """
        user_rating = self.get_user_rating(user_id)
        
        # Calculate success probability for each question
        question_scores = []
        for question in questions:
            success_prob = self.elo_system.predict_success_probability(
                user_rating, question.elo_rating
            )
            
            # Score based on how close to target success rate
            score = 1 - abs(success_prob - target_success_rate)
            question_scores.append((question, score, success_prob))
        
        # Sort by score (best matches first)
        question_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [q[0] for q in question_scores]
