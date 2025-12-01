from django.contrib import admin
from .models import PDFTranslation


@admin.register(PDFTranslation)
class PDFTranslationAdmin(admin.ModelAdmin):
    """Admin interface for PDF translations."""
    
    list_display = ['id', 'get_pdf_filename', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['pdf_file', 'error_message']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = [
        ('Archivos', {
            'fields': ['pdf_file', 'translated_pdf']
        }),
        ('Estado', {
            'fields': ['status', 'error_message']
        }),
        ('Fechas', {
            'fields': ['created_at', 'completed_at']
        }),
    ]
