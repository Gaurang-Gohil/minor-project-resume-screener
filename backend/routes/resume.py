from flask import Blueprint, request, jsonify
import os
from utils.parser import extract_text_from_pdf, extract_email, extract_skills

resume_bp = Blueprint('resume_bp', __name__)

# Create uploads directory if it doesn't exist
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    file_path = os.path.join(uploads_dir, file.filename)
    file.save(file_path)

    try:
        text = extract_text_from_pdf(file_path)
        email = extract_email(text)
        skills = extract_skills(text, ['python', 'aws', 'docker', 'terraform', 'javascript', 'react', 'node'])

        return jsonify({
            "message": f"{file.filename} processed successfully",
            "email": email,
            "skills": skills
        })
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
