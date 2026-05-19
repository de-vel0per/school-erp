from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back {user.first_name} !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            
    return render(request, 'accounts/login.html')
    
    
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')
    


@login_required
def dashboard_view(request):
    user = request.user
    
    role = getattr(user, 'role', '')
    
    if user.role == 'admin':
        return render(request, 'accounts/dashboard_admin.html')
    elif user.role == 'teacher':
        return render(request, 'accounts/dashboard_teacher.html') 
    elif user.role == 'student':
        return render(request, 'accounts/dashboard_student.html')
    else:
        return render(request, 'accounts/dashboard_admin.html')


        
    
    
    
    