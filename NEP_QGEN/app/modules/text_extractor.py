import PyPDF2
from PIL import Image
import pytesseract
import os
from typing import Optional


class TextExtractor:
    def __init__(self):
        pass

    def extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"

    def extract_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            return f"Error extracting from image: {str(e)}"

    def extract_from_text(self, file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            try:
                with open(file_path, 'r', encoding='latin1') as file:
                    return file.read().strip()
            except Exception as e2:
                return f"Error reading text file: {str(e2)}"
