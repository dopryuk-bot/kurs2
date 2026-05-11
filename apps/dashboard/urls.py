from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.dashboard.views.admin_views import AdminDashboardView
from apps.dashboard.views.starosta_views import StarostaDashboardView
from apps.dashboard.views.teacher_views import TeacherDashboardView

app_name = 'dashboard'


class RoleRedirectView(LoginRequiredMixin, RedirectView):
    """Redirects authenticated users to their role-specific dashboard."""

    def get_redirect_url(self, *args, **kwargs):
        return self.request.user.get_dashboard_url()


admin_urlpatterns = ([
    path('', AdminDashboardView.as_view(), name='index'),
], 'admin')

teacher_urlpatterns = ([
    path('', TeacherDashboardView.as_view(), name='index'),
], 'teacher')

starosta_urlpatterns = ([
    path('', StarostaDashboardView.as_view(), name='index'),
], 'starosta')

urlpatterns = [
    path('', RoleRedirectView.as_view(), name='index'),
    path('admin-panel/', include(admin_urlpatterns, namespace='admin')),
    path('teacher/', include(teacher_urlpatterns, namespace='teacher')),
    path('starosta/', include(starosta_urlpatterns, namespace='starosta')),
]
