from django.db import models
from django.utils import timezone
import os


def pdf_upload_path(instance, filename):
    """Generate upload path for PDF files."""
    return f'pdfs/{timezone.now().strftime("%Y/%m/%d")}/{filename}'


def translated_pdf_upload_path(instance, filename):
    """Generate upload path for translated PDF files."""
    return f'translated/{timezone.now().strftime("%Y/%m/%d")}/{filename}'


def docx_upload_path(instance, filename):
    """Backward compatible alias kept for older migrations."""
    return translated_pdf_upload_path(instance, filename)


class PDFTranslation(models.Model):
    """Model to track PDF uploads and their translations."""
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('error', 'Error'),
    ]
    
    # Original PDF file
    pdf_file = models.FileField(
        upload_to=pdf_upload_path,
        verbose_name='Archivo PDF'
    )
    
    # Translated PDF file
    translated_pdf = models.FileField(
        upload_to=translated_pdf_upload_path,
        blank=True,
        null=True,
        verbose_name='PDF traducido'
    )
    
    # Metadata
    target_language = models.CharField(
        max_length=10,
        default='es',
        verbose_name='Idioma destino'
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Progreso (%)'
    )
    cancel_requested = models.BooleanField(
        default=False,
        verbose_name='Cancelación solicitada'
    )
    current_page = models.PositiveIntegerField(
        default=0,
        verbose_name='Página actual'
    )
    total_pages = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de páginas'
    )
    current_chunk = models.PositiveIntegerField(
        default=0,
        verbose_name='Parte actual'
    )
    total_chunks = models.PositiveIntegerField(
        default=0,
        verbose_name='Total de partes'
    )
    status_message = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Mensaje de estado'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='Mensaje de error'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    
    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de finalización'
    )
    
    class Meta:
        verbose_name = 'Traducción de PDF'
        verbose_name_plural = 'Traducciones de PDF'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Traducción {self.id} - {self.get_status_display()}"
    
    def get_pdf_filename(self):
        """Get the original PDF filename."""
        return os.path.basename(self.pdf_file.name)
    
    def get_translated_pdf_filename(self):
        """Get the translated PDF filename."""
        if self.translated_pdf:
            return os.path.basename(self.translated_pdf.name)
        return None
