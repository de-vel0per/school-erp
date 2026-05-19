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
        from school.models import Attendance, Exam, LeaveRequest, OTRequest
        from accounts.models import Teacher, Student
        from django.utils import timezone
        
        data = {
            'teacher_count': Teacher.objects.count(),
            'student_count': Student.objecs.count(),
            'pending_leaves': LeaveRequest.objects.filter(status='pending').count(),
            'pending_ots': OTRequest.objects.filter(status='pending').count(),
            'today_attendance': Attendance.objects.filter(date=timezone.now().date()).count(),        
        }
        return render(request, 'accounts/dashboard_admin.html', {'data' : data})
    elif user.role == 'teacher':
        from school.models import Exam, LeaveRequest, OTRequest
        from django.utils import timezone

        teacher = user.teacher_profile
        
        data = {
            'exam_count': Exam.objects.filter(created_by=teacher).count(),
            'leave_balance': teacher.leave_balance,
            'pending_leaves': LeaveRequest.objects.filter(teacher=teacher, status='pending').count(),
            'pending_ots': OTRequest.objects.filter(teacher=teacher, status='pending').count(),
        }
        return render(request, 'accounts/dashboard_teacher.html', {'data': data})
        
    

        student = user.student_profile
        total = Attendance.objects.filter(student=student).count()
        present = Attendance.objects.filter(student=student, status='present').count()
        percentage = round((present / total * 100), 1) if total > 0 else 0

        data = {
            'total_days': total,
            'present_days': present,
            'attendance_pct': percentage,
            'results_count': Mark.objects.filter(student=student).count(),
            'upcoming_exams': Exam.objects.filter(
                class_name=student.class_name,
                section=student.section,
                exam_date__gte=timezone.now().date()
            ).count(),
        }
        return render(request, 'accounts/dashboard_student.html', {'data': data})

    else:
        return render(request, 'accounts/dashboard_admin.html', {'data': {}})


        
    
    
    
    