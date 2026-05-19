from django.urls import path
from . import views

urlpatterns = [
     path('attendance/', views.attendance_view, name='attendance'),
     path('attendance/mark/', views.mark_attendance_view, name='mark_attendance'),
     path('attendance/my/', views.my_attendance_view, name='my_attendance'),
     
     path('biometric-login/', views.biometric_login_view, name='biometric-login'),
     path('exams/', views.exams_view, name='exams'),
     path('exams/create/', views.create_exam_view, name='create_exam'),
     path('exams/<int:exam_id>/', views.exam_detail_view, name='exam_detail'),
     path('exams/<int:exam_id>/upload-marks/', views.upload_marks_view, name='upload_marks'),

    # student results
     path('my-results/', views.my_results_view, name='my_results'),
     
     
    # leave
    path('leave/', views.leave_list_view, name='leave_list'),
    path('leave/apply/', views.apply_leave_view, name='apply_leave'),
    path('leave/<int:leave_id>/review/', views.review_leave_view, name='review_leave'),

    # ot
    path('ot/', views.ot_list_view, name='ot_list'),
    path('ot/apply/', views.apply_ot_view, name='apply_ot'),
    path('ot/<int:ot_id>/review/', views.review_ot_view, name='review_ot'),

]
      