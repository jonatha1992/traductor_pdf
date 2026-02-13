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

    def _map_font_name(original: str) -> str:
        """Map extracted font names to PDF base14 or close equivalents.
        Prioritize uniformity: mostly Helvetica, Courier for code.
        """
        if not original:
            return "helv"
        f = original.lower().replace('-', '').replace(' ', '').replace('_', '')
        
        # Keep Courier / Mono for code blocks
        if 'courier' in f or 'mono' in f or 'console' in f:
            if 'bold' in f:
                return 'cour-b'
            return 'cour'
            
        # For everything else, use Helvetica to ensure uniformity
        # This fixes the "messy fonts" issue by standardizing the look
        if 'bold' in f and 'italic' in f:
            return 'helv-bi'
        if 'bold' in f:
            return 'helv-b'
        if 'italic' in f:
            return 'helv-i'
        return 'helv'

    def _fit_font_size_for_width(text: str, fontname: str, size: float, width: float, fallback_avg_width: float) -> float:
        """Shrink font size if needed to make translated text fit bbox width.
        Uses fitz.get_text_length when available, otherwise a simple estimate.
        """
        s = max(1.0, float(size) or 1.0)
        try:
            w = fitz.get_text_length(text, fontname=fontname, fontsize=s)  # type: ignore[attr-defined]
            if w <= 0:
                raise ValueError
        except Exception:
            # Fallback: estimate width by average glyph width
            avg = max(0.5, fallback_avg_width)
            w = avg * max(1, len(text))
        if w <= width:
            return s
        # scale down but not more than 60% of original (allowed slightly more shrinkage)
        scale = max(0.6, min(1.0, (width - 0.5) / w))
        return s * scale
    
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
                # Multiple spans: distribute translated words across original spans
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

    # Now apply all replacements using redaction (remove original glyphs without painting white boxes)
    for repl in replacements:
        # Add redaction annotation – no fill to avoid covering images/backgrounds
        try:
            target_page.add_redact_annot(repl['bbox'], text="", fill=None)
        except TypeError:
            # Older PyMuPDF may not accept None -> fall back to very low alpha white
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

        source_font = str(repl.get('font', 'helv')) or 'helv'
        mapped_font = _map_font_name(source_font)

        # Fit font size to span width, if needed
        bbox: fitz.Rect = repl['bbox']
        span_width = max(1.0, bbox.width)
        old_text = repl.get('old_text', '') or ''
        avg_width = span_width / max(1, len(old_text)) if old_text else span_width / max(1, len(repl['new_text']))
        orig_size = float(repl.get('size', 11.0))
        
        # Scale down the original font size to create more "padding" and ensure it's smaller
        # using 0.85 (15% smaller) as requested to "achicar la fuente" and "el padding"
        target_size = orig_size * 0.85
        
        fitted_size = _fit_font_size_for_width(repl['new_text'], mapped_font, target_size, span_width, avg_width)
        
        # Allow shrinking down to 50% of original (was 60%) to ensure it fits better
        # Also lowered absolute minimum from 6.0 to 5.0
        min_allowed = max(5.0, max(0.5 * orig_size, fitted_size * 0.9))

        inserted = False
        font_candidates = []
        # Prioritize the mapped font (usually helv), then fallback to helv
        for candidate in (mapped_font, "helv"):
            if candidate and candidate not in font_candidates:
                font_candidates.append(candidate)

        for font_choice in font_candidates:
            size_try = fitted_size
            # Try 6 decrements
            for _ in range(6):
                try:
                    # insert_textbox returns < 0 if text doesn't fit
                    leftover = target_page.insert_textbox(
                        bbox,
                        repl['new_text'],
                        fontsize=size_try,
                        fontname=font_choice,
                        color=rgb_color,
                        align=0,  # left align to mimic original spans
                    )
                except Exception:
                    break
                
                # If leftover is empty or 0 (or whatever indicates success), it fit successfully
                # PyMuPDF insert_textbox returns < 0 if text did not fit.
                if leftover >= 0:
                    inserted = True
                    break
                
                # Reduce size and try again
                size_try = max(min_allowed, size_try * 0.9)
                if size_try <= min_allowed and size_try < fitted_size:
                     break
            
            if inserted:
                break

        if not inserted:
            # If it still doesn't fit, we force it in with the smallest allowed size
            # But we use insert_textbox which handles wrapping, instead of insert_text which overflows
            try:
                target_page.insert_textbox(
                    bbox,
                    repl['new_text'],
                    fontsize=min_allowed,
                    fontname="helv",
                    color=rgb_color,
                    align=0,
                )
            except Exception:
                pass


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



