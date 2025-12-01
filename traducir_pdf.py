#!/usr/bin/env python3
"""Script para traducir un PDF manteniendo el formato original."""

import argparse
import signal
import sys

import argostranslate.package
import argostranslate.translate
import fitz

from translator.pdf_layout import replace_text_in_page


_stop_requested = False


def _handle_interrupt(signum, frame):
    global _stop_requested
    if not _stop_requested:
        print("\nDeteniendo traduccion...")
    _stop_requested = True


signal.signal(signal.SIGINT, _handle_interrupt)


def get_translation_options():
    """Retorna las traducciones disponibles desde ingles."""

    argostranslate.translate.load_installed_languages()
    installed_languages = argostranslate.translate.get_installed_languages()
    english_language = next((lang for lang in installed_languages if lang.code == "en"), None)
    if english_language is None:
        return [], None

    installed_packages = argostranslate.package.get_installed_packages()
    seen_codes = set()
    options = []
    for package in installed_packages:
        if package.from_code != "en":
            continue
        target_code = package.to_code
        if target_code in seen_codes:
            continue
        target_language = next((lang for lang in installed_languages if lang.code == target_code), None)
        if target_language is None:
            continue
        seen_codes.add(target_code)
        options.append({
            "code": target_code,
            "name": target_language.name,
            "language": target_language,
        })

    return options, english_language


def print_available_targets(options):
    """Imprime los codigos y nombres de los idiomas listados."""

    if not options:
        print("No se encontraron idiomas de destino instalados desde ingles.")
        print("Instala un modelo (por ejemplo: python instalar_modelo_en_es.py).")
        return

    print("Idiomas disponibles desde ingles:")
    for option in options:
        print(f"  {option['code']} - {option['name']}")


def select_translation_option(target_code, options):
    """Devuelve la opcion que coincide con el codigo solicitado."""

    normalized_code = target_code.lower()
    for option in options:
        if option["code"].lower() == normalized_code:
            return option
    return None


def print_progress(current, total, prefix='', length=40):
    """Muestra una barra de progreso en la terminal."""

    safe_total = max(total, 1)
    safe_current = min(max(current, 0), safe_total)
    percent = safe_current / safe_total
    filled_length = int(length * percent)
    bar = '#' * filled_length + '-' * (length - filled_length)
    print(f"\r{prefix} |{bar}| {percent * 100:6.2f}% ({safe_current}/{safe_total})", end='', flush=True)


def traducir_pdf(input_pdf, output_pdf, translation, target_name):
    """Traduce un PDF manteniendo la estructura visual original."""

    print(f"Cargando modelo {translation.from_lang.name} -> {target_name}...")
    print(f"Leyendo PDF: {input_pdf}")

    translated_pdf = None

    try:
        global _stop_requested
        _stop_requested = False
        with fitz.open(input_pdf) as source_pdf:
            total_pages = source_pdf.page_count
            translated_pdf = fitz.open()
            translated_pdf.insert_pdf(source_pdf)

            progress_label = f"Traduciendo a {target_name}"
            if total_pages == 0:
                print("El documento no contiene paginas procesables.")
            else:
                print_progress(0, total_pages, prefix=progress_label)

            for page_index in range(total_pages):
                if _stop_requested:
                    print("\nTraduccion cancelada por el usuario.")
                    translated_pdf.close()
                    translated_pdf = None
                    return False

                replace_text_in_page(
                    source_pdf[page_index],
                    translated_pdf[page_index],
                    translation,
                )

                if total_pages:
                    print_progress(page_index + 1, total_pages, prefix=progress_label)

            if translated_pdf.page_count == 0:
                translated_pdf.new_page(width=595, height=842)

            if total_pages:
                print()

        print(f"Guardando documento traducido: {output_pdf}")
        translated_pdf.save(output_pdf)
        print("-> Traduccion completada exitosamente!")
        return True

    except KeyboardInterrupt:
        print("\nTraduccion cancelada por el usuario.")
        return False
    except FileNotFoundError:
        print(f"Error: No se encontro el archivo {input_pdf}")
        return False
    except Exception as exc:
        print(f"Error durante la traduccion: {exc}")
        return False
    finally:
        if translated_pdf:
            translated_pdf.close()


def main():
    """Funcion principal que maneja los argumentos de linea de comandos."""

    parser = argparse.ArgumentParser(
        description="Traducir PDFs de ingles a otro idioma usando Argos Translate"
    )
    parser.add_argument("input_pdf", nargs="?", help="Ruta al archivo PDF de entrada")
    parser.add_argument("output_pdf", nargs="?", help="Ruta al archivo PDF de salida")
    parser.add_argument(
        "-t",
        "--target",
        dest="target",
        default="es",
        help="Codigo del idioma destino (por ejemplo, 'es' para espanol)",
    )
    parser.add_argument(
        "--list-targets",
        action="store_true",
        help="Listar los idiomas disponibles desde ingles",
    )
    args = parser.parse_args()

    options, english_language = get_translation_options()
    if english_language is None:
        print("No se encontro el modelo de traduccion desde ingles.")
        print("Instala uno con: python instalar_modelo_en_es.py")
        sys.exit(1)

    if args.list_targets:
        print_available_targets(options)
        sys.exit(0)

    if not options:
        print("No hay modelos de traduccion EN->X instalados en este equipo.")
        print("Instala un modelo con: python instalar_modelo_en_es.py")
        sys.exit(1)

    if not args.input_pdf or not args.output_pdf:
        parser.error("Debes indicar el archivo PDF de entrada y el PDF de salida.")

    selected_option = select_translation_option(args.target, options)
    if selected_option is None:
        print(f"Idioma destino '{args.target}' no esta disponible.")
        print_available_targets(options)
        sys.exit(1)

    target_language = selected_option["language"]
    translation = english_language.get_translation(target_language)
    target_name = selected_option["name"]

    success = traducir_pdf(args.input_pdf, args.output_pdf, translation, target_name)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
