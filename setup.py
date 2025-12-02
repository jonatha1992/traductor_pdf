#!/usr/bin/env python3
"""
Script de instalación automática para el proyecto Traductor de PDF.
Ejecuta todos los pasos necesarios para configurar el proyecto.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{'='*60}")
    print(f"📋 {description}")
    print(f"{'='*60}")
    print(f"Ejecutando: {command}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ {description} - COMPLETADO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en: {description}")
        print(f"Código de salida: {e.returncode}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Función principal de instalación."""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║        INSTALADOR AUTOMÁTICO - TRADUCTOR DE PDF           ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar versión de Python
    print(f"🐍 Python versión: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        sys.exit(1)
    
    # Paso 1: Instalar dependencias
    if not run_command(
        "pip install -r requirements.txt",
        "Instalando dependencias de Python"
    ):
        print("\n❌ Error al instalar dependencias. Abortando.")
        sys.exit(1)
    
    # Paso 2: Instalar modelo de traducción
    if not run_command(
        "python instalar_modelo_en_es.py",
        "Instalando modelo de traducción EN→ES"
    ):
        print("\n⚠️ Advertencia: El modelo de traducción no se instaló correctamente.")
        print("Puedes intentar instalarlo manualmente más tarde con:")
        print("python instalar_modelo_en_es.py")
    
    # Paso 3: Aplicar migraciones
    if not run_command(
        "python manage.py migrate",
        "Aplicando migraciones de base de datos"
    ):
        print("\n❌ Error al aplicar migraciones. Abortando.")
        sys.exit(1)
    
    # Verificar que los directorios media existan
    os.makedirs("media/pdfs", exist_ok=True)
    os.makedirs("media/translated", exist_ok=True)
    print("\n✅ Directorios de media creados")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("🎉 ¡INSTALACIÓN COMPLETADA CON ÉXITO!")
    print(f"{'='*60}")
    print("\n📝 Próximos pasos:")
    print("   1. Inicia el servidor: python manage.py runserver")
    print("   2. Abre tu navegador en: http://127.0.0.1:8000/")
    print("   3. ¡Comienza a traducir PDFs!")
    print("\n📖 Para más información, consulta el archivo README.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Instalación cancelada por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
