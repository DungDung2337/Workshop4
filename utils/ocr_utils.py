"""
Handles OCR extraction from:
  - Images (JPG, PNG) using EasyOCR (optional — disabled on cloud if unavailable)
  - PDFs using pdfplumber (text-based) with EasyOCR fallback (scanned only)
"""

import io
import ssl
import pdfplumber
import numpy as np
from PIL import Image

# EasyOCR is optional — requires torch (~1.5GB), may not be available on cloud
try:
    import easyocr
    ssl._create_default_https_context = ssl._create_unverified_context
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

_reader = None


def _get_reader():
    global _reader
    if not EASYOCR_AVAILABLE:
        return None
    if _reader is None:
        _reader = easyocr.Reader(["en", "vi"], gpu=False)
    return _reader


def extract_text_from_image(file_bytes: bytes) -> str:
    if not EASYOCR_AVAILABLE:
        return "[OCR unavailable: easyocr is not installed in this environment. Upload a .txt file instead.]"

    reader = _get_reader()
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image_np = np.array(image)
    results = reader.readtext(image_np, detail=0)
    extracted = "\n".join(results)
    return extracted.strip() if extracted else "[OCR: No text detected in image]"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    extracted_pages = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text and text.strip():
                extracted_pages.append(text.strip())
            else:
                # Scanned page — fall back to EasyOCR if available
                if not EASYOCR_AVAILABLE:
                    extracted_pages.append(
                        f"[Page {page.page_number}: scanned PDF — OCR unavailable in this environment]"
                    )
                    continue

                page_image = page.to_image(resolution=200).original
                image_np = np.array(page_image.convert("RGB"))
                reader = _get_reader()
                results = reader.readtext(image_np, detail=0)
                ocr_text = "\n".join(results)
                extracted_pages.append(
                    ocr_text.strip() if ocr_text.strip()
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
