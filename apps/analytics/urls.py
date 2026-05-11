from django.urls import path

from apps.analytics import views

app_name = 'analytics'

urlpatterns = [
    path('admin/', views.AdminAnalyticsView.as_view(), name='admin'),
    path('starosta/', views.StarostaAnalyticsView.as_view(), name='starosta'),
    path('teacher/', views.TeacherAnalyticsView.as_view(), name='teacher'),
]
