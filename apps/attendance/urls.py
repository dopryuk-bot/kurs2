from datetime import date

from django.urls import path, register_converter

from apps.attendance import views


class DateConverter:
    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        return date.fromisoformat(value)

    def to_url(self, value):
        if isinstance(value, str):
            return value
        return value.isoformat()


register_converter(DateConverter, 'date')

app_name = 'attendance'

urlpatterns = [
    path('history/', views.history_view, name='history'),
    path(
        'session/<int:schedule_id>/<date:lesson_date>/',
        views.session_view,
        name='session',
    ),
    path(
        'session/<int:schedule_id>/<date:lesson_date>/update/',
        views.update_status_ajax,
        name='update_status',
    ),
]
