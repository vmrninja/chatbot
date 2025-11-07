"""
Security Assessment Chatbot Backend
Handles document uploads and chat interactions with Claude API
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from anthropic import Anthropic
from pathlib import Path
import mimetypes
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('./uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Storage for uploaded documents
documents = {}

# Load environment variables from .env file if present
load_dotenv()

# Initialize Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables or .env file")
client = Anthropic(api_key=api_key)


def read_file_content(file_path):
    """Read and return file content as text."""
    try:
        # Try reading as text
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # If binary file, return a message
        return f"[Binary file: {file_path.name}. Content not readable as text.]"


@app.route('/')
def index():
    """Serve the HTML frontend."""
    return send_from_directory('.', 'index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate unique ID for this file
    file_id = str(uuid.uuid4())
    
    # Save file
    file_path = UPLOAD_FOLDER / f"{file_id}_{file.filename}"
    file.save(file_path)
    
    # Read and store content
    content = read_file_content(file_path)
    
    documents[file_id] = {
        'filename': file.filename,
        'path': str(file_path),
        'content': content
    }
    
    return jsonify({
        'file_id': file_id,
        'filename': file.filename,
        'message': 'File uploaded successfully'
    })


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and return Claude's response."""
    data = request.json
    user_message = data.get('message', '')
    file_ids = data.get('file_ids', [])
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Build context from uploaded documents
    context = ""
    if file_ids:
        context = "=== UPLOADED DOCUMENTS ===\n\n"
        for file_id in file_ids:
            if file_id in documents:
                doc = documents[file_id]
                context += f"Document: {doc['filename']}\n"
                context += "-" * 50 + "\n"
                context += doc['content'] + "\n\n"
    
    # Build the prompt
    system_prompt = """You are a security compliance assistant helping to verify assessment questionnaire answers against security policies.

Your role is to:
1. Analyze uploaded security policies and assessment questionnaires
2. Check if answers comply with stated policies
3. Identify gaps, inconsistencies, or areas of concern
4. Provide specific references to relevant policy sections
5. Suggest improvements or corrections when needed

Be thorough, objective, and cite specific sections from the documents when making assessments."""

    # Prepare messages
    messages = []
    
    if context:
        # Add context as a user message first
        messages.append({
            "role": "user",
            "content": context
        })
        messages.append({
            "role": "assistant",
            "content": "I have reviewed the uploaded documents. How can I help you analyze them?"
        })
    
    # Add the actual user question
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Prepare the messages for the older API version
        prompt = system_prompt + "\n\n"
        for msg in messages:
            if msg["role"] == "user":
                prompt += f"\n\nHuman: {msg['content']}"
            else:
                prompt += f"\n\nAssistant: {msg['content']}"
        prompt += "\n\nAssistant:"
        print("Prompt to Claude API:", prompt)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=prompt,
            max_tokens=4096,
        )
        
        # Extract response text
        response_text = response.content
        
        return jsonify({
            'response': response_text
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error calling Claude API: {str(e)}'
        }), 500


@app.route('/clear', methods=['POST'])
def clear_documents():
    """Clear all uploaded documents."""
    global documents
    
    # Delete files
    for doc in documents.values():
        try:
            os.remove(doc['path'])
        except:
            pass
    
    documents = {}
    
    return jsonify({
        'message': 'All documents cleared'
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Security Assessment Chatbot Backend")
    print("=" * 60)
    print(f"\n✓ Upload folder: {UPLOAD_FOLDER.absolute()}")
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️  WARNING: ANTHROPIC_API_KEY environment variable not set!")
        print("   Please set it before starting the server:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
    else:
        print("\n✓ Anthropic API key found")
    
    print("\n📝 Starting server on http://localhost:5000")
    print("   Open this URL in your browser to use the chatbot\n")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
