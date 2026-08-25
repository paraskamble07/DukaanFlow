from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('landing.urls', namespace='landing')),
    path('auth/', include('accounts.urls', namespace='accounts')),
    path('business/', include('businesses.urls', namespace='businesses')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('products/', include('products.urls', namespace='products')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
    path('purchases/', include('purchases.urls', namespace='purchases')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('expenses/', include('expenses.urls', namespace='expenses')),
    path('payments/', include('payments.urls', namespace='payments')),
    path('invoices/', include('invoices.urls', namespace='invoices')),
    path('reports/', include('reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
