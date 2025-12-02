#!/usr/bin/env python3
"""
Script rápido para probar la traducción con el nuevo enfoque optimizado.
"""

import sys
import argostranslate.package
import argostranslate.translate
import fitz

# Add the project root to the path
sys.path.insert(0, 'D:\\Repositorio\\jonatha1992\\traductor_pdf')

from translator.pdf_layout import replace_text_in_page

def test_translation():
    print("=" * 60)
    print("PRUEBA DE TRADUCCIÓN OPTIMIZADA")
    print("=" * 60)
    
    # Load translation model
    print("\n1. Cargando modelo de traducción EN → ES...")
    argostranslate.translate.load_installed_languages()
    installed_languages = argostranslate.translate.get_installed_languages()
    
    english = next((lang for lang in installed_languages if lang.code == "en"), None)
    spanish = next((lang for lang in installed_languages if lang.code == "es"), None)
    
    if not english or not spanish:
        print("❌ Error: Modelo de traducción no encontrado")
        return False
    
    translator = english.get_translation(spanish)
    print("✅ Modelo cargado")
    
    # Open test PDF
    input_pdf = "media/pdfs/2025/12/01/ArcPro_JMBOYl0.pdf"
    output_pdf = "test_output_optimized.pdf"
    
    print(f"\n2. Abriendo PDF: {input_pdf}")
    
    try:
        with fitz.open(input_pdf) as source_pdf:
            total_pages = source_pdf.page_count
            print(f"✅ PDF abierto: {total_pages} páginas")
            
            # Create translated PDF
            translated_pdf = fitz.open()
            translated_pdf.insert_pdf(source_pdf)
            
            # Translate only first page for quick test
            print(f"\n3. Traduciendo página 1 (prueba rápida)...")
            
            import time
            start_time = time.time()
            
            replace_text_in_page(
                source_pdf[0],
                translated_pdf[0],
                translator,
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Página traducida en {elapsed:.2f} segundos")
            
            # Save
            print(f"\n4. Guardando: {output_pdf}")
            translated_pdf.save(output_pdf)
            translated_pdf.close()
            print(f"✅ PDF guardado")
            
            print("\n" + "=" * 60)
            print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print(f"📁 Archivo: {output_pdf}")
            print(f"⏱️  Tiempo: {elapsed:.2f}s por página")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)
