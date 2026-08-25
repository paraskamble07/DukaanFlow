from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, UserProfileForm
from .models import UserProfile
from businesses.models import Business

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']
            shop_name = form.cleaned_data['shop_name']
            phone = form.cleaned_data['phone']
            
            # Create User
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=full_name
            )
            
            # Create Business
            business = Business.objects.create(
                owner=user,
                name=shop_name,
                owner_name=full_name,
                phone=phone,
                email=email,
                plan_tier='FREE'
            )
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                business=business,
                phone=phone,
                role='OWNER'
            )
            
            # Auto login
            login(request, user)
            messages.success(request, f"Welcome to DukaanFlow, {full_name}! Your shop '{shop_name}' is now ready.")
            return redirect('dashboard:index')
    else:
        form = RegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, username=username_or_email, password=password)
            if user is None and '@' in username_or_email:
                user_obj = User.objects.filter(email__iexact=username_or_email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard:index')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email/username or password. Please try again.")
    else:
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing:home')

@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save()
        
        messages.success(request, "Profile details updated successfully.")
        return redirect('accounts:profile')
        
    return render(request, 'accounts/profile.html', {'user': user, 'profile': profile})
