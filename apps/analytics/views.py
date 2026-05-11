import json
from datetime import date

from django.views.generic import TemplateView

from apps.analytics import services
from apps.schedules.services import get_active_semester
from core.mixins import AdminRequiredMixin, StarostaRequiredMixin, TeacherRequiredMixin


class StarostaAnalyticsView(StarostaRequiredMixin, TemplateView):
    template_name = 'analytics/starosta.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        group = self.request.user.starosta_profile.group
        semester = get_active_semester()
        today = date.today()

        ctx['group'] = group
        ctx['semester'] = semester

        if semester:
            ctx['stats_day'] = services.get_group_stats_for_day(group, today)
            ctx['stats_week'] = services.get_group_stats_for_week(group, today)
            ctx['stats_month'] = services.get_group_stats_for_month(group, today)
            stats_sem = services.get_group_stats_for_semester(group, semester)
            ctx['stats_semester'] = stats_sem

            trend = services.get_group_weekly_trend(group, weeks=8)
            ctx['chart_labels'] = json.dumps(trend['labels'])
            ctx['chart_present'] = json.dumps(trend['present'])
            ctx['chart_absent'] = json.dumps(trend['absent'])

            ctx['student_stats'] = services.get_student_stats_bulk(group, semester)

            ctx['chart_dist_data'] = json.dumps([
                stats_sem['present'] or 0,
                stats_sem['absent'] or 0,
                stats_sem['excused'] or 0,
                stats_sem['late'] or 0,
            ])

        return ctx


class TeacherAnalyticsView(TeacherRequiredMixin, TemplateView):
    template_name = 'analytics/teacher.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = get_active_semester()

        if semester:
            subject_stats = services.get_subject_stats_for_teacher(
                self.request.user, semester
            )
            ctx['subject_stats'] = subject_stats

            # Weekly trend for Chart.js
            trend = services.get_teacher_weekly_trend(self.request.user, weeks=8)
            ctx['chart_labels'] = json.dumps(trend['labels'])
            ctx['chart_present'] = json.dumps(trend['present'])
            ctx['chart_absent'] = json.dumps(trend['absent'])

            # Overall stats (sum of all schedules)
            total, present, absent = 0, 0, 0
            for stat in subject_stats:
                total += stat.get('total', 0)
                present += stat.get('present', 0)
                absent += stat.get('absent', 0)

            ctx['stats_total'] = total
            ctx['stats_present'] = present
            ctx['stats_absent'] = absent
            ctx['stats_rate'] = round(present / total * 100, 1) if total > 0 else 0

        ctx['semester'] = semester
        return ctx


class AdminAnalyticsView(AdminRequiredMixin, TemplateView):
    template_name = 'analytics/admin.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        semester = get_active_semester()
        ctx['semester'] = semester

        if semester:
            by_group = services.get_attendance_by_group(semester)
            ctx['groups_with_data'] = [g for g in by_group if g['total'] > 0]
            # Chart.js data
            ctx['chart_group_labels'] = json.dumps([g['group'] for g in by_group])
            ctx['chart_group_rates'] = json.dumps([g['rate'] for g in by_group])

        trend = services.get_weekly_attendance_trend(weeks=8)
        ctx['chart_trend_labels'] = json.dumps(trend['labels'])
        ctx['chart_trend_present'] = json.dumps(trend['present'])
        ctx['chart_trend_absent'] = json.dumps(trend['absent'])

        dist = services.get_status_distribution()
        ctx['dist_present'] = dist['present'] or 0
        ctx['dist_absent'] = dist['absent'] or 0
        ctx['dist_excused'] = dist['excused'] or 0
        ctx['dist_late'] = dist['late'] or 0
        ctx['chart_dist_data'] = json.dumps([
            dist['present'] or 0, dist['absent'] or 0,
            dist['excused'] or 0, dist['late'] or 0,
        ])

        return ctx
