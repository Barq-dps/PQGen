import os
import logging
from flask import Flask, redirect, request, jsonify, send_from_directory, Response, session, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime

# Import your improved modules with correct functions
from pdf_content_analyzer import extract_text_from_pdf, analyze_pdf_content
from llm_challenge_generator import (
    generate_single_challenge,
    generate_short_hint_for_challenge,
    extract_topics_from_content,
    is_model_ready
)
from challenge_generator import generate_fallback_challenges

# Import authentication module
from auth import (
    init_firebase, require_auth, get_current_user, register_user, authenticate_user,
    generate_jwt_token, verify_jwt_token, get_user_profile
)
from database import is_database_available

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
if is_model_ready():
    logger.info("✅ OpenAI API key detected; model is READY to generate challenges.")
else:
    logger.error("❌ OpenAI API key missing or invalid; model is NOT ready! Check your .env or env var.")

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
CORS(app, supports_credentials=True)

# Initialize Firebase
firebase_initialized = init_firebase()
if not firebase_initialized:
    logger.warning("Firebase initialization failed - authentication features will be limited")

logger.info("Starting PQGen backend with high impact features...")
logger.info("Features: Challenge State Management, Progress Bar, Topic Selection, Parallel Generation")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global storage for documents and progress
documents = {}
document_progress = {}
document_topics = {}
document_challenges = {}
challenge_states = {}

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=3)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static_files(filename):
    return send_from_directory('frontend', filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_progress(doc_id, status, progress=0, message="", topics=None, challenges=None):
    """Update progress for a document"""
    document_progress[doc_id] = {
        'status': status,
        'progress': progress,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'topics': topics,
        'challenges': challenges
    }
    logger.info(f"Progress updated for {doc_id}: {status} - {message}")

def extract_topics_async(doc_id, file_path):
    """Extract topics from PDF in background using improved system"""
    try:
        update_progress(doc_id, 'extracting', 10, 'Extracting text from PDF...')
        
        # 1. Extract raw text from PDF
        content = extract_text_from_pdf(file_path)
        if not content or len(content.strip()) < 10:
            update_progress(doc_id, 'error', 0, 'Failed to extract meaningful content from PDF')
            return
        
        update_progress(doc_id, 'extracting', 30, 'Analyzing content for topics...')
        
        # 2. Use improved topic extraction system
        try:
            # Try enhanced topic extraction first
            topics = extract_topics_from_content(content, file_path)
            if topics and len(topics) > 0:
                valid_topics = validate_topics(topics, content)
            else:
                # Fallback to basic analysis if enhanced extraction fails
                analysis = analyze_pdf_content(content)
                raw_topics = analysis.get('topics', [])
                valid_topics = validate_topics(raw_topics, content)
        except Exception as e:
            logger.warning(f"Enhanced topic extraction failed, using fallback: {e}")
            # Fallback to basic analysis
            analysis = analyze_pdf_content(content)
            raw_topics = analysis.get('topics', [])
            valid_topics = validate_topics(raw_topics, content)
        
        # 3. If nothing valid, show error
        if not valid_topics:
            valid_topics = ["Error extracting topics. Please try again."]
        
        # 4. Store and report
        document_topics[doc_id] = valid_topics
        update_progress(
            doc_id,
            'completed',
            100,
            f'Found {len(valid_topics)} topics',
            topics=valid_topics
        )
        logger.info(f"Topic extraction completed for {doc_id}: {len(valid_topics)} topics found")
        
    except Exception as e:
        logger.error(f"Error extracting topics for {doc_id}: {e}")
        update_progress(doc_id, 'error', 0, f'Error extracting topics: {e}')

def validate_topics(raw_topics, content):
    """Validate and clean extracted topics"""
    valid_topics = []
    
    for topic in raw_topics:
        if not topic or not isinstance(topic, str):
            continue
            
        topic = topic.strip()
        
        # Skip empty or very short topics
        if len(topic) < 3:
            continue
            
        # Skip very long topics (likely not actual topics)
        if len(topic) > 50:
            continue
            
        # Skip topics that are just numbers or special characters
        if topic.isdigit() or not any(c.isalpha() for c in topic):
            continue
            
        # Clean up the topic
        topic = topic.replace('_', ' ').title()
        
        # Add if not already present
        if topic not in valid_topics:
            valid_topics.append(topic)
    
    return valid_topics[:10]  # Limit to 10 topics

def get_topic_snippet(text: str, topic: str, window_chars: int = 2000) -> str:
    """
    Return up to `window_chars` of `text` centered on the first occurrence of `topic`.
    If `topic` isn't found, return the first `window_chars` of the text.
    """
    lower = text.lower()
    idx = lower.find(topic.lower())
    if idx != -1:
        half = window_chars // 2
        start = max(0, idx - half)
        end = min(len(text), idx + half)
        return text[start:end]
    return text[:window_chars]

def generate_challenge_with_improved_system(content, difficulty, topic):
    """Generate challenges using the improved challenge generation system"""
    challenges = []
    
    # Define challenge types to generate
    challenge_types = ['multiple-choice', 'debugging', 'fill-in-the-blank']
    
    for challenge_type in challenge_types:
        try:
            logger.info(f"Generating {challenge_type} challenge for topic: {topic}")
            
            challenge = generate_single_challenge(
                content=content,
                challenge_type=challenge_type,
                difficulty=difficulty,
                topic=topic
            )
            
            if challenge:
                # Ensure challenge has required fields
                challenge['id'] = challenge.get('id', f"{challenge_type}_{uuid.uuid4().hex[:8]}")
                challenge['type'] = challenge_type
                challenge['topic'] = topic
                challenge['difficulty'] = difficulty
                
                # Pre-generate hint for instant display
                try:
                    hint = generate_short_hint_for_challenge(challenge)
                    challenge['hint'] = hint
                except Exception as e:
                    logger.warning(f"Failed to generate hint for {challenge_type}: {e}")
                    challenge['hint'] = f"Think about the key concepts in {topic}."
                
                challenges.append(challenge)
                logger.info(f"Successfully generated {challenge_type} challenge for {topic}")
            else:
                logger.warning(f"Failed to generate {challenge_type} challenge for {topic}")
                
        except Exception as e:
            logger.error(f"Error generating {challenge_type} challenge for {topic}: {e}")
            continue
    
    return challenges

def generate_challenges_async(doc_id, selected_topics, difficulty_settings):
    """Generate challenges for selected topics in background using improved system"""
    try:
        update_progress(doc_id, 'generating', 10, 'Starting challenge generation...')
        
        # 1) Load full document text
        doc_info = documents.get(doc_id)
        if not doc_info:
            update_progress(doc_id, 'error', 0, 'Document not found')
            return
        
        full_content = extract_text_from_pdf(doc_info['file_path'])
        if not full_content:
            update_progress(doc_id, 'error', 0, 'Failed to extract document content')
            return
        
        challenges = []
        total = len(selected_topics)
        
        for i, topic_info in enumerate(selected_topics):
            topic = topic_info['topic']
            difficulty = topic_info['difficulty']
            
            progress = 10 + (i / total) * 80
            update_progress(doc_id, 'generating', progress, f'Generating challenges for: {topic}')
            
            try:
                # 2) Grab a focused snippet for this topic
                snippet = get_topic_snippet(full_content, topic, window_chars=2000)
                
                # 3) Use improved AI generation system
                if is_model_ready():
                    ai_chals = generate_challenge_with_improved_system(snippet, difficulty, topic)
                    if ai_chals:
                        challenges.extend(ai_chals)
                        logger.info(f"Generated {len(ai_chals)} challenges for {topic}")
                        continue
                
                # 4) Static fallback if AI fails
                logger.warning(f"AI generation failed for {topic}, using fallback")
                fallback = generate_fallback_challenges([topic], difficulty)
                if fallback:
                    challenges.extend(fallback)
                    
            except Exception as e:
                logger.error(f"Error generating challenges for {topic}: {e}")
                # Continue with next topic instead of failing completely
                continue
        
        # 5) Store challenges and init states
        document_challenges[doc_id] = challenges
        for c in challenges:
            cid = c.get('id', str(uuid.uuid4()))
            c['id'] = cid
            challenge_states[cid] = {
                'status': 'unsolved',
                'attempts': 0,
                'max_attempts': 3,
                'best_score': 0,
                'last_submission': None,
                'solved_at': None
            }
        
        update_progress(doc_id, 'completed', 100, f'Generated {len(challenges)} challenges', challenges=challenges)
        logger.info(f"Challenge generation completed for {doc_id}: {len(challenges)} challenges generated")
        
    except Exception as e:
        logger.error(f"Error in challenge generation for {doc_id}: {e}")
        update_progress(doc_id, 'error', 0, f'Error generating challenges: {e}')

# Routes for serving frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
async def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Register user
        success, message, user_data = await register_user(username, email, password)
        
        if success:
            # Generate JWT token
            token = generate_jwt_token(user_data)
            if token:
                session['auth_token'] = token
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'user': {
                        'user_id': user_data['id'],
                        'username': user_data['username'],
                        'email': user_data['email']
                    },
                    'token': token
                }), 201
            else:
                return jsonify({'error': 'Failed to generate authentication token'}), 500
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
async def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        success, message, user_data = await authenticate_user(email, password)
        
        if success:
            # Generate JWT token
            token = generate_jwt_token(user_data)
            if token:
                session['auth_token'] = token
                
                return jsonify({
                    'success': True,
                    'message': message,
                    'user': {
                        'user_id': user_data['id'],
                        'username': user_data['username'],
                        'email': user_data['email']
                    },
                    'token': token
                }), 200
            else:
                return jsonify({'error': 'Failed to generate authentication token'}), 500
        else:
            return jsonify({'error': message}), 401
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        session.pop('auth_token', None)
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user.get('id'),
                'username': user.get('username'),
                'email': user.get('email'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500

@app.route('/api/user/settings', methods=['GET'])
@require_auth
def get_user_settings():
    """Get user settings"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user settings from database or return defaults
        settings = {
            'theme': 'light',
            'difficulty_preference': 'medium',
            'challenge_types': ['multiple-choice', 'debugging', 'fill-in-the-blank'],
            'notifications': True
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        }), 200
        
    except Exception as e:
        logger.error(f"Settings error: {e}")
        return jsonify({'error': 'Failed to get settings'}), 500

# Document upload and processing routes
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process PDF file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files are allowed.'}), 400
        
        # Generate unique document ID and save file
        doc_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{doc_id}_{filename}")
        file.save(file_path)
        
        # Store document info
        documents[doc_id] = {
            'id': doc_id,
            'filename': filename,
            'file_path': file_path,
            'upload_time': datetime.now().isoformat()
        }
        
        # Start topic extraction in background
        executor.submit(extract_topics_async, doc_id, file_path)
        
        logger.info(f"File uploaded successfully: {filename} (ID: {doc_id})")
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'document_id': doc_id,
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/documents/<doc_id>/progress', methods=['GET'])
def get_progress(doc_id):
    """Get processing progress for a document"""
    try:
        if doc_id not in document_progress:
            return jsonify({
                'status': 'not_found',
                'progress': 0,
                'message': 'Document not found or processing not started'
            }), 404
        
        progress_data = document_progress[doc_id]
        
        # Return current progress as JSON
        response_data = {
            'status': progress_data['status'],
            'progress': progress_data['progress'],
            'message': progress_data['message'],
            'timestamp': progress_data['timestamp']
        }
        
        # Include topics if available
        if progress_data.get('topics'):
            response_data['topics'] = progress_data['topics']
        
        # Include challenges if available
        if progress_data.get('challenges'):
            response_data['challenges'] = progress_data['challenges']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error getting progress for {doc_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/documents/<doc_id>/topics', methods=['GET'])
def get_topics(doc_id):
    """Get extracted topics for a document"""
    try:
        if doc_id not in document_topics:
            return jsonify({'error': 'Topics not found or still processing'}), 404
        
        topics = document_topics[doc_id]
        return jsonify({
            'success': True,
            'topics': topics,
            'count': len(topics)
        })
        
    except Exception as e:
        logger.error(f"Error getting topics for {doc_id}: {str(e)}")
        return jsonify({'error': f'Failed to get topics: {str(e)}'}), 500

@app.route('/api/documents/<doc_id>/generate', methods=['POST'])
def generate_challenges(doc_id):
    """Generate challenges for selected topics"""
    try:
        data = request.get_json()
        selected_topics = data.get('topics', [])
        
        if not selected_topics:
            return jsonify({'error': 'No topics selected'}), 400
        
        logger.info(f"Starting challenge generation for {doc_id} with {len(selected_topics)} topics")
        
        # Start challenge generation in background
        executor.submit(generate_challenges_async, doc_id, selected_topics, {})
        
        return jsonify({
            'success': True,
            'message': f'Started generating challenges for {len(selected_topics)} topics',
            'document_id': doc_id
        })
        
    except Exception as e:
        logger.error(f"Error starting challenge generation for {doc_id}: {str(e)}")
        return jsonify({'error': f'Failed to start generation: {str(e)}'}), 500

# NEW ENDPOINT: Load generated challenges
@app.route('/api/documents/<doc_id>/challenges', methods=['GET'])
def get_challenges(doc_id):
    """Get generated challenges for a document"""
    try:
        if doc_id not in document_challenges:
            return jsonify({'error': 'Challenges not found or still generating'}), 404
        
        challenges = document_challenges[doc_id]
        
        # Add current state for each challenge
        for challenge in challenges:
            challenge_id = challenge.get('id')
            if challenge_id in challenge_states:
                challenge['state'] = challenge_states[challenge_id]
            else:
                challenge['state'] = {
                    'status': 'unsolved',
                    'attempts': 0,
                    'max_attempts': 3,
                    'best_score': 0
                }
        
        return jsonify({
            'success': True,
            'challenges': challenges,
            'count': len(challenges)
        })
        
    except Exception as e:
        logger.error(f"Error getting challenges for {doc_id}: {str(e)}")
        return jsonify({'error': f'Failed to get challenges: {str(e)}'}), 500

@app.route('/api/challenges/<challenge_id>/attempt', methods=['POST'])
def submit_attempt(challenge_id):
    """Submit an attempt for a challenge"""
    try:
        data = request.get_json()
        submitted_answer = data.get('answer', '')
        
        if challenge_id not in challenge_states:
            return jsonify({'error': 'Challenge not found'}), 404
        
        state = challenge_states[challenge_id]
        
        # Check if max attempts reached
        if state['attempts'] >= state['max_attempts'] and state['status'] != 'solved':
            return jsonify({
                'success': False,
                'message': 'Maximum attempts reached',
                'attempts': state['attempts'],
                'max_attempts': state['max_attempts']
            })
        
        # Find the challenge
        challenge = None
        for doc_id, challenges in document_challenges.items():
            for c in challenges:
                if c.get('id') == challenge_id:
                    challenge = c
                    break
            if challenge:
                break
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Increment attempts
        state['attempts'] += 1
        state['last_submission'] = submitted_answer
        
        # Check answer based on challenge type
        is_correct = False
        score = 0
        feedback = ""
        
        challenge_type = challenge.get('type', '')
        
        if challenge_type == 'multiple-choice':
            correct_answer = challenge.get('correct_answer', 0)
            try:
                submitted_index = int(submitted_answer)
                is_correct = submitted_index == correct_answer
                score = 100 if is_correct else 0
                if is_correct:
                    feedback = challenge.get('explanation', 'Correct!')
                else:
                    feedback = f"Incorrect. The correct answer is option {correct_answer + 1}."
            except (ValueError, TypeError):
                feedback = "Invalid answer format. Please select a valid option."
        
        elif challenge_type == 'debugging':
            # For debugging challenges, check if the submitted code fixes the bug
            # This is a simplified check - in a real system you'd want to run the code
            bug_keywords = ['=', '==', '<=', '>=', '!=', 'range', 'len', 'append']
            submitted_lower = submitted_answer.lower()
            
            if any(keyword in submitted_lower for keyword in bug_keywords):
                is_correct = True
                score = 100
                feedback = challenge.get('fix_explanation', 'Good job fixing the bug!')
            else:
                feedback = "Try to identify the specific bug in the code. Look at the error message and expected output."
        
        elif challenge_type == 'fill-in-the-blank':
            # For fill-in-the-blank, check against correct answers
            blanks = challenge.get('blanks', [])
            if blanks:
                try:
                    submitted_answers = json.loads(submitted_answer) if isinstance(submitted_answer, str) else submitted_answer
                    correct_count = 0
                    total_blanks = len(blanks)
                    
                    for i, blank in enumerate(blanks):
                        if i < len(submitted_answers):
                            if submitted_answers[i] == blank.get('correct_answer'):
                                correct_count += 1
                    
                    score = (correct_count / total_blanks) * 100
                    is_correct = score >= 80  # 80% threshold for "correct"
                    feedback = f"You got {correct_count}/{total_blanks} blanks correct."
                    
                except (json.JSONDecodeError, TypeError, IndexError):
                    feedback = "Invalid answer format for fill-in-the-blank question."
            else:
                feedback = "No answer key available for this question."
        
        # Update state
        if is_correct:
            state['status'] = 'solved'
            state['solved_at'] = datetime.now().isoformat()
            state['best_score'] = max(state['best_score'], score)
        
        return jsonify({
            'success': True,
            'correct': is_correct,
            'score': score,
            'feedback': feedback,
            'attempts': state['attempts'],
            'max_attempts': state['max_attempts'],
            'status': state['status']
        })
        
    except Exception as e:
        logger.error(f"Error submitting attempt for {challenge_id}: {str(e)}")
        return jsonify({'error': f'Failed to submit attempt: {str(e)}'}), 500

@app.route('/api/challenges/<challenge_id>/hint', methods=['GET'])
def get_hint(challenge_id):
    """Get hint for a challenge"""
    try:
        # Find the challenge
        challenge = None
        for doc_id, challenges in document_challenges.items():
            for c in challenges:
                if c.get('id') == challenge_id:
                    challenge = c
                    break
            if challenge:
                break
        
        if not challenge:
            return jsonify({'error': 'Challenge not found'}), 404
        
        # Return pre-generated hint or generate new one
        hint = challenge.get('hint')
        if not hint:
            try:
                hint = generate_short_hint_for_challenge(challenge)
                # Cache the hint for future use
                challenge['hint'] = hint
            except Exception as e:
                logger.warning(f"Failed to generate hint for {challenge_id}: {e}")
                hint = f"Think about the key concepts in {challenge.get('topic', 'this topic')}."
        
        return jsonify({
            'success': True,
            'hint': hint
        })
        
    except Exception as e:
        logger.error(f"Error getting hint for {challenge_id}: {str(e)}")
        return jsonify({'error': f'Failed to get hint: {str(e)}'}), 500

@app.route('/api/challenges/<challenge_id>/state', methods=['GET'])
def get_challenge_state(challenge_id):
    """Get current state of a challenge"""
    try:
        if challenge_id not in challenge_states:
            return jsonify({'error': 'Challenge not found'}), 404
        
        state = challenge_states[challenge_id]
        return jsonify({
            'success': True,
            'state': state
        })
        
    except Exception as e:
        logger.error(f"Error getting state for {challenge_id}: {str(e)}")
        return jsonify({'error': f'Failed to get challenge state: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

