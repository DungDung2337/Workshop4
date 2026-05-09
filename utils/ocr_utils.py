"""
Handles OCR extraction from:
  - Images (JPG, PNG) using EasyOCR
  - PDFs using pdfplumber (text-based) with EasyOCR fallback (scanned)
"""

import io
import ssl
import pdfplumber
import easyocr
import numpy as np
from PIL import Image

# ------------------------------------------------------------------ #
#  SSL FIX for macOS — Python on macOS does not use system certs,    #
#  causing URLError when EasyOCR tries to download models.           #
#  This patches the default SSL context to skip verification         #
#  ONLY for the model download step (safe for local dev use).        #
# ------------------------------------------------------------------ #
ssl._create_default_https_context = ssl._create_unverified_context

# ------------------------------------------------------------------ #
#  EasyOCR reader — initialized once to avoid reloading the model     #
#  lang list: ["en"] for English-only; add "vi" for Vietnamese        #
# ------------------------------------------------------------------ #
_reader = None  # lazy-loaded on first use

def _get_reader():
    """Lazy-load EasyOCR reader (downloads model on first call)."""
    global _reader
    if _reader is None:
        # gpu=False ensures it works on CPU-only machines
        _reader = easyocr.Reader(["en", "vi"], gpu=False)
    return _reader


# ------------------------------------------------------------------ #
#  PUBLIC FUNCTION 1 — Extract text from an image file               #
# ------------------------------------------------------------------ #
def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Accepts raw image bytes (JPG/PNG) and returns extracted text string.
    Uses EasyOCR for AI-based text recognition.
    """
    reader = _get_reader()

    # Convert bytes → numpy array for EasyOCR
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    image_np = np.array(image)

    # detail=0 returns plain text list (no bounding boxes)
    results = reader.readtext(image_np, detail=0)

    # Join all detected text lines into one string
    extracted = "\n".join(results)
    return extracted.strip() if extracted else "[OCR: No text detected in image]"


# ------------------------------------------------------------------ #
#  PUBLIC FUNCTION 2 — Extract text from a PDF file                  #
# ------------------------------------------------------------------ #
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Accepts raw PDF bytes and returns extracted text string.
    Strategy:
      1. Try pdfplumber (fast, works on text-based PDFs)
      2. If no text found → fall back to EasyOCR page-by-page (scanned PDFs)
    """
    extracted_pages = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Attempt 1: native text extraction
            text = page.extract_text()

            if text and text.strip():
                # Text-based page — use pdfplumber result directly
                extracted_pages.append(text.strip())
            else:
                # Attempt 2: scanned page — render to image then OCR
                page_image = page.to_image(resolution=200).original
                image_np = np.array(page_image.convert("RGB"))

                reader = _get_reader()
                results = reader.readtext(image_np, detail=0)
                ocr_text = "\n".join(results)

                if ocr_text.strip():
                    extracted_pages.append(ocr_text.strip())
                else:
                    extracted_pages.append(f"[OCR: Page {page.page_number} — no text detected]")

    full_text = "\n\n".join(extracted_pages)
    return full_text.strip() if full_text else "[OCR: No text found in PDF]"


# ------------------------------------------------------------------ #
#  PUBLIC FUNCTION 3 — Smart router (detects file type automatically) #
# ------------------------------------------------------------------ #
def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Routes to the correct extractor based on file extension.
    Supports: .pdf, .jpg, .jpeg, .png
    Returns extracted text as a plain string.
    """
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("jpg", "jpeg", "png"):
        return extract_text_from_image(file_bytes)
    else:
        # Unsupported format — return empty so caller can handle gracefully
        return f"[OCR: Unsupported file format '.{ext}']"