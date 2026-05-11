from django.urls import path

from apps.groups import views

app_name = 'groups'

urlpatterns = [
    path('', views.GroupListView.as_view(), name='list'),
    path('create/', views.GroupCreateView.as_view(), name='create'),
    path('<int:pk>/', views.GroupDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.GroupUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.GroupDeleteView.as_view(), name='delete'),

    # Student management
    path('<int:group_pk>/students/add/', views.StudentCreateView.as_view(), name='student_add'),
    path('<int:group_pk>/students/bulk/', views.BulkStudentCreateView.as_view(), name='student_bulk'),
    path('<int:group_pk>/students/<int:student_pk>/edit/', views.StudentUpdateView.as_view(), name='student_edit'),
    path('<int:group_pk>/students/<int:student_pk>/delete/', views.StudentDeleteView.as_view(), name='student_delete'),
]
