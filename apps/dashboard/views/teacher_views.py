from datetime import date

from apps.schedules import services
from apps.schedules.services.semester import get_week_info
from apps.attendance import services as att_services
from apps.analytics import services as analytics_services
from core.mixins import TeacherRequiredMixin
from django.views.generic import TemplateView


class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = 'dashboard/teacher/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        semester = services.get_active_semester()
        today = date.today()

        if semester:
            week_info = get_week_info(today, semester)
            week_type = week_info.get('week_type')
            if week_type:
                schedules = services.get_schedules_for_teacher(
                    self.request.user, semester, week_type
                )
                calendar_data = services.build_timetable_context(schedules, today, semester)
                context.update(calendar_data)

            # Today's sessions widget
            context['today_sessions'] = att_services.get_teacher_today_sessions(
                self.request.user, today, semester
            )

            # Subject statistics (top 5 subjects)
            subject_stats = analytics_services.get_subject_stats_for_teacher(
                self.request.user, semester
            )
            context['subject_stats'] = subject_stats[:5]

        context['semester'] = semester
        return context
