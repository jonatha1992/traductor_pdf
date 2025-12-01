import os
from threading import Thread

from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

import math

import argostranslate.package
import argostranslate.translate
import fitz

from .forms import PDFUploadForm
from .models import PDFTranslation
from .pdf_layout import replace_text_in_page

CHUNK_SIZE_PAGES = 20


def get_translation_options():
    """Return available translation targets from English."""

    argostranslate.translate.load_installed_languages()
    installed_languages = argostranslate.translate.get_installed_languages()
    english_language = next((lang for lang in installed_languages if lang.code == "en"), None)
    installed_packages = argostranslate.package.get_installed_packages()

    options = []
    seen_codes = set()
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


def start_translation_thread(translation_id):
    """Kick off the translation job in a background thread."""

    thread = Thread(target=perform_translation_job, args=(translation_id,), daemon=True)
    thread.start()


def perform_translation_job(translation_id):
    try:
        translation_record = PDFTranslation.objects.get(pk=translation_id)
    except PDFTranslation.DoesNotExist:
        return

    options, english_language = get_translation_options()
    target_entry = next((opt for opt in options if opt["code"] == translation_record.target_language), None)

    if english_language is None or target_entry is None:
        translation_record.status = 'error'
        translation_record.error_message = 'No se encontro el modelo solicitado.'
        translation_record.save(update_fields=['status', 'error_message'])
        return

    translator = english_language.get_translation(target_entry["language"])
    translation_record.status = 'processing'
    translation_record.progress = 0
    translation_record.error_message = ''
    translation_record.status_message = 'Preparando traduccion...'
    translation_record.current_page = 0
    translation_record.total_pages = 0
    translation_record.current_chunk = 0
    translation_record.total_chunks = 0
    translation_record.save(update_fields=['status', 'progress', 'error_message', 'status_message', 'current_page', 'total_pages', 'current_chunk', 'total_chunks'])

    translated_pdf = None

    try:
        with fitz.open(translation_record.pdf_file.path) as source_pdf:
            total_pages = source_pdf.page_count
            translation_record.total_pages = total_pages
            translation_record.total_chunks = math.ceil(total_pages / CHUNK_SIZE_PAGES) if total_pages else 0
            translation_record.status_message = f"Documento con {total_pages} paginas detectado."
            translation_record.save(update_fields=['total_pages', 'total_chunks', 'status_message'])

            translated_pdf = fitz.open()
            translated_pdf.insert_pdf(source_pdf)

            if total_pages == 0:
                translation_record.progress = 100
                translation_record.status_message = 'El PDF no contiene paginas procesables.'
                translation_record.save(update_fields=['progress', 'status_message'])
            else:
                for chunk_index, chunk_start in enumerate(range(0, total_pages, CHUNK_SIZE_PAGES), start=1):
                    chunk_end = min(chunk_start + CHUNK_SIZE_PAGES, total_pages)
                    translation_record.current_chunk = chunk_index
                    translation_record.status_message = (
                        f"Procesando paginas {chunk_start + 1}-{chunk_end} "
                        f"(parte {chunk_index}/{translation_record.total_chunks})"
                    )
                    translation_record.save(update_fields=['current_chunk', 'status_message'])

                    for page_index in range(chunk_start, chunk_end):
                        translation_record.refresh_from_db(fields=['cancel_requested'])
                        if translation_record.cancel_requested:
                            translation_record.status = 'error'
                            translation_record.status_message = 'Traduccion cancelada por el usuario.'
                            translation_record.error_message = 'Traduccion cancelada por el usuario.'
                            translation_record.save(update_fields=['status', 'status_message', 'error_message'])
                            translated_pdf.close()
                            return

                        replace_text_in_page(
                            source_pdf[page_index],
                            translated_pdf[page_index],
                            translator,
                        )

                        translation_record.current_page = page_index + 1
                        translation_record.progress = round((page_index + 1) / total_pages * 100)
                        translation_record.save(update_fields=['current_page', 'progress'])

        pdf_bytes = translated_pdf.tobytes() if translated_pdf else b''
        pdf_name = f"{os.path.splitext(translation_record.get_pdf_filename())[0]}_{translation_record.target_language}.pdf"
        translation_record.translated_pdf.save(pdf_name, ContentFile(pdf_bytes))
        translation_record.progress = 100
        translation_record.status = 'completed'
        translation_record.completed_at = timezone.now()
        translation_record.error_message = ''
        translation_record.status_message = 'Traduccion completada exitosamente.'
        translation_record.current_page = translation_record.total_pages
        translation_record.current_chunk = translation_record.total_chunks
        translation_record.save(update_fields=['progress', 'status', 'completed_at', 'error_message', 'status_message', 'current_page', 'current_chunk'])

    except Exception as exc:
        translation_record.status = 'error'
        translation_record.error_message = str(exc)
        translation_record.status_message = str(exc)
        translation_record.save(update_fields=['status', 'error_message', 'status_message'])
    finally:
        if translated_pdf:
            translated_pdf.close()

def upload_pdf(request):
    """Render the upload interface and handle translation requests."""

    language_options, _ = get_translation_options()
    form = PDFUploadForm()
    context = {
        'form': form,
        'language_options': language_options,
    }

    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)
            context['form'] = form
            return render(request, 'translator/upload.html', context)

        translation = form.save(commit=False)
        translation.target_language = request.POST.get('target_language', 'es')
        translation.status = 'pending'
        translation.progress = 0
        translation.cancel_requested = False
        translation.save()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            start_translation_thread(translation.id)
            return JsonResponse({'translation_id': translation.id})

        perform_translation_job(translation.id)
        translation.refresh_from_db()
        context['completed_translation'] = translation
        context['form'] = PDFUploadForm()

    return render(request, 'translator/upload.html', context)


def translation_status(request, pk):
    """Return JSON with the current status and progress of a translation."""

    translation = get_object_or_404(PDFTranslation, pk=pk)
    data = {
        'status': translation.status,
        'progress': translation.progress,
        'status_message': translation.status_message or translation.error_message or '',
        'target_language': translation.target_language,
        'original_filename': translation.get_pdf_filename(),
        'current_page': translation.current_page,
        'total_pages': translation.total_pages,
        'current_chunk': translation.current_chunk,
        'total_chunks': translation.total_chunks,
    }

    if translation.completed_at:
        data['completed_at'] = translation.completed_at.strftime('%d/%m/%Y %H:%M')

    if translation.translated_pdf and translation.status == 'completed':
        data['download_url'] = reverse('translator:download', args=[translation.id])

    return JsonResponse(data)


def download_pdf(request, pk):
    """Serve the translated PDF for download."""

    translation = get_object_or_404(PDFTranslation, pk=pk, status='completed')
    if not translation.translated_pdf:
        raise Http404

    response = FileResponse(
        translation.translated_pdf.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{translation.get_translated_pdf_filename()}"'
    return response


@require_POST
def cancel_translation(request, pk):
    """Mark a running translation as canceled."""

    translation = get_object_or_404(PDFTranslation, pk=pk)
    if translation.status == 'processing':
        translation.cancel_requested = True
        translation.save(update_fields=['cancel_requested'])
        return JsonResponse({'canceled': True})
    return JsonResponse({'canceled': False, 'status': translation.status})
