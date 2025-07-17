from flask import Flask
from routes.resume import resume_bp

# Just test the imports
print("Imports successful!")
print(f"Blueprint name: {resume_bp.name}")