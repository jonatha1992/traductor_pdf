#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba automatizado para comparar PDFs y ajustar el algoritmo.
Analiza diferencias entre original y traducido.
"""

import sys
import os
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argostranslate.package
import argostranslate.translate
import fitz
from translator.pdf_layout import replace_text_in_page

def analyze_page_structure(pdf_path, page_num=0):
    """Analiza la estructura detallada de una página."""
    with fitz.open(pdf_path) as pdf:
        page = pdf[page_num]
        page_dict = page.get_text("dict")
        
        print(f"\n{'='*80}")
        print(f"ANALISIS: {os.path.basename(pdf_path)} - Pagina {page_num + 1}")
        print(f"{'='*80}")
        
        block_count = 0
        line_count = 0
        span_count = 0
        font_sizes = []
        
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # Skip non-text blocks
                continue
            
            block_count += 1
            
            for line in block.get("lines", []):
                line_count += 1
                
                for span in line.get("spans", []):
                    span_count += 1
                    size = span.get("size", 0)
                    font_sizes.append(size)
        
        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0
        min_font_size = min(font_sizes) if font_sizes else 0
        max_font_size = max(font_sizes) if font_sizes else 0
        
        print(f"\nRESUMEN:")
        print(f"  Bloques: {block_count}")
        print(f"  Lineas: {line_count}")
        print(f"  Spans: {span_count}")
        print(f"  Tamano fuente promedio: {avg_font_size:.2f}")
        print(f"  Tamano fuente min: {min_font_size:.2f}")
        print(f"  Tamano fuente max: {max_font_size:.2f}")
        print(f"{'='*80}\n")
        
        return {
            'blocks': block_count,
            'lines': line_count,
            'spans': span_count,
            'avg_font_size': avg_font_size,
            'min_font_size': min_font_size,
            'max_font_size': max_font_size
        }

def translate_and_compare(input_pdf, output_pdf):
    """Traduce un PDF y compara la estructura."""
    
    print("\n" + "="*80)
    print("PRUEBA DE TRADUCCION CON ANALISIS DETALLADO")
    print("="*80)
    
    # Load translation model
    print("\n[1] Cargando modelo de traduccion...")
    argostranslate.translate.load_installed_languages()
    installed_languages = argostranslate.translate.get_installed_languages()
    
    english = next((lang for lang in installed_languages if lang.code == "en"), None)
    spanish = next((lang for lang in installed_languages if lang.code == "es"), None)
    
    if not english or not spanish:
        print("ERROR: Modelo de traduccion no encontrado")
        return False
    
    translator = english.get_translation(spanish)
    print("OK: Modelo cargado")
    
    # Analyze original
    print("\n[2] Analizando PDF original...")
    original_stats = analyze_page_structure(input_pdf, 0)
    
    # Translate
    print("\n[3] Traduciendo PDF...")
    try:
        with fitz.open(input_pdf) as source_pdf:
            translated_pdf = fitz.open()
            translated_pdf.insert_pdf(source_pdf)
            
            # Translate first page only for testing
            replace_text_in_page(
                source_pdf[0],
                translated_pdf[0],
                translator,
            )
            
            # Save
            translated_pdf.save(output_pdf)
            translated_pdf.close()
            print(f"OK: PDF traducido guardado: {output_pdf}")
    
    except Exception as e:
        print(f"ERROR durante traduccion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Analyze translated
    print("\n[4] Analizando PDF traducido...")
    translated_stats = analyze_page_structure(output_pdf, 0)
    
    # Compare
    print("\n[5] COMPARACION:")
    print(f"{'='*80}")
    print(f"{'Metrica':<25} {'Original':>15} {'Traducido':>15} {'Diferencia':>15}")
    print(f"{'-'*80}")
    print(f"{'Bloques':<25} {original_stats['blocks']:>15} {translated_stats['blocks']:>15} {translated_stats['blocks'] - original_stats['blocks']:>15}")
    print(f"{'Lineas':<25} {original_stats['lines']:>15} {translated_stats['lines']:>15} {translated_stats['lines'] - original_stats['lines']:>15}")
    print(f"{'Spans':<25} {original_stats['spans']:>15} {translated_stats['spans']:>15} {translated_stats['spans'] - original_stats['spans']:>15}")
    print(f"{'Tamano fuente promedio':<25} {original_stats['avg_font_size']:>15.2f} {translated_stats['avg_font_size']:>15.2f} {translated_stats['avg_font_size'] - original_stats['avg_font_size']:>15.2f}")
    print(f"{'Tamano fuente min':<25} {original_stats['min_font_size']:>15.2f} {translated_stats['min_font_size']:>15.2f} {translated_stats['min_font_size'] - original_stats['min_font_size']:>15.2f}")
    print(f"{'Tamano fuente max':<25} {original_stats['max_font_size']:>15.2f} {translated_stats['max_font_size']:>15.2f} {translated_stats['max_font_size'] - original_stats['max_font_size']:>15.2f}")
    print(f"{'='*80}")
    
    # Check if structure is preserved
    structure_preserved = (
        original_stats['blocks'] == translated_stats['blocks'] and
        original_stats['lines'] == translated_stats['lines']
    )
    
    font_sizes_preserved = (
        abs(original_stats['avg_font_size'] - translated_stats['avg_font_size']) < 0.5 and
        abs(original_stats['min_font_size'] - translated_stats['min_font_size']) < 0.5 and
        abs(original_stats['max_font_size'] - translated_stats['max_font_size']) < 0.5
    )
    
    if structure_preserved and font_sizes_preserved:
        print("\nOK: ESTRUCTURA Y TAMANOS PRESERVADOS CORRECTAMENTE")
        return True
    else:
        if not structure_preserved:
            print("\nADVERTENCIA: ESTRUCTURA MODIFICADA - Revisar algoritmo")
        if not font_sizes_preserved:
            print("\nADVERTENCIA: TAMANOS DE FUENTE MODIFICADOS - Revisar algoritmo")
        return False

if __name__ == "__main__":
    input_pdf = "media/pdfs/2025/12/01/ArcPro_Part1.pdf"
    output_pdf = "test_output_analysis.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"ERROR: No se encontro {input_pdf}")
        sys.exit(1)
    
    success = translate_and_compare(input_pdf, output_pdf)
    sys.exit(0 if success else 1)
