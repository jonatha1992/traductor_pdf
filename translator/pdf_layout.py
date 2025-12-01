from typing import Callable, Optional

import fitz  # PyMuPDF

MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 48
FONT_NAME = "helv"
MAX_ATTEMPTS = 5


class TranslationCanceled(Exception):
    """Raised when the user cancels an in-flight translation."""


def _collect_block_text(block: dict) -> str:
    """Build a string that preserves line breaks for a pdf text block."""

    lines = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        text = "".join(span.get("text", "") for span in spans).strip()
        lines.append(text)

    # Remove trailing blank lines but keep intentional empty lines inside the block.
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines).strip()


def _estimate_font_size(block: dict, rect: fitz.Rect, translated_text: str) -> float:
    """Estimate a font size that keeps the text inside the block rectangle."""

    span_sizes = [
        span.get("size")
        for line in block.get("lines", [])
        for span in line.get("spans", [])
        if span.get("size")
    ]
    average_size = sum(span_sizes) / len(span_sizes) if span_sizes else 11

    line_count = max(1, translated_text.count("\n") + 1)
    height_based = (rect.height / line_count) * 0.9 if rect.height else average_size

    return max(
        MIN_FONT_SIZE,
        min(MAX_FONT_SIZE, min(average_size * 1.15, height_based)),
    )


def _clear_rect(page: fitz.Page, rect: fitz.Rect) -> None:
    """Paint a white rectangle to hide the original text before placing the translation."""

    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(fill=(1, 1, 1), color=(1, 1, 1))
    shape.commit()


def _write_block_text(page: fitz.Page, rect: fitz.Rect, text: str, font_size: float) -> None:
    """Write translated text inside the provided rectangle, shrinking when necessary."""

    if not text.strip() or rect.width <= 0 or rect.height <= 0:
        return

    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized_text:
        return

    size = font_size
    for _ in range(MAX_ATTEMPTS):
        _clear_rect(page, rect)
        result = page.insert_textbox(
            rect,
            normalized_text,
            fontsize=size,
            fontname=FONT_NAME,
            color=(0, 0, 0),
        )
        fits = False
        if isinstance(result, str):
            fits = not result.strip()
        else:
            fits = result == 0
        if fits:
            return
        size = max(MIN_FONT_SIZE, size * 0.85)

    # If some text still does not fit, write the remainder at the minimum size.
    _clear_rect(page, rect)
    page.insert_textbox(
        rect,
        normalized_text,
        fontsize=MIN_FONT_SIZE,
        fontname=FONT_NAME,
        color=(0, 0, 0),
    )


def replace_text_in_page(source_page: fitz.Page, target_page: fitz.Page, translator) -> None:
    """Translate every text block in the source page and paint it on the target page."""

    page_dict = source_page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        text = _collect_block_text(block)
        if not text:
            continue

        translated_text = translator.translate(text)
        rect = fitz.Rect(block["bbox"])
        font_size = _estimate_font_size(block, rect, translated_text)
        _write_block_text(target_page, rect, translated_text, font_size)


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
            )

            if progress_callback:
                progress_callback(page_number + 1, total_pages)

        if total_pages == 0:
            # Ensure the exported PDF has at least one blank page to keep readers happy.
            translated_pdf.new_page(width=595, height=842)

        return translated_pdf, total_pages
