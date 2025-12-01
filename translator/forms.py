from django import forms
from .models import PDFTranslation


class PDFUploadForm(forms.ModelForm):
    """Form for uploading PDF files."""
    
    class Meta:
        model = PDFTranslation
        fields = ['pdf_file']
        widgets = {
            'pdf_file': forms.FileInput(attrs={
                'accept': '.pdf',
                'class': 'file-input',
                'id': 'pdf-file-input'
            })
        }
        labels = {
            'pdf_file': 'Selecciona un archivo PDF'
        }
    
    def clean_pdf_file(self):
        """Validate that the uploaded file is a PDF."""
        pdf_file = self.cleaned_data.get('pdf_file')
        
        if pdf_file:
            # Check file extension
            if not pdf_file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Solo se permiten archivos PDF.')
            
            # Check file size (max 50MB)
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('El archivo es demasiado grande. Máximo 50MB.')
        
        return pdf_file
