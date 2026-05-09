"""
tts_utils.py — NEW FILE
Converts text responses from OpenAI into audio using Google TTS (gTTS).
Returns audio as BytesIO so Streamlit can play it directly.
"""

import io
import re
from gtts import gTTS


def clean_text_for_tts(text: str) -> str:
    """
    Strip markdown and special characters that gTTS would read out loud.
    Examples of what gets removed:
      ### Heading     → Heading
      **bold**        → bold
      - bullet        → bullet
      `code`          → code
      [link](url)     → link
      1. item         → item
    """
    # Remove markdown headings (###, ##, #)
    text = re.sub(r"#{1,6}\s*", "", text)

    # Remove bold/italic markers (**, *, __, _)
    text = re.sub(r"\*{1,2}|_{1,2}", "", text)

    # Remove inline code backticks
    text = re.sub(r"`{1,3}", "", text)

    # Remove markdown links — keep display text, drop URL
    # [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Remove bullet/list markers (-, *, •, numbered lists)
    text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove horizontal rules (---, ___, ***)
    text = re.sub(r"^[-_*]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove HTML tags if any
    text = re.sub(r"<[^>]+>", "", text)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leftover special chars that TTS reads awkwardly
    # Keep: letters, digits, spaces, basic punctuation (.,!?;:'"-)
    text = re.sub(r"[^\w\s\.,!?;:'\"()\-\nàáảãạăắặẳẵâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def text_to_speech_bytes(text: str, lang: str = "en") -> io.BytesIO:
    """
    PUBLIC — Converts a text string into MP3 audio bytes.
    Automatically cleans markdown/special chars before passing to gTTS.
    """
    # Clean text before sending to gTTS
    cleaned = clean_text_for_tts(text)

    # Fallback if cleaning produces empty string
    if not cleaned.strip():
        cleaned = "No content to read."

    tts = gTTS(text=cleaned, lang=lang, slow=False)

    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer


def detect_lang(text: str) -> str:
    """
    Simple heuristic to detect Vietnamese vs English for gTTS lang param.
    Checks for common Vietnamese diacritic characters.
    Returns "vi" if Vietnamese detected, else "en".
    """
    vietnamese_chars = set("àáảãạăắặẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ")
    text_lower = text.lower()
    vi_count = sum(1 for c in text_lower if c in vietnamese_chars)
    return "vi" if vi_count > 5 else "en"