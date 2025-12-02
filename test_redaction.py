#!/usr/bin/env python3
"""Test nuevo algoritmo con redaction"""
import sys
sys.path.insert(0, ".")

import argostranslate.package
import argostranslate.translate
import fitz
from translator.pdf_layout import replace_text_in_page

print("Cargando modelo...")
argostranslate.translate.load_installed_languages()
installed_languages = argostranslate.translate.get_installed_languages()

english = next((lang for lang in installed_languages if lang.code == "en"), None)
spanish = next((lang for lang in installed_languages if lang.code == "es"), None)

translator = english.get_translation(spanish)
print("OK")

print("Traduciendo con nuevo algoritmo (redaction)...")
with fitz.open("media/pdfs/2025/12/01/ArcPro_Part1.pdf") as source_pdf:
    translated_pdf = fitz.open()
    translated_pdf.insert_pdf(source_pdf)
    
    replace_text_in_page(
        source_pdf[0],
        translated_pdf[0],
        translator,
    )
    
    translated_pdf.save("test_redaction_output.pdf")
    translated_pdf.close()
    print("OK: Guardado en test_redaction_output.pdf")

print("\nComparando estructuras...")
with fitz.open("media/pdfs/2025/12/01/ArcPro_Part1.pdf") as pdf:
    page = pdf[0]
    page_dict = page.get_text("dict")
    orig_blocks = sum(1 for b in page_dict.get("blocks", []) if b.get("type") == 0)
    orig_lines = sum(len(b.get("lines", [])) for b in page_dict.get("blocks", []) if b.get("type") == 0)
    orig_spans = sum(len(s.get("spans", [])) for b in page_dict.get("blocks", []) if b.get("type") == 0 for s in b.get("lines", []))
    print(f"Original: {orig_blocks} bloques, {orig_lines} lineas, {orig_spans} spans")

with fitz.open("test_redaction_output.pdf") as pdf:
    page = pdf[0]
    page_dict = page.get_text("dict")
    trans_blocks = sum(1 for b in page_dict.get("blocks", []) if b.get("type") == 0)
    trans_lines = sum(len(b.get("lines", [])) for b in page_dict.get("blocks", []) if b.get("type") == 0)
    trans_spans = sum(len(s.get("spans", [])) for b in page_dict.get("blocks", []) if b.get("type") == 0 for s in b.get("lines", []))
    print(f"Traducido: {trans_blocks} bloques, {trans_lines} lineas, {trans_spans} spans")

print(f"\nDiferencias:")
print(f"  Bloques: {trans_blocks - orig_blocks}")
print(f"  Lineas: {trans_lines - orig_lines}")
print(f"  Spans: {trans_spans - orig_spans}")

if trans_blocks == orig_blocks and trans_lines == orig_lines and trans_spans == orig_spans:
    print("\n✓ ESTRUCTURA PERFECTAMENTE PRESERVADA!")
else:
    print("\n✗ Estructura modificada, necesita ajustes")
