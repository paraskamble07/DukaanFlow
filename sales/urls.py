from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pos/', views.pos_view, name='pos'),
    path('api/checkout/', views.checkout_api, name='checkout_api'),
    path('', views.sale_list, name='list'),
    path('<int:pk>/', views.sale_detail, name='detail'),
]
