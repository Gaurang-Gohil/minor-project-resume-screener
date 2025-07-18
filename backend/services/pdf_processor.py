from PyPDF2 import PdfReader

class PDFProcessor:
    def extract_text(self, file_path: str) -> str:
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ""
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
        return text.strip()
