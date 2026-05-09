"""
Handles OCR extraction from:
  - Images (JPG, PNG) using pytesseract (primary, lightweight, no PyTorch)
  - PDFs using pdfplumber (text-based) with pytesseract fallback (scanned pages)
  - EasyOCR kept as optional local fallback if pytesseract unavailable
"""

import io
import pdfplumber
from PIL import Image

# pytesseract — primary OCR engine (requires tesseract-ocr system package)
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

# EasyOCR — optional local-only fallback (requires torch ~1.5GB, not on cloud)
try:
    import ssl
    import numpy as np
    import easyocr
    ssl._create_default_https_context = ssl._create_unverified_context
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

_easyocr_reader = None


def _get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        _easyocr_reader = easyocr.Reader(["en", "vi"], gpu=False)
    return _easyocr_reader


def _ocr_image(image: Image.Image) -> str:
    """Run OCR on a PIL Image. Tries pytesseract first, falls back to EasyOCR."""
    image = image.convert("RGB")

    if TESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(image, lang="eng+vie")
            if text.strip():
                return text.strip()
        except Exception:
            pass

    if EASYOCR_AVAILABLE:
        reader = _get_easyocr_reader()
        results = reader.readtext(np.array(image), detail=0)
        return "\n".join(results).strip()

    return "[OCR unavailable: install tesseract-ocr or easyocr to process images]"


def extract_text_from_image(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    result = _ocr_image(image)
    return result if result else "[OCR: No text detected in image]"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    extracted_pages = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                extracted_pages.append(text.strip())
            else:
                # Scanned page — OCR fallback
                page_image = page.to_image(resolution=200).original
                ocr_text = _ocr_image(page_image)
                extracted_pages.append(
                    ocr_text if ocr_text
                    else f"[OCR: Page {page.page_number} — no text detected]"
                )

    full_text = "\n\n".join(extracted_pages)
    return full_text.strip() if full_text else "[OCR: No text found in PDF]"


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("jpg", "jpeg", "png"):
        return extract_text_from_image(file_bytes)
    else:
        return f"[OCR: Unsupported file format '.{ext}']"
