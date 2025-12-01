#!/usr/bin/env python3
"""
Script para descargar e instalar el modelo de traducción EN->ES de Argos Translate.
"""

import argostranslate.package


def instalar_modelo_en_es():
    """Descarga e instala el modelo de traducción inglés-español."""
    
    print("Actualizando índice de paquetes...")
    argostranslate.package.update_package_index()
    
    print("Buscando modelo en->es...")
    available_packages = argostranslate.package.get_available_packages()
    
    # Buscar el paquete de inglés a español
    package_to_install = None
    for package in available_packages:
        if package.from_code == "en" and package.to_code == "es":
            package_to_install = package
            break
    
    if package_to_install is None:
        print("Error: No se encontró el modelo EN->ES")
        return False
    
    print("Descargando...")
    download_path = package_to_install.download()
    
    print("Instalando...")
    argostranslate.package.install_from_path(download_path)
    
    print("Listo. Modelo EN->ES instalado.")
    return True


if __name__ == "__main__":
    try:
        instalar_modelo_en_es()
    except Exception as e:
        print(f"Error durante la instalación: {e}")
        exit(1)
