from django.urls import path
from . import views

app_name = 'invoices'

urlpatterns = [
    path('<int:pk>/', views.invoice_detail, name='detail'),
    path('<int:pk>/pdf/', views.invoice_pdf_download, name='pdf'),
    path('<int:pk>/print/', views.invoice_print, name='print'),
]
