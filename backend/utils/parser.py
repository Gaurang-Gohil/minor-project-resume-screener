# utils/parser.py
import pdfplumber
import re

def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_email(text):
    match = re.findall(r'\S+@\S+', text)
    return match[0] if match else None

def extract_skills(text, skill_set):
    found = [skill for skill in skill_set if skill.lower() in text.lower()]
    return found
