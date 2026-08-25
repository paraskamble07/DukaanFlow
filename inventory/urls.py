from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('imei/', views.imei_list, name='imei_list'),
    path('imei/add/', views.imei_create, name='imei_create'),
    path('imei/search/', views.imei_search, name='imei_search'),
]
