"""
Simple web interface for the qBank system using Flask.
Provides a user-friendly web-based interface for studying.
"""

try:
    from flask import Flask, request, jsonify, render_template_string, session
    from flask_cors import CORS
except ImportError:
    Flask = None
    print("Flask not installed. Web interface disabled. Install with: pip install flask flask-cors")

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from qbank import QuestionBankManager


# HTML Templates
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>qBank - Smart Learning System</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { color: #2c3e50; margin: 0; font-size: 2.5em; }
        .header p { color: #7f8c8d; font-size: 1.2em; margin: 10px 0; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card h3 { margin: 0 0 10px 0; font-size: 2em; }
        .stat-card p { margin: 0; opacity: 0.9; }
        .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .action-card { border: 2px solid #ecf0f1; border-radius: 8px; padding: 25px; text-align: center; transition: all 0.3s; }
        .action-card:hover { border-color: #3498db; box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2); }
        .btn { background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; text-decoration: none; display: inline-block; transition: all 0.3s; }
        .btn:hover { background: #2980b9; transform: translateY(-2px); }
        .btn-success { background: #27ae60; }
        .btn-success:hover { background: #229954; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #e67e22; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .progress-bar { background: #ecf0f1; height: 8px; border-radius: 4px; overflow: hidden; margin: 10px 0; }
        .progress-fill { background: linear-gradient(90deg, #27ae60, #2ecc71); height: 100%; transition: width 0.5s; }
        .user-info { background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 qBank</h1>
            <p>Intelligent Spaced Repetition Learning System</p>
        </div>
        
        <div class="user-info">
            <strong>User:</strong> {{ user_id }} | 
            <strong>Level:</strong> {{ user_level }} | 
            <strong>Rating:</strong> {{ user_rating }} |
            <strong>Bank:</strong> {{ bank_name }}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>{{ total_questions }}</h3>
                <p>Total Questions</p>
            </div>
            <div class="stat-card">
                <h3>{{ questions_due }}</h3>
                <p>Due for Review</p>
            </div>
            <div class="stat-card">
                <h3>{{ recent_accuracy }}%</h3>
                <p>Recent Accuracy</p>
            </div>
            <div class="stat-card">
                <h3>{{ total_sessions }}</h3>
                <p>Study Sessions</p>
            </div>
        </div>
        
        <div class="actions">
            <div class="action-card">
                <h3>📚 Study Session</h3>
                <p>Review questions due for today using spaced repetition</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ (questions_due / max(total_questions, 1) * 100) if questions_due <= total_questions else 100 }}%"></div>
                </div>
                <p>{{ questions_due }} questions ready</p>
                <a href="/study" class="btn btn-success">Start Studying</a>
            </div>
            
            <div class="action-card">
                <h3>🎯 Practice Mode</h3>
                <p>Practice specific topics or all subjects</p>
                <a href="/practice" class="btn">Start Practice</a>
            </div>
            
            <div class="action-card">
                <h3>➕ Add Questions</h3>
                <p>Add new questions to your question bank</p>
                <a href="/add" class="btn btn-warning">Add Question</a>
            </div>
            
            <div class="action-card">
                <h3>📊 Analytics</h3>
                <p>View detailed statistics and progress insights</p>
                <a href="/stats" class="btn">View Stats</a>
            </div>
            
            <div class="action-card">
                <h3>🔍 Search</h3>
                <p>Search through your question bank</p>
                <a href="/search" class="btn">Search Questions</a>
            </div>
            
            <div class="action-card">
                <h3>📋 Manage Bank</h3>
                <p>Import, export, and manage your question bank</p>
                <a href="/manage" class="btn btn-danger">Manage</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

STUDY_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Study Session - qBank</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .progress { background: #ecf0f1; height: 12px; border-radius: 6px; margin: 20px 0; overflow: hidden; }
        .progress-bar { background: linear-gradient(90deg, #3498db, #2980b9); height: 100%; transition: width 0.5s; }
        .question-card { border: 2px solid #ecf0f1; border-radius: 8px; padding: 25px; margin: 20px 0; }
        .question-text { font-size: 1.3em; margin-bottom: 20px; color: #2c3e50; line-height: 1.5; }
        .answers { list-style: none; padding: 0; }
        .answer { margin: 10px 0; }
        .answer input { margin-right: 10px; }
        .answer label { cursor: pointer; padding: 15px; border: 2px solid #ecf0f1; border-radius: 6px; display: block; transition: all 0.3s; }
        .answer label:hover { border-color: #3498db; background: #f8f9fa; }
        .answer input:checked + label { border-color: #3498db; background: #e3f2fd; }
        .btn { background: #3498db; color: white; padding: 12px 30px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin: 10px 5px; transition: all 0.3s; }
        .btn:hover { background: #2980b9; }
        .btn-success { background: #27ae60; }
        .btn-danger { background: #e74c3c; }
        .feedback { padding: 15px; border-radius: 6px; margin: 15px 0; }
        .feedback.correct { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .feedback.incorrect { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .session-complete { text-align: center; padding: 40px; }
        .back-link { display: inline-block; margin: 20px 0; color: #3498db; text-decoration: none; }
        .back-link:hover { text-decoration: underline; }
        .question-info { background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 0.9em; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Dashboard</a>
        
        <div class="header">
            <h1>📚 Study Session</h1>
            <div class="progress">
                <div class="progress-bar" style="width: 0%" id="progress-bar"></div>
            </div>
            <p id="progress-text">Question 0 of 0</p>
        </div>
        
        <div id="study-content">
            <div id="loading">
                <p>Loading questions...</p>
            </div>
        </div>
    </div>
    
    <script>
        let currentQuestionIndex = 0;
        let questions = [];
        let answers = [];
        let sessionStarted = false;
        
        async function loadQuestions() {
            try {
                const response = await fetch('/api/study/questions');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('study-content').innerHTML = `
                        <div class="session-complete">
                            <h2>No Questions Available</h2>
                            <p>${data.error}</p>
                            <a href="/" class="btn">Back to Dashboard</a>
                        </div>
                    `;
                    return;
                }
                
                questions = data.questions;
                if (questions.length === 0) {
                    document.getElementById('study-content').innerHTML = `
                        <div class="session-complete">
                            <h2>No Questions Due</h2>
                            <p>Great job! You're up to date with your reviews.</p>
                            <a href="/" class="btn">Back to Dashboard</a>
                        </div>
                    `;
                    return;
                }
                
                showQuestion();
            } catch (error) {
                console.error('Error loading questions:', error);
                document.getElementById('study-content').innerHTML = `
                    <div class="session-complete">
                        <h2>Error</h2>
                        <p>Failed to load questions. Please try again.</p>
                        <a href="/" class="btn">Back to Dashboard</a>
                    </div>
                `;
            }
        }
        
        function showQuestion() {
            if (currentQuestionIndex >= questions.length) {
                completeSession();
                return;
            }
            
            const question = questions[currentQuestionIndex];
            const progress = ((currentQuestionIndex) / questions.length) * 100;
            
            document.getElementById('progress-bar').style.width = progress + '%';
            document.getElementById('progress-text').textContent = 
                `Question ${currentQuestionIndex + 1} of ${questions.length}`;
            
            // Shuffle answers
            const allAnswers = [...question.answers];
            for (let i = allAnswers.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [allAnswers[i], allAnswers[j]] = [allAnswers[j], allAnswers[i]];
            }
            
            const answersHtml = allAnswers.map((answer, index) => `
                <li class="answer">
                    <input type="radio" id="answer${index}" name="answer" value="${answer.id}">
                    <label for="answer${index}">${answer.text}</label>
                </li>
            `).join('');
            
            document.getElementById('study-content').innerHTML = `
                <div class="question-card">
                    <div class="question-info">
                        Tags: ${question.tags.join(', ')} | 
                        Difficulty: ${question.difficulty} |
                        Accuracy: ${question.accuracy.toFixed(1)}%
                    </div>
                    <div class="question-text">${question.question_text}</div>
                    <ul class="answers">
                        ${answersHtml}
                    </ul>
                    <button class="btn" onclick="submitAnswer()">Submit Answer</button>
                    <button class="btn btn-danger" onclick="skipQuestion()">Skip</button>
                </div>
            `;
        }
        
        async function submitAnswer() {
            const selectedAnswer = document.querySelector('input[name="answer"]:checked');
            if (!selectedAnswer) {
                alert('Please select an answer');
                return;
            }
            
            const question = questions[currentQuestionIndex];
            const answerId = selectedAnswer.value;
            
            try {
                const response = await fetch('/api/study/answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question_id: question.id,
                        answer_id: answerId
                    })
                });
                
                const result = await response.json();
                showFeedback(result);
                
            } catch (error) {
                console.error('Error submitting answer:', error);
                alert('Error submitting answer. Please try again.');
            }
        }
        
        function showFeedback(result) {
            const feedbackClass = result.correct ? 'correct' : 'incorrect';
            const feedbackIcon = result.correct ? '✅' : '❌';
            
            let feedbackHtml = `
                <div class="feedback ${feedbackClass}">
                    <h3>${feedbackIcon} ${result.correct ? 'Correct!' : 'Incorrect'}</h3>
            `;
            
            if (!result.correct) {
                feedbackHtml += `<p><strong>Correct answer:</strong> ${result.correct_answer.text}</p>`;
            }
            
            if (result.explanation) {
                feedbackHtml += `<p><strong>Explanation:</strong> ${result.explanation}</p>`;
            }
            
            feedbackHtml += `
                <p><strong>Your rating:</strong> ${result.user_rating.toFixed(1)}</p>
                <button class="btn" onclick="nextQuestion()">Next Question</button>
            </div>
            `;
            
            document.querySelector('.question-card').innerHTML += feedbackHtml;
        }
        
        function nextQuestion() {
            currentQuestionIndex++;
            showQuestion();
        }
        
        function skipQuestion() {
            if (confirm('Are you sure you want to skip this question?')) {
                currentQuestionIndex++;
                showQuestion();
            }
        }
        
        async function completeSession() {
            try {
                const response = await fetch('/api/study/complete', { method: 'POST' });
                const result = await response.json();
                
                document.getElementById('study-content').innerHTML = `
                    <div class="session-complete">
                        <h2>🎉 Session Complete!</h2>
                        <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin: 20px 0;">
                            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                                <h3>${result.questions_count}</h3>
                                <p>Questions</p>
                            </div>
                            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                                <h3>${result.correct_count}</h3>
                                <p>Correct</p>
                            </div>
                            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                                <h3>${result.accuracy.toFixed(1)}%</h3>
                                <p>Accuracy</p>
                            </div>
                            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                                <h3>${result.user_rating.toFixed(1)}</h3>
                                <p>New Rating</p>
                            </div>
                        </div>
                        <a href="/" class="btn btn-success">Back to Dashboard</a>
                        <a href="/study" class="btn">Start Another Session</a>
                    </div>
                `;
            } catch (error) {
                console.error('Error completing session:', error);
            }
        }
        
        // Start loading questions when page loads
        document.addEventListener('DOMContentLoaded', loadQuestions);
    </script>
</body>
</html>
"""


class QBankWebApp:
    """Web application for qBank system."""
    
    def __init__(self, question_bank_file: str = "questions.json", user_id: str = "web_user"):
        if Flask is None:
            raise ImportError("Flask is required for web interface. Install with: pip install flask flask-cors")
        
        self.app = Flask(__name__)
        self.app.secret_key = "qbank_secret_key_change_in_production"
        CORS(self.app)
        
        self.question_bank_file = question_bank_file
        self.default_user_id = user_id
        self.manager = None
        
        self._setup_routes()
        self._load_question_bank()
    
    def _load_question_bank(self):
        """Load or create question bank."""
        self.manager = QuestionBankManager("Web Question Bank", self.default_user_id)
        
        if os.path.exists(self.question_bank_file):
            try:
                self.manager.import_bank(self.question_bank_file)
                print(f"Loaded question bank from {self.question_bank_file}")
            except Exception as e:
                print(f"Error loading question bank: {e}")
        else:
            print(f"Creating new question bank: {self.question_bank_file}")
    
    def _save_question_bank(self):
        """Save question bank to file."""
        try:
            self.manager.export_bank(self.question_bank_file)
        except Exception as e:
            print(f"Error saving question bank: {e}")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def home():
            stats = self.manager.get_user_statistics()
            
            template_vars = {
                'user_id': self.manager.current_user_id,
                'user_level': stats['user_level'],
                'user_rating': f"{stats['user_rating']:.1f}",
                'bank_name': self.manager.question_bank.name,
                'total_questions': stats['total_questions'],
                'questions_due': stats['questions_due'],
                'recent_accuracy': f"{stats['recent_accuracy']:.1f}",
                'total_sessions': stats['total_sessions']
            }
            
            return render_template_string(HOME_TEMPLATE, **template_vars)
        
        @self.app.route('/study')
        def study():
            return render_template_string(STUDY_TEMPLATE)
        
        @self.app.route('/api/study/questions')
        def api_study_questions():
            try:
                questions = self.manager.start_study_session(max_questions=10)
                
                if not questions:
                    return jsonify({"error": "No questions due for review"})
                
                questions_data = []
                for q in questions:
                    questions_data.append({
                        'id': q.id,
                        'question_text': q.question_text,
                        'answers': [{'id': a.id, 'text': a.text} for a in q.answers],
                        'tags': q.tags,
                        'difficulty': self.manager.elo_system.get_difficulty_category(q.elo_rating),
                        'accuracy': q.accuracy
                    })
                
                return jsonify({"questions": questions_data})
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/study/answer', methods=['POST'])
        def api_study_answer():
            try:
                data = request.get_json()
                question_id = data['question_id']
                answer_id = data['answer_id']
                
                result = self.manager.answer_question(question_id, answer_id, 5.0)  # Default 5s response time
                
                response_data = {
                    'correct': result['correct'],
                    'user_rating': result['user_rating'],
                    'correct_answer': {
                        'text': result['correct_answer'].text
                    }
                }
                
                if hasattr(result['correct_answer'], 'explanation') and result['correct_answer'].explanation:
                    response_data['explanation'] = result['correct_answer'].explanation
                
                return jsonify(response_data)
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/study/complete', methods=['POST'])
        def api_study_complete():
            try:
                session = self.manager.end_study_session()
                
                if not session:
                    return jsonify({"error": "No active session"}), 400
                
                self._save_question_bank()
                
                return jsonify({
                    'questions_count': session.questions_count,
                    'correct_count': session.correct_count,
                    'accuracy': session.accuracy,
                    'user_rating': self.manager.user_tracker.get_user_rating(self.manager.current_user_id)
                })
                
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/stats')
        def api_stats():
            try:
                stats = self.manager.get_user_statistics()
                return jsonify(stats)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/practice')
        def practice():
            # Similar to study but allows topic selection
            return "<h1>Practice Mode</h1><p>Coming soon!</p><a href='/'>Back</a>"
        
        @self.app.route('/add')
        def add_question():
            return "<h1>Add Question</h1><p>Coming soon!</p><a href='/'>Back</a>"
        
        @self.app.route('/stats')
        def stats():
            return "<h1>Statistics</h1><p>Coming soon!</p><a href='/'>Back</a>"
        
        @self.app.route('/search')
        def search():
            return "<h1>Search Questions</h1><p>Coming soon!</p><a href='/'>Back</a>"
        
        @self.app.route('/manage')
        def manage():
            return "<h1>Manage Bank</h1><p>Coming soon!</p><a href='/'>Back</a>"
    
    def run(self, host='127.0.0.1', port=5000, debug=True):
        """Run the web application."""
        print(f"Starting qBank Web Interface...")
        print(f"Access your learning dashboard at: http://{host}:{port}")
        print(f"Question bank: {self.question_bank_file}")
        print(f"User: {self.default_user_id}")
        
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main function to run the web app."""
    import argparse
    
    parser = argparse.ArgumentParser(description="qBank Web Interface")
    parser.add_argument("--bank", "-b", default="questions.json", 
                       help="Question bank file (default: questions.json)")
    parser.add_argument("--user", "-u", default="web_user",
                       help="User ID (default: web_user)")
    parser.add_argument("--host", default="127.0.0.1",
                       help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=5000,
                       help="Port to bind to (default: 5000)")
    parser.add_argument("--debug", action="store_true",
                       help="Run in debug mode")
    
    args = parser.parse_args()
    
    try:
        app = QBankWebApp(args.bank, args.user)
        app.run(host=args.host, port=args.port, debug=args.debug)
    except ImportError as e:
        print(f"Error: {e}")
        print("To install required dependencies, run: pip install flask flask-cors")
    except KeyboardInterrupt:
        print("\nShutting down qBank Web Interface...")
    except Exception as e:
        print(f"Error starting web interface: {e}")


if __name__ == "__main__":
    main()
