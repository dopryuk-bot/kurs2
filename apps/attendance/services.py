"""
Attendance domain services.

Core responsibility: creating and managing attendance sessions (bulk records per lesson).
All DB writes go through these functions to keep business rules centralized.
"""
from datetime import date

from django.db import transaction

from apps.attendance.models import Attendance, AttendanceStatus
from apps.groups.models import Student
from apps.schedules.models import Schedule


def get_or_create_session(schedule: Schedule, lesson_date: date, created_by) -> tuple[list, bool]:
    """
    Retrieves or initializes attendance records for all active students in a group.
    Returns (queryset_of_records, created: bool).

    On first access, bulk-creates records with PRESENT status.
    Subsequent calls return existing records without modification.
    """
    existing_records = Attendance.objects.filter(
        schedule=schedule,
        date=lesson_date,
    ).select_related('student')

    if existing_records.exists():
        return existing_records, False

    students = Student.objects.filter(
        group=schedule.group,
        is_active=True,
        **({'subgroup': schedule.subgroup} if schedule.subgroup else {}),
    ).order_by('full_name')

    with transaction.atomic():
        records = Attendance.objects.bulk_create([
            Attendance(
                student=student,
                schedule=schedule,
                date=lesson_date,
                status=AttendanceStatus.PRESENT,
                marked_by=created_by,
            )
            for student in students
        ])

    return Attendance.objects.filter(schedule=schedule, date=lesson_date).select_related('student'), True


def update_attendance_status(
    schedule: Schedule,
    lesson_date: date,
    student_id: int,
    status: str,
    updated_by,
) -> Attendance:
    """
    Updates a single student's attendance status.
    Raises Attendance.DoesNotExist if the session has not been initialized.
    Raises ValueError for invalid status values.
    """
    if status not in AttendanceStatus.values:
        raise ValueError(f'Invalid status: {status}. Must be one of {AttendanceStatus.values}')

    record = Attendance.objects.get(
        schedule=schedule,
        date=lesson_date,
        student_id=student_id,
    )
    record.status = status
    record.marked_by = updated_by
    record.save(update_fields=['status', 'marked_by', 'updated_at'])
    return record


def get_session_summary(schedule: Schedule, lesson_date: date) -> dict:
    """
    Returns a count summary for a specific lesson session.
    Example: {'PRESENT': 22, 'ABSENT': 3, 'EXCUSED': 1, 'LATE': 2, 'total': 28}
    """
    records = Attendance.objects.filter(schedule=schedule, date=lesson_date)

    summary = {status: 0 for status in AttendanceStatus.values}
    for record in records:
        summary[record.status] += 1
    summary['total'] = records.count()

    return summary


def get_today_sessions(group, today: date, semester=None) -> list[dict]:
    """
    Returns schedules that fall on today for a group, with attendance status.
    Each item: {schedule, date, has_session, att_count}
    """
    from apps.schedules.models import Schedule
    from apps.schedules.services import get_active_semester
    from apps.schedules.services.semester import get_week_info

    if semester is None:
        semester = get_active_semester()
    if not semester:
        return []

    week_info = get_week_info(today, semester)
    week_type = week_info.get('week_type')
    if not week_type:
        return []

    weekday = today.weekday()
    schedules = (
        Schedule.objects.filter(
            group=group,
            semester=semester,
            week_type=week_type,
            weekday=weekday,
        )
        .select_related('subject', 'teacher')
        .order_by('lesson_number')
    )

    result = []
    for schedule in schedules:
        att_count = Attendance.objects.filter(schedule=schedule, date=today).count()
        result.append({
            'schedule': schedule,
            'date': today,
            'has_session': att_count > 0,
            'att_count': att_count,
        })
    return result


def get_recent_sessions(group, limit: int = 20) -> list[dict]:
    """
    Returns recent attendance sessions for a group with summary stats.
    Each item: {schedule, date, summary}
    """
    from apps.schedules.models import Schedule

    entries = (
        Attendance.objects.filter(student__group=group)
        .values('schedule_id', 'date')
        .distinct()
        .order_by('-date', 'schedule_id')[:limit]
    )

    result = []
    schedule_cache: dict[int, Schedule] = {}
    for entry in entries:
        sid = entry['schedule_id']
        if sid not in schedule_cache:
            try:
                schedule_cache[sid] = Schedule.objects.select_related('subject', 'teacher').get(pk=sid)
            except Schedule.DoesNotExist:
                continue
        schedule = schedule_cache[sid]
        summary = get_session_summary(schedule, entry['date'])
        result.append({
            'schedule': schedule,
            'date': entry['date'],
            'summary': summary,
        })
    return result


def get_teacher_today_sessions(teacher, today: date, semester=None) -> list[dict]:
    """
    Returns schedules that fall on today for a teacher, with attendance status.
    Each item: {schedule, date, has_session, att_count}
    """
    from apps.schedules.models import Schedule
    from apps.schedules.services import get_active_semester
    from apps.schedules.services.semester import get_week_info

    if semester is None:
        semester = get_active_semester()
    if not semester:
        return []

    week_info = get_week_info(today, semester)
    week_type = week_info.get('week_type')
    if not week_type:
        return []

    weekday = today.weekday()
    schedules = (
        Schedule.objects.filter(
            teacher=teacher,
            semester=semester,
            week_type=week_type,
            weekday=weekday,
        )
        .select_related('subject', 'group')
        .order_by('lesson_number')
    )

    result = []
    for schedule in schedules:
        att_count = Attendance.objects.filter(schedule=schedule, date=today).count()
        result.append({
            'schedule': schedule,
            'date': today,
            'has_session': att_count > 0,
            'att_count': att_count,
        })
    return result


def get_teacher_recent_sessions(teacher, limit: int = 20) -> list[dict]:
    """
    Returns recent attendance sessions for a teacher with summary stats.
    Each item: {schedule, date, summary}
    """
    from apps.schedules.models import Schedule

    entries = (
        Attendance.objects.filter(schedule__teacher=teacher)
        .values('schedule_id', 'date')
        .distinct()
        .order_by('-date', 'schedule_id')[:limit]
    )

    result = []
    schedule_cache: dict[int, Schedule] = {}
    for entry in entries:
        sid = entry['schedule_id']
        if sid not in schedule_cache:
            try:
                schedule_cache[sid] = Schedule.objects.select_related('subject', 'group').get(pk=sid)
            except Schedule.DoesNotExist:
                continue
        schedule = schedule_cache[sid]
        summary = get_session_summary(schedule, entry['date'])
        result.append({
            'schedule': schedule,
            'date': entry['date'],
            'summary': summary,
        })
    return result
