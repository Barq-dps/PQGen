import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import uuid
import threading
from werkzeug.utils import secure_filename

from pdf_content_analyzer import extract_topics_and_content
from challenge_generator import generate_challenges_for_topics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Directory for storing uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), 'frontend')

# In-memory storage for document processing status and results
documents = {}

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Generate a unique ID for this document
    document_id = str(uuid.uuid4())
    
    # Save the file
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"{document_id}_{filename}")
    file.save(file_path)
    
    # Initialize document status
    documents[document_id] = {
        'status': 'processing',
        'file_path': file_path,
        'challenges': [],
        'error': None
    }
    
    # Get difficulty from request (default to medium)
    difficulty = request.args.get('difficulty', 'medium')
    
    # Process the document in a background thread
    threading.Thread(
        target=process_document,
        args=(document_id, file_path, difficulty),
        daemon=True
    ).start()
    
    return jsonify({
        'document_id': document_id,
        'status': 'processing'
    })

def process_document(document_id, file_path, difficulty):
    try:
        structured = extract_topics_and_content(file_path)
        if not isinstance(structured, dict):
            raise ValueError(f"Expected dict from extract, got {type(structured)}")

        topics_with_content = structured.get("topics_with_content", [])
        if not isinstance(topics_with_content, list):
            raise ValueError("topics_with_content must be a list")
            
        # Check if we have any topics before proceeding
        if not topics_with_content:
            documents[document_id].update({
                "status": "error",
                "error": "No topics could be extracted from the PDF. Please try a different document with clear headings and content."
            })
            return

        # Pass the entire structured dictionary instead of just topics_with_content
        # This ensures the LLM has access to the full PDF content
        challenges = generate_challenges_for_topics(structured, difficulty=difficulty)
        if not challenges:
            raise RuntimeError("No challenges generated for any topic")

        # success → write back
        documents[document_id].update({
            "status": "completed",
            "challenges": challenges,
            "topics": structured.get("topics", []),
        })

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        documents[document_id].update({
            "status": "error",
            "error": str(e),
        })



@app.route('/api/documents/<document_id>/status', methods=['GET'])
def get_document_status(document_id):
    if document_id not in documents:
        return jsonify({'error': 'Document not found'}), 404
    
    return jsonify({
        'status': documents[document_id]['status'],
        'error':  documents[document_id]['error']
    })

@app.route('/api/documents/<document_id>/challenges', methods=['GET'])
def get_document_challenges(document_id):
    if document_id not in documents:
        return jsonify({'error': 'Document not found'}), 404
    
    if documents[document_id]['status'] != 'completed':
        return jsonify({'error': 'Document processing not completed'}), 400
    
    return jsonify({
        'challenges': documents[document_id]['challenges'],
        'topics':     documents[document_id].get('topics', [])
    })

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

if __name__ == '__main__':
    print("Starting Flask app with template-based challenge generation...")
    app.run(debug=True, host='0.0.0.0')
