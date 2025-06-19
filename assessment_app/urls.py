from django.contrib import admin
from django.urls import path
from assessments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.department_list, name='department_list'),
    path('departments/<int:department_id>/', views.job_title_list, name='job_title_list'),
    path('job_titles/<int:job_title_id>/', views.competency_list, name='competency_list'),
    path('start_interview/<int:competency_id>/', views.start_interview, name='start_interview'),
    path('interview_question/<int:session_id>/', views.interview_question, name='interview_question'),
    path('interview_complete/<int:session_id>/', views.interview_complete, name='interview_complete'),
    path('feedback_report/<int:session_id>/', views.feedback_report, name='feedback_report'),
    path('live_feedback/', views.live_feedback, name='live_feedback'),
]