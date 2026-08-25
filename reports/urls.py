from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_index, name='index'),
    path('sales/', views.sales_report, name='sales'),
    path('profit-loss/', views.profit_loss_report, name='profit_loss'),
    path('khata/', views.khata_report, name='khata'),
    path('inventory/', views.inventory_report, name='inventory'),
]
