#!/usr/bin/env python3
"""Script simple para comparar estructuras de PDF"""
import sys
import fitz

# Analizar original
print("Analizando original...")
with fitz.open("media/pdfs/2025/12/01/ArcPro_Part1.pdf") as pdf:
    page = pdf[0]
    page_dict = page.get_text("dict")
    
    orig_blocks = 0
    orig_lines = 0
    orig_spans = 0
    
    for block in page_dict.get("blocks", []):
        if block.get("type") == 0:
            orig_blocks += 1
            for line in block.get("lines", []):
                orig_lines += 1
                orig_spans += len(line.get("spans", []))
    
    print(f"Original: {orig_blocks} bloques, {orig_lines} lineas, {orig_spans} spans")

# Analizar traducido
print("Analizando traducido...")
with fitz.open("media/translated/2025/12/01/ArcPro_Part1_YCFcwP2_es.pdf") as pdf:
    page = pdf[0]
    page_dict = page.get_text("dict")
    
    trans_blocks = 0
    trans_lines = 0
    trans_spans = 0
    
    for block in page_dict.get("blocks", []):
        if block.get("type") == 0:
            trans_blocks += 1
            for line in block.get("lines", []):
                trans_lines += 1
                trans_spans += len(line.get("spans", []))
    
    print(f"Traducido: {trans_blocks} bloques, {trans_lines} lineas, {trans_spans} spans")

print(f"\nDiferencias:")
print(f"  Bloques: {trans_blocks - orig_blocks}")
print(f"  Lineas: {trans_lines - orig_lines}")
print(f"  Spans: {trans_spans - orig_spans}")
