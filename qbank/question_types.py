"""
Extended question types for the qBank system.
Supports various question formats beyond multiple choice.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
import json
from .models import Question, Answer


class QuestionType(Enum):
    """Supported question types."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    MATCHING = "matching"
    ORDERING = "ordering"


@dataclass
class FillBlankQuestion(Question):
    """Question with fill-in-the-blank format."""
    blanks: List[str] = field(default_factory=list)  # Expected answers for each blank
    case_sensitive: bool = False
    
    def check_answer(self, user_answers: List[str]) -> bool:
        """Check if the user's answers match the expected blanks."""
        if len(user_answers) != len(self.blanks):
            return False
        
        for user_answer, expected in zip(user_answers, self.blanks):
            if self.case_sensitive:
                if user_answer.strip() != expected:
                    return False
            else:
                if user_answer.strip().lower() != expected.lower():
                    return False
        return True


@dataclass
class MatchingQuestion(Question):
    """Question where items from two lists need to be matched."""
    left_items: List[str] = field(default_factory=list)
    right_items: List[str] = field(default_factory=list)
    correct_matches: Dict[int, int] = field(default_factory=dict)  # left_index -> right_index
    
    def check_answer(self, user_matches: Dict[int, int]) -> bool:
        """Check if user's matches are correct."""
        return user_matches == self.correct_matches


@dataclass
class OrderingQuestion(Question):
    """Question where items need to be put in correct order."""
    items: List[str] = field(default_factory=list)
    correct_order: List[int] = field(default_factory=list)  # Correct indices order
    
    def check_answer(self, user_order: List[int]) -> bool:
        """Check if user's order is correct."""
        return user_order == self.correct_order


class QuestionFactory:
    """Factory for creating different types of questions."""
    
    @staticmethod
    def create_true_false_question(
        question_text: str,
        correct_answer: bool,
        tags: List[str] = None,
        objective: str = None,
        explanation: str = None
    ) -> Question:
        """Create a true/false question."""
        answers = [
            Answer(text="True", is_correct=(correct_answer is True), explanation=explanation),
            Answer(text="False", is_correct=(correct_answer is False), explanation=explanation)
        ]
        
        return Question(
            question_text=question_text,
            answers=answers,
            tags=tags or [],
            objective=objective,
            question_type=QuestionType.TRUE_FALSE.value
        )
    
    @staticmethod
    def create_fill_blank_question(
        question_text: str,
        blanks: List[str],
        tags: List[str] = None,
        objective: str = None,
        case_sensitive: bool = False
    ) -> FillBlankQuestion:
        """Create a fill-in-the-blank question."""
        return FillBlankQuestion(
            question_text=question_text,
            blanks=blanks,
            case_sensitive=case_sensitive,
            tags=tags or [],
            objective=objective,
            question_type=QuestionType.FILL_BLANK.value
        )
    
    @staticmethod
    def create_short_answer_question(
        question_text: str,
        acceptable_answers: List[str],
        tags: List[str] = None,
        objective: str = None,
        case_sensitive: bool = False
    ) -> Question:
        """Create a short answer question with multiple acceptable answers."""
        answers = [
            Answer(text=answer, is_correct=True)
            for answer in acceptable_answers
        ]
        
        question = Question(
            question_text=question_text,
            answers=answers,
            tags=tags or [],
            objective=objective,
            question_type=QuestionType.SHORT_ANSWER.value
        )
        question.case_sensitive = case_sensitive
        return question
    
    @staticmethod
    def create_matching_question(
        question_text: str,
        left_items: List[str],
        right_items: List[str],
        correct_matches: Dict[int, int],
        tags: List[str] = None,
        objective: str = None
    ) -> MatchingQuestion:
        """Create a matching question."""
        return MatchingQuestion(
            question_text=question_text,
            left_items=left_items,
            right_items=right_items,
            correct_matches=correct_matches,
            tags=tags or [],
            objective=objective,
            question_type=QuestionType.MATCHING.value
        )
    
    @staticmethod
    def create_ordering_question(
        question_text: str,
        items: List[str],
        correct_order: List[int],
        tags: List[str] = None,
        objective: str = None
    ) -> OrderingQuestion:
        """Create an ordering question."""
        return OrderingQuestion(
            question_text=question_text,
            items=items,
            correct_order=correct_order,
            tags=tags or [],
            objective=objective,
            question_type=QuestionType.ORDERING.value
        )


class AdvancedQuestionChecker:
    """Advanced answer checking with fuzzy matching and pattern recognition."""
    
    @staticmethod
    def check_short_answer(user_answer: str, acceptable_answers: List[str], 
                          case_sensitive: bool = False, fuzzy_threshold: float = 0.8) -> bool:
        """Check short answer with fuzzy matching."""
        if not case_sensitive:
            user_answer = user_answer.lower()
            acceptable_answers = [ans.lower() for ans in acceptable_answers]
        
        user_answer = user_answer.strip()
        
        # Exact match
        if user_answer in acceptable_answers:
            return True
        
        # Fuzzy matching using simple character similarity
        for acceptable in acceptable_answers:
            similarity = AdvancedQuestionChecker._calculate_similarity(user_answer, acceptable)
            if similarity >= fuzzy_threshold:
                return True
        
        return False
    
    @staticmethod
    def _calculate_similarity(str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Levenshtein distance."""
        if len(str1) == 0:
            return 0.0 if len(str2) > 0 else 1.0
        if len(str2) == 0:
            return 0.0
        
        # Simple character-based similarity
        max_len = max(len(str1), len(str2))
        distance = AdvancedQuestionChecker._levenshtein_distance(str1, str2)
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def _levenshtein_distance(str1: str, str2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(str1) > len(str2):
            str1, str2 = str2, str1
        
        distances = list(range(len(str1) + 1))
        for i2, char2 in enumerate(str2):
            new_distances = [i2 + 1]
            for i1, char1 in enumerate(str1):
                if char1 == char2:
                    new_distances.append(distances[i1])
                else:
                    new_distances.append(1 + min((distances[i1], distances[i1 + 1], new_distances[-1])))
            distances = new_distances
        return distances[-1]
    
    @staticmethod
    def check_mathematical_expression(user_answer: str, correct_answers: List[str]) -> bool:
        """Check mathematical expressions with some tolerance."""
        try:
            # Remove spaces and normalize
            user_clean = re.sub(r'\s+', '', user_answer.lower())
            
            for correct in correct_answers:
                correct_clean = re.sub(r'\s+', '', correct.lower())
                
                # Direct match
                if user_clean == correct_clean:
                    return True
                
                # Try to evaluate as mathematical expressions (basic)
                if AdvancedQuestionChecker._try_mathematical_equivalence(user_clean, correct_clean):
                    return True
            
            return False
        except:
            return False
    
    @staticmethod
    def _try_mathematical_equivalence(expr1: str, expr2: str) -> bool:
        """Try to check if two mathematical expressions are equivalent (basic)."""
        try:
            # Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/().x^')
            if not all(c in allowed_chars for c in expr1 + expr2):
                return False
            
            # Replace ^ with ** for Python evaluation
            expr1 = expr1.replace('^', '**').replace('x', '*x')
            expr2 = expr2.replace('^', '**').replace('x', '*x')
            
            # Very basic - just string comparison after normalization
            return expr1 == expr2
        except:
            return False


# Integration with existing QuestionBankManager would go here
# This would extend the manager to support these new question types
