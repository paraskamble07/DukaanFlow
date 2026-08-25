from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('customer/add/', views.customer_payment_create, name='customer_add'),
    path('supplier/add/', views.supplier_payment_create, name='supplier_add'),
]
