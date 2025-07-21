from PyPDF2 import PdfReader
from typing import List, Dict
from io import BytesIO
import logging
logger = logging.getLogger(__name__)


class PDFProcessor:

    def extract_text(self, file_path: str) -> str:
        """Extract text from a single PDF file path"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Failed to extract text: {str(e)}")

    def extract_from_upload_files(self, upload_files) -> List[Dict]:
        """Extract text from UploadFile objects (e.g., from FastAPI)"""
        results = []

        for file in upload_files:
            try:
                logger.info(f"Processing: {file.filename}")

                content = file.file.read()
                file.file.seek(0)

                if not content:
                    raise ValueError("File is empty")

                reader = PdfReader(BytesIO(content))
                text = ""

                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted

                if not text.strip():
                    raise ValueError("No extractable text found")

                results.append({
                    "filename": file.filename,
                    "text_content": text.strip(),
                    "extraction_success": True,
                    "text_length": len(text.strip())
                })

            except Exception as e:
                print(f"Error processing {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "text_content": "",
                    "extraction_success": False,
                    "error": str(e),
                    "text_length": 0
                })

        return results

    def extract_from_memory(self, file_data_list: List[Dict]) -> List[Dict]:
        """Extract text from in-memory file content (used in background tasks)"""
        results = []

        for file_data in file_data_list:
            try:
                reader = PdfReader(BytesIO(file_data["content"]))
                text = "".join(page.extract_text() or "" for page in reader.pages)

                results.append({
                    "filename": file_data["filename"],
                    "text_content": text.strip(),
                    "extraction_success": True,
                    "text_length": len(text.strip())
                })

            except Exception as e:
                results.append({
                    "filename": file_data["filename"],
                    "text_content": "",
                    "extraction_success": False,
                    "error": str(e),
                    "text_length": 0
                })

        return results

