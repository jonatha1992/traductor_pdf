from typing import Callable, Optional

import fitz  # PyMuPDF

# Translation cache to avoid re-translating the same text
_translation_cache = {}


class TranslationCanceled(Exception):
    """Raised when the user cancels an in-flight translation."""


def _translate_with_cache(text: str, translator) -> str:
    """Translate text using cache to avoid redundant translations."""
    global _translation_cache
    
    # Use cache for common words/phrases
    if text in _translation_cache:
        return _translation_cache[text]
    
    try:
        translated = translator.translate(text)
        # Only cache if translation succeeded and cache isn't too large
        if len(_translation_cache) < 10000:  # Limit cache size
            _translation_cache[text] = translated
        return translated
    except Exception:
        return text  # Return original on error


def replace_text_in_page(
    source_page: fitz.Page, 
    target_page: fitz.Page, 
    translator,
    cancel_callback: Optional[Callable[[], bool]] = None
) -> None:
    """
    Translate text preserving EXACT PDF structure using redaction API.
    This approach modifies text in-place without creating new spans.
    """
    page_dict = source_page.get_text("dict")
    
    # Collect all text replacements first
    replacements = []
    
    for block in page_dict.get("blocks", []):
        # Skip non-text blocks (images, etc.)
        if block.get("type") != 0:
            continue
        
        for line in block.get("lines", []):
            # Check for cancellation
            if cancel_callback and cancel_callback():
                raise TranslationCanceled("Translation canceled by user")
            
            # Collect all text from spans in this line
            line_text = ""
            for span in line.get("spans", []):
                text = span.get("text", "")
                line_text += text
            
            line_text = line_text.strip()
            if not line_text:
                continue
            
            # Translate the entire line
            translated_text = _translate_with_cache(line_text, translator)
            
            # For each span in the line, we need to replace its text
            # We'll distribute the translated text across spans proportionally
            spans = line.get("spans", [])
            if not spans:
                continue
            
            # If single span, simple replacement
            if len(spans) == 1:
                span = spans[0]
                bbox = fitz.Rect(span["bbox"])
                replacements.append({
                    'bbox': bbox,
                    'old_text': span.get("text", ""),
                    'new_text': translated_text,
                    'font': span.get("font", "helv"),
                    'size': span.get("size", 11.0),
                    'color': span.get("color", 0),
                })
            else:
                # Multiple spans: distribute translated words
                original_texts = [span.get("text", "") for span in spans]
                total_original_length = sum(len(t) for t in original_texts)
                
                if total_original_length == 0:
                    continue
                
                translated_words = translated_text.split()
                current_word_idx = 0
                
                for i, span in enumerate(spans):
                    if current_word_idx >= len(translated_words):
                        break
                    
                    # Calculate how many words this span should get
                    original_proportion = len(original_texts[i]) / total_original_length
                    words_for_span = max(1, int(len(translated_words) * original_proportion))
                    
                    # Adjust for last span to get remaining words
                    if i == len(spans) - 1:
                        words_for_span = len(translated_words) - current_word_idx
                    
                    # Get words for this span
                    span_words = translated_words[current_word_idx:current_word_idx + words_for_span]
                    span_text = " ".join(span_words)
                    
                    bbox = fitz.Rect(span["bbox"])
                    replacements.append({
                        'bbox': bbox,
                        'old_text': span.get("text", ""),
                        'new_text': span_text,
                        'font': span.get("font", "helv"),
                        'size': span.get("size", 11.0),
                        'color': span.get("color", 0),
                    })
                    
                    current_word_idx += words_for_span
    
    # Now apply all replacements using redaction
    for repl in replacements:
        # Add redaction annotation
        target_page.add_redact_annot(repl['bbox'], text="", fill=(1, 1, 1))
    
    # Apply all redactions (this removes the old text)
    target_page.apply_redactions()
    
    # Now insert the new text at the original positions
    for repl in replacements:
        if not repl['new_text'].strip():
            continue
        
        # Convert color
        color = repl['color']
        if isinstance(color, int):
            r = ((color >> 16) & 0xFF) / 255.0
            g = ((color >> 8) & 0xFF) / 255.0
            b = (color & 0xFF) / 255.0
            rgb_color = (r, g, b)
        else:
            rgb_color = color
        
        # Map font
        font = repl['font'].lower().replace('-', '').replace(' ', '').replace('_', '')
        if 'times' in font or 'serif' in font:
            if 'bold' in font and 'italic' in font:
                mapped_font = 'times-bi'
            elif 'bold' in font:
                mapped_font = 'times-b'
            elif 'italic' in font:
                mapped_font = 'times-i'
            else:
                mapped_font = 'times'
        elif 'courier' in font or 'mono' in font:
            if 'bold' in font:
                mapped_font = 'cour-b'
            else:
                mapped_font = 'cour'
        else:
            if 'bold' in font and 'italic' in font:
                mapped_font = 'helv-bi'
            elif 'bold' in font:
                mapped_font = 'helv-b'
            elif 'italic' in font:
                mapped_font = 'helv-i'
            else:
                mapped_font = 'helv'
        
        # Insert text at top-left of bbox
        origin = fitz.Point(repl['bbox'].x0, repl['bbox'].y0 + repl['size'])
        
        try:
            target_page.insert_text(
                origin,
                repl['new_text'],
                fontsize=repl['size'],
                fontname=mapped_font,
                color=rgb_color,
            )
        except:
            # Fallback to basic font
            try:
                target_page.insert_text(
                    origin,
                    repl['new_text'],
                    fontsize=repl['size'],
                    fontname="helv",
                    color=(0, 0, 0),
                )
            except:
                pass  # Give up on this replacement


def translate_pdf_document(
    input_path: str,
    translator,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_callback: Optional[Callable[[], bool]] = None,
) -> tuple[fitz.Document, int]:
    """
    Translate a PDF file keeping the original layout.

    Returns the translated PyMuPDF document and the total number of processed pages.
    """

    with fitz.open(input_path) as source_pdf:
        total_pages = source_pdf.page_count
        translated_pdf = fitz.open()
        translated_pdf.insert_pdf(source_pdf)

        for page_number in range(total_pages):
            if cancel_callback and cancel_callback():
                translated_pdf.close()
                raise TranslationCanceled("Traducción cancelada por el usuario.")

            replace_text_in_page(
                source_pdf[page_number],
                translated_pdf[page_number],
                translator,
                cancel_callback=cancel_callback,
            )

            if progress_callback:
                progress_callback(page_number + 1, total_pages)

        if total_pages == 0:
            # Ensure the exported PDF has at least one blank page to keep readers happy.
            translated_pdf.new_page(width=595, height=842)

        return translated_pdf, total_pages



