# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a poner en marcha el proyecto en **menos de 5 minutos**.

## ⚡ Instalación Rápida (Recomendado)

### Opción 1: Script Automático

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Ejecutar instalador automático
python setup.py
```

¡Eso es todo! El script instalará todo automáticamente.

### Opción 2: Instalación Manual

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar modelo de traducción
python instalar_modelo_en_es.py

# 4. Configurar base de datos
python manage.py migrate

# 5. Iniciar servidor
python manage.py runserver
```

## 🌐 Acceder a la Aplicación

Una vez iniciado el servidor, abre tu navegador en:

**http://127.0.0.1:8000/**

## 📝 Uso Básico

1. **Subir PDF**: Haz clic en "Elegir archivo" y selecciona un PDF en inglés
2. **Traducir**: Haz clic en "Traducir PDF"
3. **Descargar**: Espera unos segundos y descarga el PDF traducido

## ⚠️ Problemas Comunes

| Error | Solución Rápida |
|-------|----------------|
| `ModuleNotFoundError` | Ejecuta `pip install -r requirements.txt` |
| `no such table` | Ejecuta `python manage.py migrate` |
| `No se detectaron modelos` | Ejecuta `python instalar_modelo_en_es.py` |

## 📚 Documentación Completa

Para más detalles, consulta el archivo [README.md](README.md)

## 🆘 ¿Necesitas Ayuda?

Si encuentras algún problema:
1. Revisa la sección de **Solución de Problemas** en el README
2. Verifica que hayas activado el entorno virtual
3. Asegúrate de tener Python 3.8 o superior

---

**¡Listo para traducir PDFs! 🎉**
