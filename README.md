# Traductor de PDF

Aplicacion web en Django para traducir archivos PDF de ingles a idiomas instalados en Argos Translate (por defecto, espanol), manteniendo una estructura visual similar del documento original.

El procesamiento se hace localmente, con seguimiento de progreso en tiempo real y opcion de cancelar una traduccion en curso.

## Caracteristicas

- Traduccion de PDF desde una interfaz web simple.
- Ejecucion offline despues de instalar dependencias y modelos.
- Progreso en tiempo real (porcentaje, pagina actual y bloque actual).
- Procesamiento por bloques de 20 paginas para mejorar control de avance.
- Cancelacion de traducciones en curso desde la UI.
- Descarga del PDF traducido al finalizar.
- Validacion de archivo (`.pdf`, maximo 50 MB).

## Stack

- Python 3.8+
- Django 4.2
- Argos Translate
- PyMuPDF (`fitz`)
- SQLite (desarrollo)

## Requisitos

- Python 3.8 o superior
- `pip`
- Conexion a internet para instalar dependencias y descargar modelos de traduccion (solo en setup)

## Instalacion

### Opcion 1: Instalacion automatica (recomendada)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

python setup.py
```

Este script:
- Instala dependencias de `requirements.txt`
- Descarga e instala el modelo EN->ES
- Ejecuta migraciones
- Crea directorios de `media`

### Opcion 2: Instalacion manual

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
python instalar_modelo_en_es.py
python manage.py migrate
python manage.py runserver
```

Aplicacion disponible en: `http://127.0.0.1:8000/`

## Uso rapido

1. Abrir `http://127.0.0.1:8000/`
2. Subir un PDF en ingles
3. Elegir idioma destino (segun modelos instalados)
4. Iniciar traduccion
5. Monitorear progreso o cancelar si hace falta
6. Descargar el PDF traducido al finalizar

## Endpoints principales

- `GET /` interfaz de carga y traduccion
- `GET /status/<id>/` estado y progreso de la traduccion (JSON)
- `GET /download/<id>/` descarga del PDF traducido (si `completed`)
- `POST /cancel/<id>/` solicita cancelacion de traduccion en curso

## Estructura del proyecto

```text
traductor_pdf/
├── pdf_translator_project/   # Configuracion Django (settings, urls, wsgi/asgi)
├── translator/               # App principal de traduccion
│   ├── views.py              # Flujo de carga, estado, descarga y cancelacion
│   ├── pdf_layout.py         # Reemplazo de texto en paginas PDF
│   ├── models.py             # Modelo PDFTranslation
│   ├── forms.py              # Validacion de archivo PDF
│   ├── templates/translator/upload.html
│   └── static/translator/style.css
├── media/                    # PDFs subidos y traducidos
├── instalar_modelo_en_es.py  # Instala modelo EN->ES de Argos
├── setup.py                  # Instalador automatico del proyecto
├── QUICKSTART.md
└── requirements.txt
```

## Donde se guardan los archivos

- PDF original: `media/pdfs/YYYY/MM/DD/<archivo>.pdf`
- PDF traducido: `media/translated/YYYY/MM/DD/<archivo>_<idioma>.pdf`

## Configuracion relevante

- Limite de subida: 50 MB (`FILE_UPLOAD_MAX_MEMORY_SIZE`, `DATA_UPLOAD_MAX_MEMORY_SIZE`)
- Zona horaria: `America/Argentina/Buenos_Aires`
- Idioma de Django: `es-es`
- Base de datos: SQLite (`db.sqlite3`)

## Problemas comunes

- `ModuleNotFoundError`
  - Ejecutar `pip install -r requirements.txt`
- `no such table`
  - Ejecutar `python manage.py migrate`
- No aparecen idiomas/modelos disponibles
  - Ejecutar `python instalar_modelo_en_es.py`
- El archivo no carga
  - Verificar que sea `.pdf` y pese menos de 50 MB

## Notas de desarrollo

- La traduccion se ejecuta en un hilo en background al usar la UI con peticiones AJAX.
- El estado de traduccion se persiste en el modelo `PDFTranslation`.
- No hay tests automatizados incluidos actualmente.

## Nota para produccion

La configuracion actual esta orientada a desarrollo local:
- `DEBUG = True`
- `ALLOWED_HOSTS = []`
- `SECRET_KEY` de ejemplo en settings

Antes de desplegar en produccion, ajustar estas variables y endurecer configuracion de static/media y seguridad.
