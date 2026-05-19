from django.db import models
from accounts.models import Teacher, Student, User
from django.utils import timezone


class Attendance(models.Model):
    STATUS_CHOICES = (
            ('present', 'Present'),
            ('absent', 'Absent'),
            ('late', 'Late'),
            )
            
            
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    biometric_verified = models.BooleanField(default=False)
    time_in = models.TimeField(null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"

class Exam(models.Model):
    STATUS_CHOICES = (
            ('scheduled', 'Scheduled'),
            ('ongoing', 'Ongoing'),
            ('completed', 'Completed'),   
    
    )
    title = models.CharField(max_length=200)
    subject = models.CharField(max_length=100)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    exam_date = models.DateField()
    duration_mins = models.IntegerField(default=60)
    total_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=40)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='exams')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-exam_date']
        
    def __str__(self):
        return f"{self.title} - Class {self.class_name} {self.section}"
        
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.FloatField()
    grade = models.CharField(max_length=5, blank=True)
    remarks = models.TextField(blank=True)
    checked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='checked_marks')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # one mark record per student per exam
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student} — {self.exam.title} — {self.marks_obtained}"
        
class LeaveRequest(models.Model):
    LEAVE_TYPE_CHOICES = (
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('emergency', 'Emergency Leave'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPE_CHOICES)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.teacher} — {self.leave_type} — {self.status}"

    @property
    def total_days(self):
        return (self.to_date - self.from_date).days + 1


class OTRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='ot_requests')
    ot_date = models.DateField()
    hours = models.FloatField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_ots')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.teacher} — {self.ot_date} — {self.hours} hrs — {self.status}"