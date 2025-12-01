# CLAUDE.md

This document gives Codex / Claude Code a quick overview of the repository.

## Resumen del proyecto

- Aplicación web Django para traducir PDFs de inglés a otros idiomas usando modelos offline de Argos Translate.
- El objetivo principal es conservar el diseño original del PDF: se copia cada página y se reemplazan los bloques de texto directamente en el PDF final.
- Se persisten los trabajos en el modelo `PDFTranslation` para poder consultar progreso, cancelar la tarea y descargar el resultado una vez que finaliza.
- También existe un script CLI (`traducir_pdf.py`) que reutiliza la misma lógica basada en PyMuPDF para procesar documentos desde la terminal.

## Componentes principales

| Archivo/Carpeta | Descripción |
| --- | --- |
| `pdf_translator_project/` | Configuración estándar de Django (settings, urls, wsgi/asgi). |
| `translator/` | App con modelos, formularios, vistas, templates y assets. |
| `translator/pdf_layout.py` | Helpers basados en PyMuPDF para reemplazar texto en bloques conservando el layout. |
| `translator/views.py` | Flujo completo de traducción en background. Se divide en bloques de páginas para reportar progreso. |
| `translator/models.py` | Modelo `PDFTranslation` con el PDF original, el PDF traducido y metadatos de estado/progreso. |
| `translator/templates/translator/upload.html` | Única vista frontend (drag & drop, barra de progreso y botón de cancelación). |
| `traducir_pdf.py` | Script CLI que recibe `input.pdf` y `output.pdf` y muestra progreso en consola. |

## Flujo de traducción web

1. El usuario sube un PDF mediante `PDFUploadForm`.
2. Se crea un registro `PDFTranslation` con estado `pending`.
3. `views.start_translation_thread()` lanza un hilo que ejecuta `perform_translation_job`.
4. `perform_translation_job`:
   - Detecta cantidad de páginas y partes (`CHUNK_SIZE_PAGES`).
   - Abre el PDF con PyMuPDF, duplica todas las páginas y luego recorre bloque por bloque.
   - Cada bloque de texto se traduce con Argos Translate y se reescribe dentro del rectángulo original (reduciendo tipografía si es necesario).
   - Se actualizan campos `current_page`, `progress`, `current_chunk` y `status_message` para que el frontend los consulte vía `translation_status`.
   - Si el usuario solicita cancelación, se marca el registro en estado de error con mensaje de cancelación.
   - Al finalizar se guarda `translated_pdf` en `media/translated/...` y se marca como `completed`.
5. El frontend usa fetch + polling (cada 2 s) para mostrar progreso y habilitar el enlace de descarga (`translator:download`).

## Comandos útiles

```bash
# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar modelo Argos EN->ES (u otros equivalentes)
python instalar_modelo_en_es.py

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Servidor de desarrollo
python manage.py runserver
```

### CLI

```bash
python traducir_pdf.py input.pdf output.pdf
python traducir_pdf.py --target es input.pdf output.pdf
python traducir_pdf.py --list-targets
```

## Consideraciones

- Entrada soportada: solo PDF, máximo 50 MB (validez en formulario).
- Salida: PDF idéntico al original pero con texto traducido (las imágenes y diagramas quedan intactos).
- Todo el proceso es offline: tras instalar el modelo Argos no se requiere red.
- Para PDFs basados únicamente en imágenes se necesitaría OCR previo (no incluido).
- Cancelar traducciones solo es posible mientras el estado está en `processing`.
- `requirements.txt` usa PyMuPDF; pdfplumber y python-docx ya no forman parte del pipeline.
