"""
Analytics services — aggregation queries for statistics.
All computations are done at DB level via annotations/aggregations.
"""
from datetime import date, timedelta

from django.db.models import Count, Q

from apps.attendance.models import Attendance, AttendanceStatus
from apps.groups.models import Group
from apps.schedules.models import Schedule, Semester


def get_group_stats_for_period(group: Group, start_date: date, end_date: date) -> dict:
    qs = Attendance.objects.filter(
        student__group=group,
        date__range=(start_date, end_date),
    )
    return qs.aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
        late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
    )


def get_group_stats_for_day(group: Group, target_date: date) -> dict:
    return get_group_stats_for_period(group, target_date, target_date)


def get_group_stats_for_week(group: Group, target_date: date) -> dict:
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return get_group_stats_for_period(group, monday, sunday)


def get_group_stats_for_month(group: Group, target_date: date) -> dict:
    start = target_date.replace(day=1)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    end = next_month - timedelta(days=1)
    return get_group_stats_for_period(group, start, end)


def get_group_stats_for_semester(group: Group, semester: Semester) -> dict:
    return get_group_stats_for_period(group, semester.start_date, semester.end_date)


def get_student_stats(student, semester: Semester) -> dict:
    return Attendance.objects.filter(
        student=student,
        schedule__semester=semester,
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
        late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
    )


def get_subject_stats_for_teacher(teacher, semester: Semester) -> list[dict]:
    schedules = Schedule.objects.filter(teacher=teacher, semester=semester).select_related('subject', 'group')
    results = []
    for schedule in schedules:
        stats = Attendance.objects.filter(schedule=schedule).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        )
        results.append({
            'schedule': schedule,
            'subject': schedule.subject.name,
            'group': str(schedule.group),
            **stats,
        })
    return results


# ─── Admin analytics ──────────────────────────────────────────────────────────

def get_attendance_by_group(semester: Semester) -> list[dict]:
    """Attendance rate per group for the whole semester."""
    groups = Group.objects.order_by('course', 'name')
    result = []
    for g in groups:
        stats = Attendance.objects.filter(
            student__group=g,
            schedule__semester=semester,
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        )
        total = stats['total'] or 0
        present = stats['present'] or 0
        rate = round(present / total * 100, 1) if total > 0 else 0
        result.append({'group': g.name, 'rate': rate, 'total': total})
    return result


def get_weekly_attendance_trend(weeks: int = 8) -> dict:
    """Attendance present/absent counts for the last N weeks."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    labels, present_data, absent_data = [], [], []

    for i in range(weeks - 1, -1, -1):
        week_start = monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=5)
        stats = Attendance.objects.filter(
            date__range=(week_start, week_end),
        ).aggregate(
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status__in=[AttendanceStatus.ABSENT, AttendanceStatus.LATE])),
        )
        labels.append(week_start.strftime('%d.%m'))
        present_data.append(stats['present'] or 0)
        absent_data.append(stats['absent'] or 0)

    return {'labels': labels, 'present': present_data, 'absent': absent_data}


def get_status_distribution() -> dict:
    """Overall attendance status distribution."""
    stats = Attendance.objects.aggregate(
        present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
        late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
    )
    return stats


# ─── Starosta analytics ───────────────────────────────────────────────────────

def get_student_stats_bulk(group, semester: Semester) -> list[dict]:
    """Per-student attendance stats for the whole semester (one query per student)."""
    from apps.groups.models import Student
    students = Student.objects.filter(group=group, is_active=True).order_by('full_name')
    result = []
    for student in students:
        stats = Attendance.objects.filter(
            student=student,
            schedule__semester=semester,
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
            excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
            late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
        )
        total = stats['total'] or 0
        present = stats['present'] or 0
        rate = round(present / total * 100, 1) if total > 0 else 0
        result.append({'student': student, 'rate': rate, **stats})
    return result


def get_group_weekly_trend(group, weeks: int = 8) -> dict:
    """Weekly attendance present/absent counts for a specific group."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    labels, present_data, absent_data = [], [], []

    for i in range(weeks - 1, -1, -1):
        week_start = monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=5)
        stats = Attendance.objects.filter(
            student__group=group,
            date__range=(week_start, week_end),
        ).aggregate(
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status__in=[AttendanceStatus.ABSENT, AttendanceStatus.LATE])),
        )
        labels.append(week_start.strftime('%d.%m'))
        present_data.append(stats['present'] or 0)
        absent_data.append(stats['absent'] or 0)

    return {'labels': labels, 'present': present_data, 'absent': absent_data}


def get_teacher_weekly_trend(teacher, weeks: int = 8) -> dict:
    """Weekly attendance present/absent counts for a specific teacher's lessons."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    labels, present_data, absent_data = [], [], []

    for i in range(weeks - 1, -1, -1):
        week_start = monday - timedelta(weeks=i)
        week_end = week_start + timedelta(days=5)
        stats = Attendance.objects.filter(
            schedule__teacher=teacher,
            date__range=(week_start, week_end),
        ).aggregate(
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status__in=[AttendanceStatus.ABSENT, AttendanceStatus.LATE])),
        )
        labels.append(week_start.strftime('%d.%m'))
        present_data.append(stats['present'] or 0)
        absent_data.append(stats['absent'] or 0)

    return {'labels': labels, 'present': present_data, 'absent': absent_data}
