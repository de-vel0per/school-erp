from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Teacher, Student


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ( ('School Info', {'fields': ('role', 'phone', 'profile_photo')}),)
    
admin.site.register(User, CustomUserAdmin)
admin.site.register(Teacher)
admin.site.register(Student)
