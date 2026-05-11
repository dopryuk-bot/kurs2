from django.urls import path

from apps.accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Teacher management
    path('teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('teachers/create/', views.TeacherCreateView.as_view(), name='teacher_create'),
    path('teachers/<int:pk>/edit/', views.TeacherUpdateView.as_view(), name='teacher_edit'),
    path('teachers/<int:pk>/delete/', views.TeacherDeleteView.as_view(), name='teacher_delete'),

    # Starosta management
    path('starostas/', views.StarostaListView.as_view(), name='starosta_list'),
    path('starostas/create/', views.StarostaCreateView.as_view(), name='starosta_create'),
    path('starostas/<int:pk>/edit/', views.StarostaUpdateView.as_view(), name='starosta_edit'),
    path('starostas/<int:pk>/delete/', views.StarostaDeleteView.as_view(), name='starosta_delete'),
]
