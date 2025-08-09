"""
Advanced analytics and progress tracking for the qBank system.
Provides detailed insights into learning patterns and performance.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json
import math


@dataclass
class LearningSession:
    """Detailed session analytics."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    questions_attempted: int = 0
    questions_correct: int = 0
    total_response_time: float = 0.0
    subjects_practiced: List[str] = field(default_factory=list)
    difficulty_distribution: Dict[str, int] = field(default_factory=dict)
    learning_velocity: float = 0.0  # Questions per minute
    
    @property
    def duration_minutes(self) -> float:
        """Session duration in minutes."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return 0.0
    
    @property
    def accuracy(self) -> float:
        """Session accuracy percentage."""
        if self.questions_attempted == 0:
            return 0.0
        return (self.questions_correct / self.questions_attempted) * 100
    
    @property
    def average_response_time(self) -> float:
        """Average response time per question in seconds."""
        if self.questions_attempted == 0:
            return 0.0
        return self.total_response_time / self.questions_attempted


@dataclass
class LearningMetrics:
    """Comprehensive learning metrics for a user."""
    user_id: str
    total_study_time: float = 0.0  # in minutes
    total_questions: int = 0
    total_correct: int = 0
    streak_current: int = 0
    streak_longest: int = 0
    mastery_levels: Dict[str, float] = field(default_factory=dict)  # subject -> mastery %
    learning_curve: List[Tuple[datetime, float]] = field(default_factory=list)  # date, accuracy
    retention_rate: float = 0.0
    
    @property
    def overall_accuracy(self) -> float:
        """Overall accuracy across all sessions."""
        if self.total_questions == 0:
            return 0.0
        return (self.total_correct / self.total_questions) * 100


class AdvancedAnalytics:
    """Advanced analytics engine for learning insights."""
    
    def __init__(self):
        self.sessions: Dict[str, LearningSession] = {}
        self.user_metrics: Dict[str, LearningMetrics] = {}
    
    def record_session(self, session: LearningSession):
        """Record a learning session."""
        self.sessions[session.session_id] = session
        
        # Update user metrics
        if session.user_id not in self.user_metrics:
            self.user_metrics[session.user_id] = LearningMetrics(session.user_id)
        
        metrics = self.user_metrics[session.user_id]
        metrics.total_study_time += session.duration_minutes
        metrics.total_questions += session.questions_attempted
        metrics.total_correct += session.questions_correct
        
        # Update learning curve
        if session.end_time:
            metrics.learning_curve.append((session.end_time, session.accuracy))
        
        # Update mastery levels for subjects
        for subject in session.subjects_practiced:
            if subject not in metrics.mastery_levels:
                metrics.mastery_levels[subject] = 0.0
            
            # Simple mastery calculation based on recent performance
            current_mastery = metrics.mastery_levels[subject]
            session_performance = session.accuracy / 100.0
            # Weighted average with more weight on recent performance
            metrics.mastery_levels[subject] = (current_mastery * 0.7) + (session_performance * 0.3)
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive learning insights for a user."""
        if user_id not in self.user_metrics:
            return {"error": "No data available for user"}
        
        metrics = self.user_metrics[user_id]
        user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        
        insights = {
            "overview": {
                "total_study_time": metrics.total_study_time,
                "total_questions": metrics.total_questions,
                "overall_accuracy": metrics.overall_accuracy,
                "current_streak": metrics.streak_current,
                "longest_streak": metrics.streak_longest
            },
            "performance_trends": self._analyze_performance_trends(user_sessions),
            "subject_mastery": metrics.mastery_levels,
            "study_patterns": self._analyze_study_patterns(user_sessions),
            "recommendations": self._generate_recommendations(user_id, user_sessions)
        }
        
        return insights
    
    def _analyze_performance_trends(self, sessions: List[LearningSession]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(sessions) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort sessions by time
        sorted_sessions = sorted(sessions, key=lambda s: s.start_time)
        
        # Calculate accuracy trend
        recent_sessions = sorted_sessions[-5:]  # Last 5 sessions
        older_sessions = sorted_sessions[-10:-5] if len(sorted_sessions) >= 10 else sorted_sessions[:-5]
        
        if older_sessions:
            recent_avg = sum(s.accuracy for s in recent_sessions) / len(recent_sessions)
            older_avg = sum(s.accuracy for s in older_sessions) / len(older_sessions)
            accuracy_change = recent_avg - older_avg
        else:
            accuracy_change = 0.0
        
        # Calculate response time trend
        recent_response_time = sum(s.average_response_time for s in recent_sessions) / len(recent_sessions)
        
        return {
            "accuracy_trend": "improving" if accuracy_change > 5 else "declining" if accuracy_change < -5 else "stable",
            "accuracy_change": accuracy_change,
            "recent_accuracy": sum(s.accuracy for s in recent_sessions) / len(recent_sessions),
            "average_response_time": recent_response_time,
            "total_sessions": len(sessions)
        }
    
    def _analyze_study_patterns(self, sessions: List[LearningSession]) -> Dict[str, Any]:
        """Analyze study patterns and habits."""
        if not sessions:
            return {}
        
        # Study frequency
        session_dates = [s.start_time.date() for s in sessions]
        unique_dates = set(session_dates)
        days_studied = len(unique_dates)
        
        # Time of day preferences
        hour_counts = defaultdict(int)
        for session in sessions:
            hour_counts[session.start_time.hour] += 1
        
        preferred_hour = max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else 12
        
        # Session length preferences
        avg_session_length = sum(s.duration_minutes for s in sessions) / len(sessions)
        
        # Subject preferences
        subject_counts = defaultdict(int)
        for session in sessions:
            for subject in session.subjects_practiced:
                subject_counts[subject] += 1
        
        return {
            "days_studied": days_studied,
            "average_session_length": avg_session_length,
            "preferred_study_hour": preferred_hour,
            "most_practiced_subjects": dict(sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def _generate_recommendations(self, user_id: str, sessions: List[LearningSession]) -> List[str]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        if not sessions:
            return ["Start with a practice session to establish your baseline."]
        
        metrics = self.user_metrics[user_id]
        recent_sessions = sorted(sessions, key=lambda s: s.start_time)[-5:]
        
        # Accuracy-based recommendations
        recent_accuracy = sum(s.accuracy for s in recent_sessions) / len(recent_sessions)
        if recent_accuracy < 60:
            recommendations.append("Focus on reviewing incorrect answers and their explanations.")
            recommendations.append("Consider shorter sessions with immediate feedback.")
        elif recent_accuracy > 85:
            recommendations.append("Great job! Try challenging yourself with harder topics.")
            recommendations.append("Consider teaching others to reinforce your knowledge.")
        
        # Study frequency recommendations
        if len(sessions) < 7:  # Less than a week of data
            recommendations.append("Establish a consistent daily study routine.")
        
        # Subject balance recommendations
        subject_counts = defaultdict(int)
        for session in recent_sessions:
            for subject in session.subjects_practiced:
                subject_counts[subject] += 1
        
        if len(subject_counts) == 1:
            recommendations.append("Try studying different subjects to broaden your knowledge.")
        
        # Mastery-based recommendations
        low_mastery_subjects = [
            subject for subject, mastery in metrics.mastery_levels.items() 
            if mastery < 0.7
        ]
        if low_mastery_subjects:
            recommendations.append(f"Focus on improving: {', '.join(low_mastery_subjects[:3])}.")
        
        # Session length recommendations
        avg_length = sum(s.duration_minutes for s in recent_sessions) / len(recent_sessions)
        if avg_length < 5:
            recommendations.append("Consider longer study sessions for better retention.")
        elif avg_length > 30:
            recommendations.append("Try shorter, more frequent sessions to avoid fatigue.")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def get_comparative_analytics(self, user_id: str) -> Dict[str, Any]:
        """Compare user performance against system averages."""
        if user_id not in self.user_metrics:
            return {"error": "No data available for user"}
        
        user_metrics = self.user_metrics[user_id]
        
        # Calculate system averages
        all_accuracies = [m.overall_accuracy for m in self.user_metrics.values() if m.total_questions > 0]
        all_study_times = [m.total_study_time for m in self.user_metrics.values()]
        
        if not all_accuracies:
            return {"error": "Insufficient system data for comparison"}
        
        avg_accuracy = sum(all_accuracies) / len(all_accuracies)
        avg_study_time = sum(all_study_times) / len(all_study_times)
        
        user_percentile_accuracy = sum(1 for acc in all_accuracies if acc <= user_metrics.overall_accuracy) / len(all_accuracies) * 100
        user_percentile_study_time = sum(1 for time in all_study_times if time <= user_metrics.total_study_time) / len(all_study_times) * 100
        
        return {
            "user_accuracy": user_metrics.overall_accuracy,
            "system_average_accuracy": avg_accuracy,
            "accuracy_percentile": user_percentile_accuracy,
            "user_study_time": user_metrics.total_study_time,
            "system_average_study_time": avg_study_time,
            "study_time_percentile": user_percentile_study_time,
            "rank": f"Top {100 - user_percentile_accuracy:.0f}%" if user_percentile_accuracy > 50 else f"Bottom {user_percentile_accuracy:.0f}%"
        }
    
    def export_analytics_report(self, user_id: str, file_path: str):
        """Export a comprehensive analytics report to JSON."""
        insights = self.get_learning_insights(user_id)
        comparative = self.get_comparative_analytics(user_id)
        
        report = {
            "user_id": user_id,
            "generated_at": datetime.now().isoformat(),
            "insights": insights,
            "comparative_analytics": comparative
        }
        
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)


class ProgressPredictor:
    """Predict future learning progress and outcomes."""
    
    @staticmethod
    def predict_mastery_timeline(current_accuracy: float, target_accuracy: float = 90.0, 
                                sessions_per_week: int = 5) -> Dict[str, Any]:
        """Predict when a user will reach target mastery."""
        if current_accuracy >= target_accuracy:
            return {"status": "already_achieved", "current": current_accuracy}
        
        # Simple linear model - in reality, learning curves are not linear
        improvement_rate = 2.0  # Assume 2% improvement per week with regular practice
        weeks_needed = (target_accuracy - current_accuracy) / improvement_rate
        
        if sessions_per_week < 3:
            weeks_needed *= 1.5  # Slower progress with infrequent practice
        elif sessions_per_week > 7:
            weeks_needed *= 0.8  # Faster progress with intensive practice
        
        return {
            "weeks_to_target": math.ceil(weeks_needed),
            "target_accuracy": target_accuracy,
            "current_accuracy": current_accuracy,
            "recommended_sessions_per_week": max(3, sessions_per_week)
        }
    
    @staticmethod
    def calculate_retention_probability(days_since_last_study: int, 
                                      original_accuracy: float) -> float:
        """Calculate probability of retaining knowledge."""
        # Based on Ebbinghaus forgetting curve
        if days_since_last_study <= 0:
            return original_accuracy / 100.0
        
        # Simplified forgetting curve: R(t) = e^(-t/S)
        # Where S is the stability (higher for better initial performance)
        stability = original_accuracy / 10.0  # Higher accuracy = better retention
        retention = math.exp(-days_since_last_study / stability)
        
        return max(0.1, retention)  # Minimum 10% retention
