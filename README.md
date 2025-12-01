# PDF Translator - Django Web Application

Aplicación web Django para traducir archivos PDF de inglés a español de forma completamente offline usando Argos Translate.

## 🌟 Características

- ✅ **100% Offline** - No requiere conexión a Internet después de la instalación
- ✅ **Interfaz Web Moderna** - Diseño premium con drag-and-drop
- ✅ **Traducción EN→ES** - Traduce de inglés a español
- ✅ **Formato PDF preservado** - Mantiene el estilo y las imágenes originales
- ✅ **Privado y Seguro** - Tus documentos nunca salen de tu computadora

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
cd c:\Repositorio\traductor_pdf
```

### 2. Crear un entorno virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar el modelo de traducción EN→ES

```bash
python instalar_modelo_en_es.py
```

Este script descargará e instalará el modelo de traducción. Solo necesitas ejecutarlo una vez.

### 5. Configurar la base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. (Opcional) Crear un superusuario para el admin

```bash
python manage.py createsuperuser
```

## 🎯 Uso

### Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

### Acceder a la aplicación

Abre tu navegador y visita:

```
http://localhost:8000/
```

### Traducir un PDF

1. Haz clic en el área de carga o arrastra un archivo PDF
2. Haz clic en "Traducir PDF"
3. Espera a que se complete la traducción
4. Descarga el PDF traducido con el mismo formato

### Panel de administración (opcional)

Si creaste un superusuario, puedes acceder al panel de administración en:

```
http://localhost:8000/admin/
```

## 📁 Estructura del Proyecto

```
traductor_pdf/
├── manage.py                      # Script de gestión de Django
├── requirements.txt               # Dependencias del proyecto
├── instalar_modelo_en_es.py      # Script para instalar modelo de traducción
├── README.md                      # Este archivo
│
├── pdf_translator_project/        # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py               # Configuración de Django
│   ├── urls.py                   # URLs principales
│   ├── asgi.py
│   └── wsgi.py
│
└── translator/                    # Aplicación de traducción
    ├── __init__.py
    ├── admin.py                  # Configuración del admin
    ├── apps.py                   # Configuración de la app
    ├── forms.py                  # Formularios
    ├── models.py                 # Modelos de base de datos
    ├── urls.py                   # URLs de la app
    ├── views.py                  # Vistas y lógica de traducción
    ├── migrations/               # Migraciones de base de datos
    ├── static/
    │   └── translator/
    │       └── style.css         # Estilos CSS
    └── templates/
        └── translator/
            └── upload.html       # Template principal
```

## 🛠️ Tecnologías Utilizadas

- **Django 4.2** - Framework web
- **argostranslate** - Motor de traducción offline
- **PyMuPDF** - Reemplazo de texto y preservación de diseño en PDFs

## 📝 Notas Importantes

- **Tamaño máximo de archivo**: 10MB
- **Formatos soportados**: Solo archivos PDF
- **Idiomas**: Inglés → Español
- **Salida**: Documento PDF con el diseño original

## 🔧 Solución de Problemas

### Error: "Modelo de traducción EN→ES no encontrado"

Ejecuta el script de instalación del modelo:

```bash
python instalar_modelo_en_es.py
```

### Error: "No module named 'django'"

Asegúrate de haber instalado las dependencias:

```bash
pip install -r requirements.txt
```

### El PDF no tiene texto extraíble

Algunos PDFs son solo imágenes escaneadas. Para estos casos, necesitarías usar OCR (reconocimiento óptico de caracteres) antes de la traducción.

### Error de permisos en archivos media

Asegúrate de que Django tenga permisos para crear la carpeta `media/` en el directorio del proyecto.

## 🎨 Características de la Interfaz

- **Drag & Drop** - Arrastra archivos directamente al navegador
- **Diseño Responsivo** - Funciona en desktop y móvil
- **Modo Oscuro** - Diseño moderno con colores vibrantes
- **Animaciones Suaves** - Micro-animaciones para mejor UX
- **Feedback Visual** - Indicadores de progreso y estado

## 📦 Archivos Generados

Los archivos se almacenan en:

- **PDFs originales**: `media/pdfs/YYYY/MM/DD/`
- **PDFs traducidos**: `media/translated/YYYY/MM/DD/`

## Herramienta CLI de traducción

También puedes traducir archivos desde la terminal con el script `traducir_pdf.py`. El script muestra una barra de progreso mientras procesa cada página y acepta el código del idioma destino.

```
python traducir_pdf.py documento.pdf documento_traducido.pdf
python traducir_pdf.py --target es documento.pdf documento_traducido.pdf
python traducir_pdf.py --list-targets
```

Usa `--target` para indicar el idioma destino (por ejemplo `es` para español) o `--list-targets` para ver los idiomas instalados desde inglés. Asegúrate de ejecutar primero `python instalar_modelo_en_es.py` para instalar el modelo requerido.

Durante la traducción puedes presionar `Ctrl+C` para detener el proceso; el script cancelará la operación sin guardar el archivo incompleto.

La interfaz web ahora divide internamente los PDFs en bloques de unas 20 páginas, muestra "Procesando página X de Y" y "Parte N de M" mientras traduce cada bloque, y ofrece un botón para detener la traducción si lo deseas.

## 🔐 Seguridad

- Todos los archivos se procesan localmente
- No se envían datos a servicios externos
- No se requiere conexión a Internet para traducir
- Los archivos se almacenan en tu computadora

## 📄 Licencia

Este proyecto es de código abierto y está disponible para uso personal y educativo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias o mejoras.

## 📧 Soporte

Si encuentras algún problema, por favor crea un issue en el repositorio del proyecto.

---

**¡Disfruta traduciendo tus PDFs de forma offline! 🚀**
