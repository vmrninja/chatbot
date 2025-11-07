# Security Assessment Chatbot

A simple web-based chatbot that helps verify assessment questionnaire answers against security policies using Claude AI.

## Features

- 📤 **Document Upload**: Upload multiple security policies and assessment questionnaires
- 💬 **Interactive Chat**: Ask questions about compliance and policy verification
- 🤖 **AI-Powered Analysis**: Uses Claude API to analyze documents and provide insights
- 🎯 **Compliance Checking**: Identifies gaps, inconsistencies, and areas of concern

## Architecture

The application consists of two main components:

1. **Frontend (index.html)**: Simple HTML/CSS/JavaScript interface
   - Clean chat interface
   - File upload functionality
   - Real-time messaging

2. **Backend (app.py)**: Python Flask server
   - Handles file uploads and storage
   - Manages chat interactions
   - Integrates with Anthropic Claude API

## Prerequisites

- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation

1. **Clone or download the files** to a directory

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Anthropic API key**:
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```
   
   On Windows (Command Prompt):
   ```cmd
   set ANTHROPIC_API_KEY=your-api-key-here
   ```
   
   On Windows (PowerShell):
   ```powershell
   $env:ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

1. **Start the backend server**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Upload documents**:
   - Click "Upload Documents" button
   - Select security policies and assessment questionnaires
   - Supported formats: .txt, .pdf, .doc, .docx, .md

4. **Ask questions** such as:
   - "Does the answer to question 5 comply with our data encryption policy?"
   - "Are there any gaps between the assessment answers and our security requirements?"
   - "What are the key security concerns in the uploaded documents?"
   - "Compare the incident response procedures against industry standards"

## Project Structure

```
.
├── index.html          # Frontend web interface
├── app.py             # Backend Flask application
├── requirements.txt   # Python dependencies
├── uploads/          # Directory for uploaded files (created automatically)
└── README.md         # This file
```

## API Endpoints

### POST /upload
Upload a document file
- **Request**: multipart/form-data with 'file' field
- **Response**: `{"file_id": "uuid", "filename": "name", "message": "success"}`

### POST /chat
Send a chat message
- **Request**: `{"message": "your question", "file_ids": ["uuid1", "uuid2"]}`
- **Response**: `{"response": "Claude's answer"}`

### POST /clear
Clear all uploaded documents
- **Response**: `{"message": "All documents cleared"}`

## Configuration

You can modify these settings in `app.py`:

- `UPLOAD_FOLDER`: Directory for storing uploaded files (default: `./uploads`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: 10MB)
- `model`: Claude model to use (default: `claude-sonnet-4-20250514`)
- `max_tokens`: Maximum response length (default: 4096)

## Security Considerations

⚠️ **Important**: This is a development application. For production use:

1. Add authentication and authorization
2. Implement rate limiting
3. Add input validation and sanitization
4. Use HTTPS for API calls
5. Implement proper error handling
6. Add logging and monitoring
7. Secure file upload validation
8. Implement session management

## Troubleshooting

**API Key Error**:
- Ensure `ANTHROPIC_API_KEY` environment variable is set
- Verify the API key is valid

**File Upload Issues**:
- Check file size is under 10MB
- Ensure the file format is supported
- Verify write permissions for the uploads directory

**Connection Errors**:
- Ensure port 5000 is not in use
- Check firewall settings
- Verify CORS is enabled

## Example Use Cases

1. **Policy Compliance Review**:
   - Upload your organization's security policies
   - Upload completed assessment questionnaires
   - Ask: "Are all answers compliant with our policies?"

2. **Gap Analysis**:
   - Upload required security standards
   - Upload current implementation documentation
   - Ask: "What are the gaps in our security implementation?"

3. **Vendor Assessment**:
   - Upload vendor security questionnaire responses
   - Upload your security requirements
   - Ask: "Does this vendor meet our security requirements?"

## License

This is a sample application for educational and development purposes.

## Support

For issues with:
- **Claude API**: Visit [Anthropic Documentation](https://docs.anthropic.com/)
- **Flask**: Visit [Flask Documentation](https://flask.palletsprojects.com/)
