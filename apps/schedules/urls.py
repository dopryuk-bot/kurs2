from django.urls import path

from apps.schedules import views

app_name = 'schedules'

urlpatterns = [
    # ── Role-specific weekly timetable ────────────────────────────────────────
    path('starosta/week/', views.StarostaScheduleView.as_view(), name='starosta_week'),
    path('teacher/week/', views.TeacherScheduleView.as_view(), name='teacher_week'),
    path('admin/timetable/', views.AdminTimetableView.as_view(), name='admin_timetable'),
    path('admin/general/', views.AdminGeneralTimetableView.as_view(), name='admin_general'),

    # ── Semester management (admin only) ──────────────────────────────────────
    path('admin/semesters/', views.SemesterListView.as_view(), name='semester_list'),
    path('admin/semesters/create/', views.SemesterCreateView.as_view(), name='semester_create'),
    path('admin/semesters/<int:pk>/edit/', views.SemesterUpdateView.as_view(), name='semester_edit'),
    path('admin/semesters/<int:pk>/delete/', views.SemesterDeleteView.as_view(), name='semester_delete'),


    # ── Subject management (admin only) ───────────────────────────────────────
    path('admin/subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('admin/subjects/create/', views.SubjectCreateView.as_view(), name='subject_create'),
    path('admin/subjects/<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='subject_edit'),
    path('admin/subjects/<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    # ── Schedule management (admin only) ──────────────────────────────────────
    path('admin/schedule/', views.ScheduleListView.as_view(), name='schedule_list'),
    path('admin/schedule/create/', views.ScheduleCreateView.as_view(), name='schedule_create'),
    path('admin/schedule/<int:pk>/edit/', views.ScheduleUpdateView.as_view(), name='schedule_edit'),
    path('admin/schedule/<int:pk>/delete/', views.ScheduleDeleteView.as_view(), name='schedule_delete'),
]
