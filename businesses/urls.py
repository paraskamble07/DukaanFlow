from django.urls import path
from . import views

app_name = 'businesses'

urlpatterns = [
    path('onboarding/', views.onboarding_view, name='onboarding'),
    path('settings/', views.settings_view, name='settings'),
    path('plans/', views.plans_view, name='plans'),
]
