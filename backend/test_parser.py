# test_parser.py
from utils.parser import extract_text_from_pdf, extract_email, extract_skills

def main():
    # Path to your sample PDF
    pdf_path = "sample_resume.pdf"
    
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    print("\nExtracted text (first 500 characters):")
    print(text[:500] if text else "No text extracted")
    
    print("\nExtracting email...")
    email = extract_email(text)
    print(f"Email found: {email}")
    
    print("\nExtracting skills...")
    skill_set = ['python', 'aws', 'docker', 'terraform', 'javascript', 'react', 'node', 'java', 'sql']
    skills = extract_skills(text, skill_set)
    print(f"Skills found: {skills}")

if __name__ == "__main__":
    main()