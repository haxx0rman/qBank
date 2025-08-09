"""
Learning paths and curriculum management for structured learning.
Provides guided learning experiences with prerequisites and milestones.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json


class PathStatus(Enum):
    """Status of a learning path."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class MilestoneType(Enum):
    """Types of learning milestones."""
    ACCURACY_THRESHOLD = "accuracy_threshold"
    QUESTION_COUNT = "question_count"
    STREAK = "streak"
    TIME_BASED = "time_based"
    MASTERY_LEVEL = "mastery_level"


@dataclass
class Milestone:
    """A learning milestone within a path."""
    id: str
    name: str
    description: str
    milestone_type: MilestoneType
    target_value: float
    current_value: float = 0.0
    completed: bool = False
    completed_at: Optional[datetime] = None
    
    @property
    def progress_percentage(self) -> float:
        """Progress towards milestone completion."""
        if self.target_value == 0:
            return 100.0 if self.completed else 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)


@dataclass
class LearningModule:
    """A module within a learning path."""
    id: str
    name: str
    description: str
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # Module IDs
    estimated_duration: int = 30  # minutes
    difficulty_level: int = 1  # 1-5 scale
    questions: List[str] = field(default_factory=list)  # Question IDs
    milestones: List[Milestone] = field(default_factory=list)
    completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def is_unlocked(self, completed_modules: Set[str]) -> bool:
        """Check if module is unlocked based on prerequisites."""
        return all(prereq in completed_modules for prereq in self.prerequisites)


@dataclass
class LearningPath:
    """A structured learning path with modules and milestones."""
    id: str
    name: str
    description: str
    category: str
    difficulty_level: int = 1  # 1-5 scale
    estimated_total_duration: int = 0  # minutes
    modules: List[LearningModule] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # Path IDs
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_percentage(self) -> float:
        """Overall progress through the path."""
        if not self.modules:
            return 0.0
        completed_count = sum(1 for module in self.modules if module.completed)
        return (completed_count / len(self.modules)) * 100
    
    @property
    def status(self) -> PathStatus:
        """Current status of the learning path."""
        if not any(module.started_at for module in self.modules):
            return PathStatus.NOT_STARTED
        elif all(module.completed for module in self.modules):
            return PathStatus.COMPLETED
        else:
            return PathStatus.IN_PROGRESS


class CurriculumManager:
    """Manages learning paths and student progress."""
    
    def __init__(self):
        self.paths: Dict[str, LearningPath] = {}
        self.user_progress: Dict[str, Dict[str, Any]] = {}  # user_id -> progress data
    
    def create_learning_path(self, path_data: Dict[str, Any]) -> LearningPath:
        """Create a new learning path."""
        path = LearningPath(
            id=path_data["id"],
            name=path_data["name"],
            description=path_data["description"],
            category=path_data.get("category", "General"),
            difficulty_level=path_data.get("difficulty_level", 1),
            tags=path_data.get("tags", [])
        )
        
        # Add modules
        for module_data in path_data.get("modules", []):
            module = LearningModule(
                id=module_data["id"],
                name=module_data["name"],
                description=module_data["description"],
                tags=module_data.get("tags", []),
                prerequisites=module_data.get("prerequisites", []),
                estimated_duration=module_data.get("estimated_duration", 30),
                difficulty_level=module_data.get("difficulty_level", 1),
                questions=module_data.get("questions", [])
            )
            
            # Add milestones
            for milestone_data in module_data.get("milestones", []):
                milestone = Milestone(
                    id=milestone_data["id"],
                    name=milestone_data["name"],
                    description=milestone_data["description"],
                    milestone_type=MilestoneType(milestone_data["type"]),
                    target_value=milestone_data["target_value"]
                )
                module.milestones.append(milestone)
            
            path.modules.append(module)
        
        # Calculate estimated total duration
        path.estimated_total_duration = sum(module.estimated_duration for module in path.modules)
        
        self.paths[path.id] = path
        return path
    
    def enroll_user(self, user_id: str, path_id: str) -> bool:
        """Enroll a user in a learning path."""
        if path_id not in self.paths:
            return False
        
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        self.user_progress[user_id][path_id] = {
            "enrolled_at": datetime.now(),
            "current_module": None,
            "completed_modules": set(),
            "milestones_completed": set()
        }
        
        return True
    
    def get_next_module(self, user_id: str, path_id: str) -> Optional[LearningModule]:
        """Get the next available module for a user."""
        if user_id not in self.user_progress or path_id not in self.user_progress[user_id]:
            return None
        
        path = self.paths[path_id]
        completed_modules = self.user_progress[user_id][path_id]["completed_modules"]
        
        for module in path.modules:
            if not module.completed and module.is_unlocked(completed_modules):
                return module
        
        return None
    
    def start_module(self, user_id: str, path_id: str, module_id: str) -> bool:
        """Start a module for a user."""
        if user_id not in self.user_progress or path_id not in self.user_progress[user_id]:
            return False
        
        path = self.paths[path_id]
        module = next((m for m in path.modules if m.id == module_id), None)
        
        if not module or module.completed:
            return False
        
        completed_modules = self.user_progress[user_id][path_id]["completed_modules"]
        if not module.is_unlocked(completed_modules):
            return False
        
        module.started_at = datetime.now()
        self.user_progress[user_id][path_id]["current_module"] = module_id
        
        return True
    
    def complete_module(self, user_id: str, path_id: str, module_id: str) -> bool:
        """Mark a module as completed."""
        if user_id not in self.user_progress or path_id not in self.user_progress[user_id]:
            return False
        
        path = self.paths[path_id]
        module = next((m for m in path.modules if m.id == module_id), None)
        
        if not module:
            return False
        
        module.completed = True
        module.completed_at = datetime.now()
        
        self.user_progress[user_id][path_id]["completed_modules"].add(module_id)
        self.user_progress[user_id][path_id]["current_module"] = None
        
        return True
    
    def update_milestone_progress(self, user_id: str, path_id: str, module_id: str, 
                                milestone_id: str, value: float) -> bool:
        """Update progress on a milestone."""
        path = self.paths.get(path_id)
        if not path:
            return False
        
        module = next((m for m in path.modules if m.id == module_id), None)
        if not module:
            return False
        
        milestone = next((m for m in module.milestones if m.id == milestone_id), None)
        if not milestone:
            return False
        
        milestone.current_value = value
        
        # Check if milestone is completed
        if milestone.current_value >= milestone.target_value and not milestone.completed:
            milestone.completed = True
            milestone.completed_at = datetime.now()
            
            # Add to user's completed milestones
            if user_id in self.user_progress and path_id in self.user_progress[user_id]:
                self.user_progress[user_id][path_id]["milestones_completed"].add(milestone_id)
        
        return True
    
    def get_user_progress(self, user_id: str, path_id: str) -> Dict[str, Any]:
        """Get detailed progress for a user on a path."""
        if user_id not in self.user_progress or path_id not in self.user_progress[user_id]:
            return {"error": "User not enrolled in path"}
        
        path = self.paths[path_id]
        user_data = self.user_progress[user_id][path_id]
        
        # Calculate overall progress
        completed_modules = len(user_data["completed_modules"])
        total_modules = len(path.modules)
        
        # Get current module details
        current_module = None
        if user_data["current_module"]:
            current_module = next(
                (m for m in path.modules if m.id == user_data["current_module"]), 
                None
            )
        
        # Calculate time spent and estimated remaining
        time_spent = 0
        estimated_remaining = 0
        
        for module in path.modules:
            if module.id in user_data["completed_modules"]:
                time_spent += module.estimated_duration
            else:
                estimated_remaining += module.estimated_duration
        
        return {
            "path_id": path_id,
            "path_name": path.name,
            "enrolled_at": user_data["enrolled_at"],
            "status": path.status.value,
            "progress_percentage": path.progress_percentage,
            "completed_modules": completed_modules,
            "total_modules": total_modules,
            "current_module": current_module.name if current_module else None,
            "time_spent_minutes": time_spent,
            "estimated_remaining_minutes": estimated_remaining,
            "milestones_completed": len(user_data["milestones_completed"]),
            "next_available_modules": [
                {"id": m.id, "name": m.name, "description": m.description}
                for m in path.modules 
                if not m.completed and m.is_unlocked(user_data["completed_modules"])
            ]
        }
    
    def get_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get personalized path recommendations for a user."""
        if user_id not in self.user_progress:
            # New user - recommend beginner paths
            return [
                {
                    "path_id": path.id,
                    "name": path.name,
                    "description": path.description,
                    "reason": "Great for beginners",
                    "difficulty": path.difficulty_level,
                    "estimated_duration": path.estimated_total_duration
                }
                for path in self.paths.values()
                if path.difficulty_level <= 2
            ][:3]
        
        # Get user's completed paths and current interests
        user_data = self.user_progress[user_id]
        completed_paths = {
            path_id for path_id, progress in user_data.items()
            if self.paths[path_id].status == PathStatus.COMPLETED
        }
        
        recommendations = []
        
        # Recommend next level paths
        for path in self.paths.values():
            if path.id not in user_data:  # Not enrolled
                # Check if prerequisites are met
                if all(prereq in completed_paths for prereq in path.prerequisites):
                    reason = "Next step in your learning journey"
                    if path.prerequisites:
                        reason = f"Builds on {', '.join(path.prerequisites)}"
                    
                    recommendations.append({
                        "path_id": path.id,
                        "name": path.name,
                        "description": path.description,
                        "reason": reason,
                        "difficulty": path.difficulty_level,
                        "estimated_duration": path.estimated_total_duration
                    })
        
        return recommendations[:5]
    
    def create_adaptive_path(self, user_id: str, weak_subjects: List[str], 
                           target_accuracy: float = 80.0) -> LearningPath:
        """Create an adaptive learning path based on user's weak areas."""
        path_id = f"adaptive_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        path = LearningPath(
            id=path_id,
            name=f"Personalized Learning Plan",
            description=f"Adaptive path targeting: {', '.join(weak_subjects)}",
            category="Adaptive",
            difficulty_level=2
        )
        
        # Create modules for each weak subject
        for i, subject in enumerate(weak_subjects):
            module = LearningModule(
                id=f"module_{subject}_{i}",
                name=f"Mastering {subject.title()}",
                description=f"Focused practice on {subject} concepts",
                tags=[subject],
                estimated_duration=45,
                difficulty_level=2
            )
            
            # Add milestones
            accuracy_milestone = Milestone(
                id=f"accuracy_{subject}",
                name=f"{subject.title()} Accuracy",
                description=f"Achieve {target_accuracy}% accuracy in {subject}",
                milestone_type=MilestoneType.ACCURACY_THRESHOLD,
                target_value=target_accuracy
            )
            
            streak_milestone = Milestone(
                id=f"streak_{subject}",
                name=f"{subject.title()} Streak",
                description=f"Answer 10 {subject} questions correctly in a row",
                milestone_type=MilestoneType.STREAK,
                target_value=10
            )
            
            module.milestones.extend([accuracy_milestone, streak_milestone])
            path.modules.append(module)
        
        path.estimated_total_duration = sum(m.estimated_duration for m in path.modules)
        self.paths[path.id] = path
        
        return path
    
    def export_curriculum(self, file_path: str):
        """Export curriculum data to JSON."""
        curriculum_data = {
            "paths": {
                path_id: {
                    "id": path.id,
                    "name": path.name,
                    "description": path.description,
                    "category": path.category,
                    "difficulty_level": path.difficulty_level,
                    "estimated_total_duration": path.estimated_total_duration,
                    "modules": [
                        {
                            "id": module.id,
                            "name": module.name,
                            "description": module.description,
                            "tags": module.tags,
                            "prerequisites": module.prerequisites,
                            "estimated_duration": module.estimated_duration,
                            "difficulty_level": module.difficulty_level,
                            "milestones": [
                                {
                                    "id": milestone.id,
                                    "name": milestone.name,
                                    "description": milestone.description,
                                    "type": milestone.milestone_type.value,
                                    "target_value": milestone.target_value
                                }
                                for milestone in module.milestones
                            ]
                        }
                        for module in path.modules
                    ],
                    "prerequisites": path.prerequisites,
                    "tags": path.tags
                }
                for path_id, path in self.paths.items()
            },
            "exported_at": datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(curriculum_data, f, indent=2)


# Predefined curriculum templates
CURRICULUM_TEMPLATES = {
    "python_fundamentals": {
        "id": "python_fundamentals",
        "name": "Python Programming Fundamentals",
        "description": "Complete introduction to Python programming",
        "category": "Programming",
        "difficulty_level": 2,
        "modules": [
            {
                "id": "python_basics",
                "name": "Python Basics",
                "description": "Variables, data types, and basic operations",
                "tags": ["python", "basics", "syntax"],
                "estimated_duration": 60,
                "difficulty_level": 1,
                "milestones": [
                    {
                        "id": "syntax_accuracy",
                        "name": "Syntax Mastery",
                        "description": "Achieve 80% accuracy in Python syntax questions",
                        "type": "accuracy_threshold",
                        "target_value": 80.0
                    }
                ]
            },
            {
                "id": "control_structures",
                "name": "Control Structures",
                "description": "If statements, loops, and control flow",
                "tags": ["python", "control-flow", "loops"],
                "prerequisites": ["python_basics"],
                "estimated_duration": 45,
                "difficulty_level": 2,
                "milestones": [
                    {
                        "id": "control_mastery",
                        "name": "Control Flow Mastery",
                        "description": "Complete 20 control structure questions correctly",
                        "type": "question_count",
                        "target_value": 20
                    }
                ]
            },
            {
                "id": "functions",
                "name": "Functions and Modules",
                "description": "Defining and using functions, modules and packages",
                "tags": ["python", "functions", "modules"],
                "prerequisites": ["control_structures"],
                "estimated_duration": 50,
                "difficulty_level": 3,
                "milestones": [
                    {
                        "id": "function_streak",
                        "name": "Function Expert",
                        "description": "Answer 15 function questions correctly in a row",
                        "type": "streak",
                        "target_value": 15
                    }
                ]
            }
        ]
    },
    
    "data_structures": {
        "id": "data_structures",
        "name": "Data Structures and Algorithms",
        "description": "Essential data structures and algorithmic thinking",
        "category": "Computer Science",
        "difficulty_level": 3,
        "prerequisites": ["python_fundamentals"],
        "modules": [
            {
                "id": "arrays_lists",
                "name": "Arrays and Lists",
                "description": "Working with linear data structures",
                "tags": ["data-structures", "arrays", "lists"],
                "estimated_duration": 40,
                "difficulty_level": 2,
                "milestones": [
                    {
                        "id": "array_mastery",
                        "name": "Array Operations",
                        "description": "Achieve 85% accuracy in array questions",
                        "type": "accuracy_threshold",
                        "target_value": 85.0
                    }
                ]
            },
            {
                "id": "stacks_queues",
                "name": "Stacks and Queues",
                "description": "LIFO and FIFO data structures",
                "tags": ["data-structures", "stack", "queue"],
                "prerequisites": ["arrays_lists"],
                "estimated_duration": 35,
                "difficulty_level": 3,
                "milestones": [
                    {
                        "id": "stack_queue_mastery",
                        "name": "Stack/Queue Expert",
                        "description": "Master stack and queue operations",
                        "type": "mastery_level",
                        "target_value": 90.0
                    }
                ]
            }
        ]
    }
}
