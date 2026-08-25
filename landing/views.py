from django.shortcuts import render, redirect
from businesses.models import PLAN_LIMITS

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'landing/index.html', {
        'plans': PLAN_LIMITS
    })
