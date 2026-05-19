from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to = 'profiles/', blank=True, null=True)
    groups = models.ManyToManyField('auth.Group', related_name='account_Users', blank=True)
    user_permission = models.ManyToManyField('auth.Permission', related_name='account_Users', blank=True)
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.role})"
        
        
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    join_date = models.DateField()
    leave_balance = models.IntegerField(default=20)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"
        

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    biometric_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    class_name = models.CharField(max_length=50)
    section = models.CharField(max_length=10)
    roll_number = models.IntegerField()
    parent_name = models.CharField(max_length=120)
    parent_phone = models.CharField(max_length=20)
    admission_date = models.DateField()
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Class {self.class_name} : {self.section}"