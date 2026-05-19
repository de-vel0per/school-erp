from django.contrib import admin
from .models import Attendance, Exam, Mark, LeaveRequest, OTRequest

admin.site.register(Attendance)
admin.site.register(Exam)
admin.site.register(Mark)
admin.site.register(LeaveRequest)
admin.site.register(OTRequest)
