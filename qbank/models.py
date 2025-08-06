"""
Core data models for the question bank system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json


class Difficulty(Enum):
    """Question difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"
    EXPERT = "expert"


class AnswerResult(Enum):
    """Result of answering a question"""
    CORRECT = "correct"
    INCORRECT = "incorrect" 
    SKIPPED = "skipped"


@dataclass
class Answer:
    """Represents a single answer option for a question"""
    text: str
    is_correct: bool
    explanation: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Question:
    """Represents a single question with multiple choice answers"""
    question_text: str
    answers: List[Answer]
    objective: Optional[str] = None  # What the question is testing for
    tags: Set[str] = field(default_factory=set)
    elo_rating: float = 1200.0  # Starting ELO rating
    times_answered: int = 0
    times_correct: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_studied: Optional[datetime] = None
    next_review: Optional[datetime] = None
    interval_days: float = 1.0  # Spaced repetition interval
    ease_factor: float = 2.5  # Spaced repetition ease
    repetition_count: int = 0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def correct_answer(self) -> Optional[Answer]:
        """Get the correct answer for this question"""
        for answer in self.answers:
            if answer.is_correct:
                return answer
        return None
    
    @property
    def incorrect_answers(self) -> List[Answer]:
        """Get all incorrect answers for this question"""
        return [answer for answer in self.answers if not answer.is_correct]
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage for this question"""
        if self.times_answered == 0:
            return 0.0
        return (self.times_correct / self.times_answered) * 100
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this question"""
        self.tags.add(tag.lower().strip())
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this question"""
        self.tags.discard(tag.lower().strip())
    
    def has_tag(self, tag: str) -> bool:
        """Check if question has a specific tag"""
        return tag.lower().strip() in self.tags


@dataclass 
class StudySession:
    """Represents a study session with questions and results"""
    questions_studied: List[str]  # Question IDs
    results: Dict[str, AnswerResult]  # Question ID -> Result
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get the duration of the study session"""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    @property
    def questions_count(self) -> int:
        """Get total number of questions in session"""
        return len(self.questions_studied)
    
    @property
    def correct_count(self) -> int:
        """Get number of correct answers"""
        return sum(1 for result in self.results.values() if result == AnswerResult.CORRECT)
    
    @property
    def incorrect_count(self) -> int:
        """Get number of incorrect answers"""
        return sum(1 for result in self.results.values() if result == AnswerResult.INCORRECT)
    
    @property
    def skipped_count(self) -> int:
        """Get number of skipped questions"""
        return sum(1 for result in self.results.values() if result == AnswerResult.SKIPPED)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage for this session"""
        answered = self.correct_count + self.incorrect_count
        if answered == 0:
            return 0.0
        return (self.correct_count / answered) * 100


@dataclass
class QuestionBank:
    """Main question bank containing all questions and study sessions"""
    questions: Dict[str, Question] = field(default_factory=dict)
    study_sessions: List[StudySession] = field(default_factory=list)
    name: str = "Default Question Bank"
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_question(self, question: Question) -> None:
        """Add a question to the bank"""
        self.questions[question.id] = question
    
    def remove_question(self, question_id: str) -> bool:
        """Remove a question from the bank"""
        if question_id in self.questions:
            del self.questions[question_id]
            return True
        return False
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a question by ID"""
        return self.questions.get(question_id)
    
    def get_questions_by_tag(self, tag: str) -> List[Question]:
        """Get all questions with a specific tag"""
        return [q for q in self.questions.values() if q.has_tag(tag)]
    
    def get_all_tags(self) -> Set[str]:
        """Get all unique tags across all questions"""
        all_tags = set()
        for question in self.questions.values():
            all_tags.update(question.tags)
        return all_tags
    
    def search_questions(self, query: str) -> List[Question]:
        """Search questions by text content"""
        query_lower = query.lower()
        results = []
        
        for question in self.questions.values():
            # Search in question text
            if query_lower in question.question_text.lower():
                results.append(question)
                continue
            
            # Search in answer text
            for answer in question.answers:
                if query_lower in answer.text.lower():
                    results.append(question)
                    break
        
        return results
    
    def get_questions_due_for_review(self) -> List[Question]:
        """Get questions that are due for spaced repetition review"""
        now = datetime.now()
        return [
            q for q in self.questions.values() 
            if q.next_review is None or q.next_review <= now
        ]
    
    def get_statistics(self) -> Dict:
        """Get overall statistics for the question bank"""
        total_questions = len(self.questions)
        if total_questions == 0:
            return {
                "total_questions": 0,
                "total_sessions": len(self.study_sessions),
                "average_accuracy": 0.0,
                "most_difficult_questions": [],
                "easiest_questions": [],
                "most_studied_tags": []
            }
        
        # Calculate average accuracy
        accuracies = [q.accuracy for q in self.questions.values() if q.times_answered > 0]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        
        # Find most difficult questions (lowest ELO or accuracy)
        sorted_by_difficulty = sorted(
            self.questions.values(), 
            key=lambda q: (q.elo_rating, q.accuracy) if q.times_answered > 0 else (q.elo_rating, 0)
        )
        
        # Count tag usage
        tag_counts = {}
        for question in self.questions.values():
            for tag in question.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        most_studied_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_questions": total_questions,
            "total_sessions": len(self.study_sessions),
            "average_accuracy": avg_accuracy,
            "most_difficult_questions": sorted_by_difficulty[:5],
            "easiest_questions": sorted_by_difficulty[-5:],
            "most_studied_tags": most_studied_tags,
            "questions_due_for_review": len(self.get_questions_due_for_review())
        }
    
    def export_to_json(self, filepath: str) -> None:
        """Export question bank to JSON file"""
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Convert to serializable format
        data = {
            "name": self.name,
            "created_at": self.created_at,
            "questions": {qid: {
                "id": q.id,
                "question_text": q.question_text,
                "objective": q.objective,
                "answers": [{
                    "id": a.id,
                    "text": a.text,
                    "is_correct": a.is_correct,
                    "explanation": a.explanation
                } for a in q.answers],
                "tags": list(q.tags),
                "elo_rating": q.elo_rating,
                "times_answered": q.times_answered,
                "times_correct": q.times_correct,
                "created_at": q.created_at,
                "last_studied": q.last_studied,
                "next_review": q.next_review,
                "interval_days": q.interval_days,
                "ease_factor": q.ease_factor,
                "repetition_count": q.repetition_count
            } for qid, q in self.questions.items()},
            "study_sessions": [{
                "session_id": s.session_id,
                "questions_studied": s.questions_studied,
                "results": {qid: result.value for qid, result in s.results.items()},
                "start_time": s.start_time,
                "end_time": s.end_time
            } for s in self.study_sessions]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, default=serialize_datetime, indent=2, ensure_ascii=False)
    
    @classmethod
    def import_from_json(cls, filepath: str) -> 'QuestionBank':
        """Import question bank from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def parse_datetime(date_str):
            if date_str:
                return datetime.fromisoformat(date_str)
            return datetime.now()  # Default fallback
        
        bank = cls(name=data["name"], created_at=parse_datetime(data.get("created_at")))
        
        # Import questions
        for qid, q_data in data["questions"].items():
            answers = [
                Answer(
                    id=a_data["id"],
                    text=a_data["text"],
                    is_correct=a_data["is_correct"],
                    explanation=a_data.get("explanation")
                ) for a_data in q_data["answers"]
            ]
            
            question = Question(
                id=q_data["id"],
                question_text=q_data["question_text"],
                answers=answers,
                objective=q_data.get("objective"),
                tags=set(q_data["tags"]),
                elo_rating=q_data["elo_rating"],
                times_answered=q_data["times_answered"],
                times_correct=q_data["times_correct"],
                created_at=parse_datetime(q_data.get("created_at")),
                last_studied=parse_datetime(q_data.get("last_studied")),
                next_review=parse_datetime(q_data.get("next_review")),
                interval_days=q_data["interval_days"],
                ease_factor=q_data["ease_factor"],
                repetition_count=q_data["repetition_count"]
            )
            bank.add_question(question)
        
        # Import study sessions
        for s_data in data["study_sessions"]:
            session = StudySession(
                session_id=s_data["session_id"],
                questions_studied=s_data["questions_studied"],
                results={qid: AnswerResult(result) for qid, result in s_data["results"].items()},
                start_time=parse_datetime(s_data.get("start_time")),
                end_time=parse_datetime(s_data.get("end_time")) if s_data.get("end_time") else None
            )
            bank.study_sessions.append(session)
        
        return bank
