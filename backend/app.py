from flask import Blueprint, request, jsonify
from utils.parser import extract_text_from_pdf, extract_email, extract_skills

resume_bp = Blueprint('resume_bp', __name__)

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    file_path = f"uploads/{file.filename}"
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    email = extract_email(text)
    skills = extract_skills(text, ['python', 'aws', 'docker', 'terraform'])

    return jsonify({
        "email": email,
        "skills": skills
    })
