from datetime import date

from apps.schedules import services
from apps.schedules.services.semester import get_week_info
from core.mixins import StarostaRequiredMixin
from django.views.generic import TemplateView


class StarostaDashboardView(StarostaRequiredMixin, TemplateView):
    template_name = 'dashboard/starosta/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        semester = services.get_active_semester()
        today = date.today()

        try:
            group = user.starosta_profile.group
        except Exception:
            group = None

        if semester and group:
            week_info = get_week_info(today, semester)
            week_type = week_info.get('week_type')
            if week_type:
                schedules = services.get_schedules_for_group(group, semester, week_type)
                calendar_data = services.build_timetable_context(schedules, today, semester)
                context.update(calendar_data)

            from apps.attendance import services as att_services
            context['today_sessions'] = att_services.get_today_sessions(group, today, semester)
            context['group'] = group

        context['semester'] = semester
        return context
