import json
from datetime import date, timedelta

from django.db.models import Count, Q
from django.views.generic import TemplateView

from apps.accounts.models import Role, User
from apps.attendance.models import Attendance, AttendanceStatus
from apps.groups.models import Group, Student
from apps.schedules.models import Schedule
from apps.schedules.services import get_active_semester
from core.mixins import AdminRequiredMixin


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/admin/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = get_active_semester()
        today = date.today()

        ctx['semester'] = semester
        ctx['groups_count'] = Group.objects.count()
        ctx['students_count'] = Student.objects.filter(is_active=True).count()
        ctx['teachers_count'] = User.objects.filter(role=Role.TEACHER, is_active=True).count()
        ctx['starostas_count'] = User.objects.filter(role=Role.STAROSTA, is_active=True).count()
        ctx['today_lessons_count'] = (
            Schedule.objects.filter(semester=semester, weekday=today.weekday()).count()
            if semester else 0
        )

        today_att = Attendance.objects.filter(date=today)
        ctx['today_att_total'] = today_att.count()
        ctx['today_att_present'] = today_att.filter(status=AttendanceStatus.PRESENT).count()

        # Weekly attendance trend (last 6 weeks)
        monday = today - timedelta(days=today.weekday())
        trend_labels, trend_present, trend_absent = [], [], []
        for i in range(5, -1, -1):
            w_start = monday - timedelta(weeks=i)
            w_end = w_start + timedelta(days=5)
            stats = Attendance.objects.filter(date__range=(w_start, w_end)).aggregate(
                present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
                absent=Count('id', filter=Q(status__in=[AttendanceStatus.ABSENT, AttendanceStatus.LATE])),
            )
            trend_labels.append(w_start.strftime('%d.%m'))
            trend_present.append(stats['present'] or 0)
            trend_absent.append(stats['absent'] or 0)

        ctx['chart_labels'] = json.dumps(trend_labels)
        ctx['chart_present'] = json.dumps(trend_present)
        ctx['chart_absent'] = json.dumps(trend_absent)

        ctx['recent_groups'] = (
            Group.objects.annotate(
                active_student_count=Count('students', filter=Q(students__is_active=True))
            ).order_by('-created_at')[:6]
        )

        return ctx
