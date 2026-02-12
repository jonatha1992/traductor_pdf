from typing import Callable, Optional, List, Dict
import fitz  # PyMuPDF
import re

_translation_cache = {}


class TranslationCanceled(Exception):
    """Raised when the user cancels an in-flight translation."""


def _translate_with_cache(text: str, translator) -> str:
    global _translation_cache
    text_stripped = text.strip()
    
    # Skip empty, numbers-only, or dots-only text
    if not text_stripped:
        return text
    if re.match(r'^[\d\.\s]+$', text_stripped):
        return text
    
    if text_stripped in _translation_cache:
        cached = _translation_cache[text_stripped]
        # Preserve original whitespace
        if text.startswith(' '):
            cached = ' ' + cached.lstrip()
        if text.endswith(' '):
            cached = cached.rstrip() + ' '
        return cached
    
    try:
        translated = translator.translate(text_stripped)
        if translated:
            _translation_cache[text_stripped] = translated.strip()
            # Preserve whitespace
            if text.startswith(' '):
                translated = ' ' + translated.lstrip()
            if text.endswith(' '):
                translated = translated.rstrip() + ' '
            return translated
        return text
    except Exception:
        return text


def _get_font_name(original_font: str) -> str:
    font = original_font.lower()
    if 'bold' in font:
        return 'hebo'
    elif 'italic' in font:
        return 'heit'
    else:
        return 'helv'


def _color_to_rgb(color) -> tuple:
    if isinstance(color, int):
        r = ((color >> 16) & 0xFF) / 255.0
        g = ((color >> 8) & 0xFF) / 255.0
        b = (color & 0xFF) / 255.0
        return (r, g, b)
    elif hasattr(color, '__iter__') and len(color) >= 3:
        return tuple(color)[:3]
    return (0, 0, 0)


def replace_text_in_page(
    source_page: fitz.Page, 
    target_page: fitz.Page, 
    translator,
    cancel_callback: Optional[Callable[[], bool]] = None
) -> None:
    """
    Simple and consistent text replacement.
    - Groups contiguous text spans
    - Translates them
    - Inserts with ORIGINAL font size (no scaling)
    """
    page_dict = source_page.get_text("dict")
    
    redaction_rects = []
    insertions = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        
        for line in block.get("lines", []):
            if cancel_callback and cancel_callback():
                raise TranslationCanceled("Translation canceled by user")
            
            spans = line.get("spans", [])
            if not spans:
                continue
            
            # Group spans by proximity
            groups = []
            current_group = []
            
            for span in spans:
                text = span['text']
                
                if not current_group:
                    current_group.append(span)
                    continue
                
                prev = current_group[-1]
                gap = span['bbox'][0] - prev['bbox'][2]
                
                # Check if this is a separator (dots or numbers only)
                is_sep = bool(re.match(r'^[\d\.]+$', text.strip()))
                prev_is_sep = bool(re.match(r'^[\d\.]+$', prev['text'].strip()))
                
                # Split if large gap OR transitioning to/from separator
                if gap > (prev['size'] * 0.5) or (is_sep != prev_is_sep):
                    groups.append(current_group)
                    current_group = [span]
                else:
                    current_group.append(span)
            
            if current_group:
                groups.append(current_group)
            
            # Process each group
            for group in groups:
                # Calculate bounding box
                rect = fitz.Rect(group[0]['bbox'])
                text = ""
                for s in group:
                    rect |= fitz.Rect(s['bbox'])
                    text += s['text']
                
                # Skip if only numbers/dots
                if re.match(r'^[\d\.\s]+$', text):
                    continue
                
                # Translate
                translated = _translate_with_cache(text, translator)
                if not translated or not translated.strip():
                    continue
                
                # Store for later
                first = group[0]
                redaction_rects.append(rect)
                insertions.append({
                    'rect': rect,
                    'text': translated,
                    'fontname': _get_font_name(first['font']),
                    'fontsize': first['size'],  # USE ORIGINAL SIZE ALWAYS
                    'color': _color_to_rgb(first['color']),
                })

    # 1. Redact original text
    for rect in redaction_rects:
        target_page.add_redact_annot(rect, text="", fill=(1, 1, 1))
    target_page.apply_redactions()
    
    # 2. Insert translated text with ORIGINAL sizing
    for ins in insertions:
        try:
            # Position at original location
            # Use y1 (bottom of bbox) as baseline reference
            x = ins['rect'].x0
            y = ins['rect'].y1 - (ins['fontsize'] * 0.15)  # Slight baseline adjustment
            
            target_page.insert_text(
                fitz.Point(x, y),
                ins['text'],
                fontname=ins['fontname'],
                fontsize=ins['fontsize'],
                color=ins['color']
            )
        except Exception:
            pass


def translate_pdf_document(
    input_path: str,
    translator,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    cancel_callback: Optional[Callable[[], bool]] = None,
) -> tuple[fitz.Document, int]:
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
            translated_pdf.new_page()
        
        return translated_pdf, total_pages
