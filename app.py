"""
Security Assessment Chatbot Backend
Handles document uploads and chat interactions with Claude API
"""

from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import os
import uuid
from anthropic import Anthropic
from pathlib import Path
import mimetypes
from dotenv import load_dotenv
import json

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path('./uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Load environment variables from .env file if present
load_dotenv()

# Initialize Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables or .env file")
client = Anthropic(api_key=api_key)


# Helper functions
def add_user_messages(messages, text):
    input_message = {"role": "user", "content": text}
    messages.append(input_message)

def add_assistant_messages(messages, text):
    input_message = {"role": "assistant", "content": text}
    messages.append(input_message)

# Storage for uploaded documents
documents = {}

# Handling file upload and use of its content for context
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
    
    print(f"Uploaded file: {file.filename} (ID: {file_id}, Size: {os.path.getsize(file_path)} bytes), File content: {content[:100]}...")  # Print first 100 chars of content

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
    """Handle chat messages and stream Claude's response."""
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
        add_user_messages(messages, context)
        add_assistant_messages(messages, "I have received the uploaded documents. How can I help you analyze them?")
    
    # Add the actual user question
    add_user_messages(messages, user_message)
    
    formatted_json = json.dumps(messages, indent=4)

    # Set headers for streaming response
    response = Response(stream_with_context(stream_response(messages, system_prompt)), 
                       mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

def stream_response(messages, system_prompt):
    """Stream the response from Claude API"""
    try:
        response_text = ""
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            messages=messages,
            max_tokens=4096,
            system=system_prompt
        ) as stream:
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    if hasattr(chunk.delta, 'text'):
                        text_chunk = chunk.delta.text
                        response_text += text_chunk
                        # Send each chunk as a server-sent event
                        yield f"data: {json.dumps({'response': text_chunk, 'done': False})}\n\n"
                
                elif chunk.type == "content_block_stop":
                    # Send final message indicating completion
                    yield f"data: {json.dumps({'response': '', 'done': True})}\n\n"
                    break
            
            # Add the complete response to messages history
            add_assistant_messages(messages, response_text)
    
    except Exception as e:
        error_response = json.dumps({'error': f'Error calling Claude API: {str(e)}'})
        yield f"data: {error_response}\n\n"
    data = request.json
    user_message = data.get('message', '')
    file_ids = data.get('file_ids', [])
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    

# Delete all uploaded documents
@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_document(file_id):
    """Delete a specific document."""
    global documents
    
    if file_id not in documents:
        return jsonify({
            'error': 'File not found'
        }), 404
    
    try:
        # Get the file path and delete it
        file_path = documents[file_id]['path']
        os.remove(file_path)
        
        # Remove from documents dictionary
        del documents[file_id]
        
        return jsonify({
            'message': f'File deleted successfully',
            'file_id': file_id,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error deleting file: {str(e)}',
            'success': False
        }), 500

@app.route('/clear', methods=['POST'])
def clear_documents():
    """Clear all uploaded documents."""
    global documents
    
    try:
        # Count files before deletion
        file_count = len(documents)
        
        # Delete files
        failed_deletions = 0
        for doc in documents.values():
            try:
                os.remove(doc['path'])
            except Exception as e:
                print(f"Failed to delete file {doc['path']}: {str(e)}")
                failed_deletions += 1
        
        # Clear the documents dictionary
        documents.clear()
        
        return jsonify({
            'message': f'Cleared {file_count} documents',
            'failed_deletions': failed_deletions,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error clearing documents: {str(e)}',
            'success': False
        }), 500


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
