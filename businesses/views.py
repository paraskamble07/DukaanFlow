from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Business, PLAN_LIMITS
from .forms import BusinessSettingsForm
from accounts.models import UserProfile

@login_required
def onboarding_view(request):
    if getattr(request, 'business', None):
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, request.FILES)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()
            
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.business = business
            profile.save()
            
            messages.success(request, f"Shop '{business.name}' configured successfully!")
            return redirect('dashboard:index')
    else:
        form = BusinessSettingsForm(initial={
            'owner_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })
        
    return render(request, 'businesses/settings.html', {'form': form, 'is_onboarding': True})

@login_required
def settings_view(request):
    business = getattr(request, 'business', None)
    if not business:
        return redirect('businesses:onboarding')
        
    if request.method == 'POST':
        form = BusinessSettingsForm(request.POST, request.FILES, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, "Business settings updated successfully!")
            return redirect('businesses:settings')
    else:
        form = BusinessSettingsForm(instance=business)
        
    return render(request, 'businesses/settings.html', {'form': form, 'business': business, 'is_onboarding': False})

@login_required
def plans_view(request):
    business = getattr(request, 'business', None)
    
    if request.method == 'POST':
        new_plan = request.POST.get('plan')
        if new_plan in PLAN_LIMITS and business:
            business.plan_tier = new_plan
            business.save(update_fields=['plan_tier'])
            messages.success(request, f"Your subscription plan has been updated to {PLAN_LIMITS[new_plan]['name']}!")
            return redirect('businesses:plans')
            
    return render(request, 'businesses/plans.html', {
        'business': business,
        'plans': PLAN_LIMITS,
        'current_plan': business.plan_tier if business else 'FREE'
    })
