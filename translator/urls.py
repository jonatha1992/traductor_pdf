from django.urls import path
from . import views

app_name = 'translator'

urlpatterns = [
    path('', views.upload_pdf, name='upload'),
    path('status/<int:pk>/', views.translation_status, name='status'),
    path('download/<int:pk>/', views.download_pdf, name='download'),
    path('cancel/<int:pk>/', views.cancel_translation, name='cancel'),
]
