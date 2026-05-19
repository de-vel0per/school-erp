from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Attendance, Exam, Mark, LeaveRequest, OTRequest
import json

from accounts.models import User, Teacher, Student
from .models import Attendance

def admin_required(view_func):
    """decorator that checks the user is an admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            messages.error(request, 'Only admins can access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    """decorator that checks the user is a teacher or admin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role not in ['teacher', 'admin']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """decorator that checks the user is a student"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'student':
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@teacher_required
def attendance_view(request):
    """shows list of classes and today's attendance summary"""
    # get all unique classes from students
    classes = Student.objects.values('class_name', 'section').distinct().order_by('class_name', 'section')

    today = timezone.now().date()

    # for each class calculate today's attendance stats
    class_stats = []
    for c in classes:
        total = Student.objects.filter(
            class_name=c['class_name'],
            section=c['section']
        ).count()

        present = Attendance.objects.filter(
            date=today,
            status='present',
            student__class_name=c['class_name'],
            student__section=c['section']
        ).count()

        class_stats.append({
            'class_name': c['class_name'],
            'section': c['section'],
            'total': total,
            'present': present,
            'absent': total - present,
        })

    return render(request, 'school/attendance.html', {
        'class_stats': class_stats,
        'today': today,
    })


@login_required
@teacher_required
def mark_attendance_view(request):
    """teacher marks attendance for a specific class on a specific date"""
    class_name = request.GET.get('class_name', '')
    section = request.GET.get('section', '')
    date_str = request.GET.get('date', timezone.now().date().isoformat())

    try:
        selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    students = Student.objects.filter(
        class_name=class_name,
        section=section
    ).select_related('user').order_by('roll_number')

    # get existing attendance records for this class and date
    existing = {}
    for att in Attendance.objects.filter(date=selected_date, student__in=students):
        existing[att.student_id] = att

    if request.method == 'POST':
        class_name = request.POST.get('class_name')
        section = request.POST.get('section')
        date_str = request.POST.get('date')
        selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()

        students = Student.objects.filter(class_name=class_name, section=section)

        teacher = None
        if request.user.role == 'teacher':
            teacher = request.user.teacher_profile

        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
            remarks = request.POST.get(f'remarks_{student.id}', '')

            if student.id in existing:
                # update existing record
                att = existing[student.id]
                att.status = status
                att.remarks = remarks
                att.marked_by = teacher
                att.save()
            else:
                # create new record
                Attendance.objects.create(
                    student=student,
                    date=selected_date,
                    status=status,
                    remarks=remarks,
                    marked_by=teacher,
                    time_in=timezone.now().time()
                )

        messages.success(request, f'Attendance marked for Class {class_name} {section} on {selected_date}.')
        return redirect('attendance')

    return render(request, 'school/mark_attendance.html', {
        'students': students,
        'existing': existing,
        'class_name': class_name,
        'section': section,
        'selected_date': selected_date,
    })


@login_required
@student_required
def my_attendance_view(request):
    """student views their own attendance records"""
    student = request.user.student_profile
    records = Attendance.objects.filter(student=student).order_by('-date')

    total = records.count()
    present = records.filter(status='present').count()
    absent = records.filter(status='absent').count()
    late = records.filter(status='late').count()
    percentage = round((present / total * 100), 1) if total > 0 else 0

    return render(request, 'school/my_attendance.html', {
        'records': records,
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'percentage': percentage,
    })


@csrf_exempt
def biometric_login_view(request):
    """called by the biometric machine when a student scans their finger or card"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            biometric_id = data.get('biometric_id')

            student = Student.objects.select_related('user').get(biometric_id=biometric_id)
            user = student.user

            if not user.is_active:
                return JsonResponse({'success': False, 'message': 'Account is inactive.'})

            today = timezone.now().date()

            # check if already marked today
            already_marked = Attendance.objects.filter(
                student=student,
                date=today
            ).exists()

            if not already_marked:
                Attendance.objects.create(
                    student=student,
                    date=today,
                    status='present',
                    biometric_verified=True,
                    time_in=timezone.now().time()
                )
                message = f'Attendance marked for {user.get_full_name()}'
            else:
                message = f'Already marked for {user.get_full_name()} today'

            return JsonResponse({
                'success': True,
                'message': message,
                'student_name': user.get_full_name(),
                'student_id': student.student_id,
            })

        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Biometric ID not recognized.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
def calculate_grade(marks_obtained, total_marks):
    """converts a mark into a letter grade"""
    percentage = (marks_obtained / total_marks) * 100

    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    else:
        return 'F'


@login_required
@teacher_required
def exams_view(request):
    """shows all exams — teachers see their own, admins see all"""
    if request.user.role == 'admin':
        all_exams = Exam.objects.select_related('created_by__user').all()
    else:
        teacher = request.user.teacher_profile
        all_exams = Exam.objects.select_related('created_by__user').filter(created_by=teacher)

    return render(request, 'school/exams.html', {
        'exams': all_exams,
    })


@login_required
@teacher_required
def create_exam_view(request):
    """teacher fills a form to create a new exam"""
    if request.method == 'POST':
        title = request.POST.get('title')
        subject = request.POST.get('subject')
        class_name = request.POST.get('class_name')
        section = request.POST.get('section')
        exam_date = request.POST.get('exam_date')
        duration_mins = request.POST.get('duration_mins', 60)
        total_marks = request.POST.get('total_marks', 100)
        pass_marks = request.POST.get('pass_marks', 40)
        instructions = request.POST.get('instructions', '')

        teacher = request.user.teacher_profile

        exam = Exam.objects.create(
            title=title,
            subject=subject,
            class_name=class_name,
            section=section,
            exam_date=exam_date,
            duration_mins=duration_mins,
            total_marks=total_marks,
            pass_marks=pass_marks,
            instructions=instructions,
            created_by=teacher,
        )

        messages.success(request, f'Exam "{title}" created successfully!')
        return redirect('exam_detail', exam_id=exam.id)

    # for GET request — show available classes to pick from
    classes = Student.objects.values('class_name', 'section').distinct().order_by('class_name', 'section')

    return render(request, 'school/create_exam.html', {
        'classes': classes,
    })


@login_required
def exam_detail_view(request, exam_id):
    """shows exam details — teachers see marks sheet, students see their result"""
    exam = Exam.objects.get(id=exam_id)

    if request.user.role == 'student':
        student = request.user.student_profile
        # student can only see their own mark
        try:
            mark = Mark.objects.get(student=student, exam=exam)
        except Mark.DoesNotExist:
            mark = None
        return render(request, 'school/exam_detail_student.html', {
            'exam': exam,
            'mark': mark,
        })

    # teacher or admin sees all students marks
    marks = Mark.objects.filter(exam=exam).select_related('student__user')
    students_with_marks = {m.student_id: m for m in marks}

    # get all students in this class
    students = Student.objects.filter(
        class_name=exam.class_name,
        section=exam.section
    ).select_related('user').order_by('roll_number')

    return render(request, 'school/exam_detail_teacher.html', {
        'exam': exam,
        'students': students,
        'students_with_marks': students_with_marks,
    })


@login_required
@teacher_required
def upload_marks_view(request, exam_id):
    """teacher enters marks for each student in the exam"""
    exam = Exam.objects.get(id=exam_id)
    teacher = request.user.teacher_profile

    students = Student.objects.filter(
        class_name=exam.class_name,
        section=exam.section
    ).select_related('user').order_by('roll_number')

    # get already uploaded marks
    existing_marks = {}
    for mark in Mark.objects.filter(exam=exam):
        existing_marks[mark.student_id] = mark

    if request.method == 'POST':
        for student in students:
            marks_value = request.POST.get(f'marks_{student.id}', '').strip()
            remarks = request.POST.get(f'remarks_{student.id}', '').strip()

            # skip if teacher left the field empty
            if not marks_value:
                continue

            marks_float = float(marks_value)
            grade = calculate_grade(marks_float, exam.total_marks)

            if student.id in existing_marks:
                # update existing
                m = existing_marks[student.id]
                m.marks_obtained = marks_float
                m.grade = grade
                m.remarks = remarks
                m.checked_by = teacher
                m.save()
            else:
                # create new
                Mark.objects.create(
                    student=student,
                    exam=exam,
                    marks_obtained=marks_float,
                    grade=grade,
                    remarks=remarks,
                    checked_by=teacher,
                )

        # mark exam as completed
        exam.status = 'completed'
        exam.save()

        messages.success(request, 'Marks uploaded successfully!')
        return redirect('exam_detail', exam_id=exam.id)

    return render(request, 'school/upload_marks.html', {
        'exam': exam,
        'students': students,
        'existing_marks': existing_marks,
    })


@login_required
@student_required
def my_results_view(request):
    """student sees all their results across all exams"""
    student = request.user.student_profile
    marks = Mark.objects.filter(
        student=student
    ).select_related('exam').order_by('-exam__exam_date')

    return render(request, 'school/my_results.html', {
        'marks': marks,
    })


# ── Leave Views ────────────────────────────────────────────────

@login_required
@teacher_required
def leave_list_view(request):
    """
    Teachers see their own leave requests.
    Admins see all leave requests from all teachers.
    """
    if request.user.role == 'admin':
        leaves = LeaveRequest.objects.select_related(
            'teacher__user'
        ).all()
    else:
        teacher = request.user.teacher_profile
        leaves = LeaveRequest.objects.filter(teacher=teacher)

    return render(request, 'school/leave_list.html', {
        'leaves': leaves,
    })


@login_required
@teacher_required
def apply_leave_view(request):
    """teacher fills a form to apply for leave"""
    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        reason = request.POST.get('reason')

        teacher = request.user.teacher_profile

        # check leave balance before applying
        from datetime import datetime
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        days_requested = (to_date_obj - from_date_obj).days + 1

        if days_requested > teacher.leave_balance:
            messages.error(
                request,
                f'You only have {teacher.leave_balance} days of leave balance but requested {days_requested} days.'
            )
            return redirect('apply_leave')

        if to_date_obj < from_date_obj:
            messages.error(request, 'End date cannot be before start date.')
            return redirect('apply_leave')

        LeaveRequest.objects.create(
            teacher=teacher,
            leave_type=leave_type,
            from_date=from_date,
            to_date=to_date,
            reason=reason,
        )

        messages.success(request, f'Leave request submitted for {days_requested} day(s). Waiting for approval.')
        return redirect('leave_list')

    return render(request, 'school/apply_leave.html')


@login_required
@admin_required
def review_leave_view(request, leave_id):
    """admin approves or rejects a leave request"""
    leave = LeaveRequest.objects.select_related('teacher__user').get(id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')  # 'approve' or 'reject'
        admin_remarks = request.POST.get('admin_remarks', '')

        if action == 'approve':
            leave.status = 'approved'

            # deduct days from teacher leave balance
            teacher = leave.teacher
            teacher.leave_balance -= leave.total_days
            teacher.save()

            messages.success(request, f'Leave approved. {leave.total_days} day(s) deducted from balance.')

        elif action == 'reject':
            leave.status = 'rejected'
            messages.success(request, 'Leave request rejected.')

        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.admin_remarks = admin_remarks
        leave.save()

        return redirect('leave_list')

    return render(request, 'school/review_leave.html', {
        'leave': leave,
    })


# ── OT Views ───────────────────────────────────────────────────

@login_required
@teacher_required
def ot_list_view(request):
    """
    Teachers see their own OT requests.
    Admins see all OT requests.
    """
    if request.user.role == 'admin':
        ots = OTRequest.objects.select_related('teacher__user').all()
    else:
        teacher = request.user.teacher_profile
        ots = OTRequest.objects.filter(teacher=teacher)

    return render(request, 'school/ot_list.html', {
        'ots': ots,
    })


@login_required
@teacher_required
def apply_ot_view(request):
    """teacher fills a form to apply for overtime"""
    if request.method == 'POST':
        ot_date = request.POST.get('ot_date')
        hours = request.POST.get('hours')
        reason = request.POST.get('reason')

        teacher = request.user.teacher_profile

        # check if OT already applied for this date
        from datetime import datetime
        ot_date_obj = datetime.strptime(ot_date, '%Y-%m-%d').date()

        already_applied = OTRequest.objects.filter(
            teacher=teacher,
            ot_date=ot_date_obj
        ).exists()

        if already_applied:
            messages.error(request, 'You have already applied for OT on this date.')
            return redirect('apply_ot')

        OTRequest.objects.create(
            teacher=teacher,
            ot_date=ot_date,
            hours=float(hours),
            reason=reason,
        )

        messages.success(request, f'OT request submitted for {hours} hour(s) on {ot_date}.')
        return redirect('ot_list')

    return render(request, 'school/apply_ot.html')


@login_required
@admin_required
def review_ot_view(request, ot_id):
    """admin approves or rejects an OT request"""
    ot = OTRequest.objects.select_related('teacher__user').get(id=ot_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        admin_remarks = request.POST.get('admin_remarks', '')

        if action == 'approve':
            ot.status = 'approved'
            messages.success(request, f'OT approved for {ot.hours} hour(s).')
        elif action == 'reject':
            ot.status = 'rejected'
            messages.success(request, 'OT request rejected.')

        ot.reviewed_by = request.user
        ot.reviewed_at = timezone.now()
        ot.admin_remarks = admin_remarks
        ot.save()

        return redirect('ot_list')

    return render(request, 'school/review_ot.html', {
        'ot': ot,
    })