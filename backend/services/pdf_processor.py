from PyPDF2 import PdfReader
from typing import List, Dict
from io import BytesIO
import logging
logger = logging.getLogger(__name__)

class PDFProcessor:
    
    def extract_from_file_contents(self, file_data_list):
        """Extract text from file contents (for background processing)"""
        results = []
        
        for file_data in file_data_list:
            try:
                filename = file_data["filename"]
                content = file_data["content"]
                
                # Extract PDF text
                text = self._extract_pdf_from_bytes(content)
                
                results.append({
                    "filename": filename,
                    "text_content": text.strip(),
                    "extraction_success": len(text.strip()) > 0,
                    "text_length": len(text.strip())
                })
                
            except Exception as e:
                results.append({
                    "filename": file_data.get("filename", "unknown"),
                    "extraction_success": False,
                    "error": str(e),
                    "text_content": "",
                    "text_length": 0
                })
        
        return results
    
    def _extract_pdf_from_bytes(self, content: bytes) -> str:
        """Extract text from PDF bytes"""
        
        pdf_file = BytesIO(content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
